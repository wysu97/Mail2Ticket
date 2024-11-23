from django.db import models
from mail_receiver.utils.encryption import encrypt_password, decrypt_password
from django.db import models
from django.utils import timezone
from email.utils import parsedate_to_datetime
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
    
    

# Model do przetrzymywania danych emaili
class Email(models.Model):
    # Podstawowe pola nagłówkowe
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
    
    class Meta:
        verbose_name = "Email"
        verbose_name_plural = "Emaile"
        ordering = ['-received_date']
        indexes = [
            models.Index(fields=['-received_date']),
            models.Index(fields=['sender']),
            models.Index(fields=['is_processed']),
        ]

    def __str__(self):
        return f"{self.subject} - {self.sender} ({self.received_date})"

    def save_from_json(self, email_data):
        """Metoda do zapisywania danych z JSON"""
        try:
            headers = email_data['headers']
            metadata = email_data['metadata']
            
            self.sender = headers.get('from', '')
            self.recipient = headers.get('to', '')
            self.subject = headers.get('subject', '')
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
            
            self.save()
            return True
        except Exception as e:
            self.processing_errors = str(e)
            self.save()
            return False