from django.db import models
from mail_receiver.utils.encryption import encrypt_password, decrypt_password
from django.db import models
from django.utils import timezone
from email.utils import parsedate_to_datetime
import imaplib
import re
import binascii
from email.header import decode_header

def _decode_modified_utf7(encoded_text):
    """Dekoduje tekst z IMAP Modified UTF-7 do UTF-8"""
    if not encoded_text:
        return encoded_text
        
    def _modified_utf7_decode(s):
        s_bytes = s.encode('ascii')
        s_bytes = s_bytes.replace(b',', b'/')
        try:
            return binascii.a2b_base64(s_bytes).decode('utf-16-be')
        except:
            return s

    pattern = r'&([^-]*)-'
    result = re.sub(pattern, lambda m: _modified_utf7_decode(m.group(1)), encoded_text)
    return result

# Model do przetrzymywania danych skrzynek pocztowych, dane są potrzebne do logowania do skrzynek pocztowych
class Mailbox(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    # IMAP settings
    imap_server = models.CharField(max_length=100)
    imap_port = models.IntegerField(default=993)
    imap_login = models.CharField(max_length=100)
    imap_password = models.CharField(max_length=2024)
    imap_encryption = models.CharField(max_length=10, choices=[
        ('SSL', 'SSL'),
        ('TLS', 'TLS'),
        ('STARTTLS', 'STARTTLS'),
        ('NONE', 'None')
    ], default='SSL')
    
    # SMTP settings
    smtp_server = models.CharField(max_length=100)
    smtp_port = models.IntegerField(default=587)
    smtp_login = models.CharField(max_length=100)
    smtp_password = models.CharField(max_length=2024)
    smtp_encryption = models.CharField(max_length=10, choices=[
        ('SSL', 'SSL'),
        ('TLS', 'TLS'),
        ('STARTTLS', 'STARTTLS'),
        ('NONE', 'None')
    ], default='TLS')
    
    # Status fields
    is_active = models.BooleanField(default=True)
    last_error = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Mailbox'
        verbose_name_plural = 'Mailboxes'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Sprawdź czy to nowy obiekt (nie ma jeszcze ID)
        if not self.pk:
            # Szyfruj hasła tylko dla nowego obiektu
            self.imap_password = encrypt_password(self.imap_password)
            self.smtp_password = encrypt_password(self.smtp_password)
        else:
            # Dla istniejącego obiektu, sprawdź czy hasła zostały zmienione
            original = Mailbox.objects.get(pk=self.pk)
            if self.imap_password != original.imap_password:
                self.imap_password = encrypt_password(self.imap_password)
            if self.smtp_password != original.smtp_password:
                self.smtp_password = encrypt_password(self.smtp_password)
                
        super().save(*args, **kwargs)

    def get_imap_password(self):
        # Odszyfruj hasło na żądanie
        return decrypt_password(self.imap_password)

    def get_smtp_password(self):
        return decrypt_password(self.smtp_password)
    
    def update_folders(self):
        """Aktualizuje listę folderów dla skrzynki"""
        if self.imap_encryption == 'SSL':
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
        else:
            mail = imaplib.IMAP4(self.imap_server, self.imap_port)
            if self.imap_encryption == 'STARTTLS':
                mail.starttls()
        
        try:
            mail.login(self.imap_login, self.get_imap_password())
            _, folder_list = mail.list()
            current_time = timezone.now()
            
            for folder_data in folder_list:
                # Dekodowanie danych folderu
                decoded_data = folder_data.decode('utf-8')
                # Przykładowy format: (\HasNoChildren) "/" "INBOX.Sent"
                parts = re.match(r'\((.*?)\) "(.*?)" "(.*?)"', decoded_data)
                print(parts)
                if parts:
                    attributes = parts.group(1)
                    delimiter = parts.group(2)
                    full_path = parts.group(3)
                    
                    # Dekodowanie nazwy folderu z IMAP Modified UTF-7
                    decoded_path = _decode_modified_utf7(full_path)
                    name = decoded_path.split(delimiter)[-1]
                    
                    # Aktualizacja lub utworzenie folderu
                    MailFolder.objects.update_or_create(
                        mailbox=self,
                        full_path=decoded_path,
                        defaults={
                            'name': name,
                            'delimiter': delimiter,
                            'attributes': attributes,
                            'updated_at': current_time
                        }
                    )
            
            # Usuń foldery, które już nie istnieją
            self.folders.filter(updated_at__lt=current_time).delete()
            
        except imaplib.IMAP4.error as e:
            self.last_error = f"Błąd IMAP: {str(e)}"
            self.save()
            raise
        finally:
            try:
                mail.logout()
            except:
                pass

# Model do przetrzymywania danych emaili
class Email(models.Model):
    mailbox = models.ForeignKey(
        'Mailbox',
        on_delete=models.CASCADE,
        related_name='emails',
        verbose_name="Skrzynka pocztowa",
        null=True
    )
    
    # Dodajemy pole ticket
    ticket = models.CharField(
        max_length=50,
        verbose_name="Numer zgłoszenia",
        null=True,
        blank=True,
        help_text="Numer zgłoszenia wyodrębniony z tematu lub treści wiadomości",
        db_index=True
    )
    
    sender = models.CharField(max_length=255, verbose_name="Nadawca")
    recipient = models.CharField(max_length=255, verbose_name="Odbiorca", null=True, blank=True)
    subject = models.CharField(
        max_length=512, 
        verbose_name="Temat", 
        null=True, 
        blank=True,
        db_collation='utf8mb4_unicode_ci'
    )
    received_date = models.DateTimeField(
        verbose_name="Data synchronizacji",
        default=timezone.now,
        null=True,
        blank=True
    )
    
    # Treść
    content = models.TextField(
        verbose_name="Treść wiadomości",
        db_collation='utf8mb4_unicode_ci'
    )
    
    # Metadane
    message_id = models.CharField(max_length=255, unique=True, verbose_name="ID wiadomości", null=True, blank=True)
    content_type = models.CharField(max_length=100, verbose_name="Typ zawartości")
    mime_version = models.CharField(max_length=20, verbose_name="Wersja MIME", null=True, blank=True)
    return_path = models.CharField(max_length=255, verbose_name="Ścieżka zwrotna", null=True, blank=True)
    dkim_signature = models.TextField(verbose_name="Podpis DKIM", null=True, blank=True)
    date = models.DateTimeField(verbose_name="Data", null=True, blank=True)
    # Pola systemowe
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data utworzenia w bazie")
    is_processed = models.BooleanField(default=False, verbose_name="Czy przetworzona")
    processing_errors = models.TextField(null=True, blank=True, verbose_name="Błędy przetwarzania")
    # TODO dodac załączniki
    attachments = models.ManyToManyField('EmailAttachment', blank=True, related_name='emails')
    
    class Meta:
        verbose_name = "Email"
        verbose_name_plural = "Emaile"
        ordering = ['-received_date']
        indexes = [
            models.Index(fields=['-received_date']),
            models.Index(fields=['sender']),
            models.Index(fields=['is_processed']),
            models.Index(fields=['mailbox']),
        ]

    def __str__(self):
        return f"{self.subject} - {self.sender} ({self.received_date})"

    def save_from_json(self, email_data):
        try:
            # mailbox powinno być już ustawione przed wywołaniem tej metody
            if not self.mailbox:
                raise ValueError("Nie ustawiono skrzynki pocztowej")
            
            headers = email_data['headers']
            metadata = email_data['metadata']
            
            self.sender = headers.get('from', '')
            self.recipient = headers.get('to', '')
            self.subject = headers.get('subject', '')
            
            # Dodajemy ekstrakcję numeru zgłoszenia z tematu
            if self.subject:
                # Przykładowy wzorzec - możesz dostosować według swoich potrzeb
                ticket_pattern = r'\[#(\d+)\]|\(#(\d+)\)|#(\d+)'
                ticket_match = re.search(ticket_pattern, self.subject)
                if ticket_match:
                    # Bierzemy pierwszą znalezioną grupę, która nie jest None
                    self.ticket = next(group for group in ticket_match.groups() if group is not None)
            
            self.date = headers.get('date')
            date_str = headers.get('date')
            if date_str:
                try:
                    self.received_date = parsedate_to_datetime(date_str)
                except (TypeError, ValueError):
                    self.received_date = timezone.now()
            else:
                self.received_date = timezone.now()
            
            self.content = email_data.get('content', '')
            self.content_type = metadata.get('content_type', '')
            self.mime_version = metadata.get('mime_version', '')
            self.return_path = metadata.get('return_path', '')
            self.dkim_signature = metadata.get('dkim_signature', '')
            
            # Obsługa załączników
            attachments = email_data.get('attachments', [])
            for attachment_data in attachments:
                attachment = EmailAttachment.objects.create(
                    file=attachment_data.get('content'),
                    filename=attachment_data.get('filename'),
                    content_type=attachment_data.get('content_type'),
                    size=attachment_data.get('size', 0)
                )
                self.attachments.add(attachment)
            
            self.save()
            return True
        except Exception as e:
            print(f"Błąd podczas zapisywania emaila: {str(e)}")
            return False

# Model do przechowywania załączników
class EmailAttachment(models.Model):
    file = models.FileField(upload_to='email_attachments/%Y/%m/%d/', verbose_name="Plik")
    filename = models.CharField(max_length=255, verbose_name="Nazwa pliku")
    content_type = models.CharField(max_length=100, verbose_name="Typ MIME")
    size = models.IntegerField(verbose_name="Rozmiar pliku (bajty)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data dodania")

    class Meta:
        verbose_name = "Załącznik"
        verbose_name_plural = "Załączniki"
        indexes = [
            models.Index(fields=['filename']),
            models.Index(fields=['content_type']),
        ]

    def __str__(self):
        return f"{self.filename} ({self.size} bajtów)"
    

class MailFolder(models.Model):
    mailbox = models.ForeignKey(
        Mailbox,
        on_delete=models.CASCADE,
        related_name='folders'
    )
    full_path = models.CharField(max_length=255, help_text='Pełna ścieżka folderu')
    name = models.CharField(max_length=100, help_text='Nazwa folderu')
    delimiter = models.CharField(max_length=5, help_text='Separator używany w ścieżce')
    attributes = models.CharField(max_length=50, help_text='Atrybuty folderu')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('mailbox', 'full_path')
        verbose_name = 'Folder mailowy'
        verbose_name_plural = 'Foldery mailowe'

    def __str__(self):
        return f"{self.mailbox}: {self.full_path}"