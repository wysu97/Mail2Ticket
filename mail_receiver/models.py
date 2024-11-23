from django.db import models
from mail_receiver.utils.encryption import encrypt_password, decrypt_password

# Model do przetrzymywania danych skrzynek pocztowych, dane są potrzebne do logowania do skrzynek pocztowych
class Mailbox(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    # IMAP settings
    imap_server = models.CharField(max_length=100)
    imap_port = models.IntegerField(default=993)
    imap_login = models.CharField(max_length=100)
    imap_password = models.CharField(max_length=255)
    imap_encryption = models.CharField(max_length=10, choices=[
        ('SSL', 'SSL'),
        ('TLS', 'TLS'),
        ('NONE', 'None')
    ], default='SSL')
    
    # SMTP settings
    smtp_server = models.CharField(max_length=100)
    smtp_port = models.IntegerField(default=587)
    smtp_login = models.CharField(max_length=100)
    smtp_password = models.CharField(max_length=255)
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
        # Szyfruj hasła przed zapisaniem
        self.imap_password = encrypt_password(self.imap_password)
        self.smtp_password = encrypt_password(self.smtp_password)
        super().save(*args, **kwargs)

    def get_imap_password(self):
        # Odszyfruj hasło na żądanie
        return decrypt_password(self.imap_password)

    def get_smtp_password(self):
        return decrypt_password(self.smtp_password)