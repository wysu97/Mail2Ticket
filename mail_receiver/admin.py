from django.contrib import admin
from .models import Mailbox

@admin.register(Mailbox)
class MailboxAdmin(admin.ModelAdmin):
    list_display = ['name', 'imap_server', 'smtp_server', 'is_active', 'created_at']
    list_filter = ['imap_encryption', 'smtp_encryption', 'is_active']
    search_fields = ['name', 'imap_server', 'smtp_server', 'imap_login', 'smtp_login']
    list_editable = ['is_active']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description')
        }),
        ('IMAP Settings', {
            'fields': ('imap_server', 'imap_port', 'imap_login', 'imap_password', 'imap_encryption')
        }),
        ('SMTP Settings', {
            'fields': ('smtp_server', 'smtp_port', 'smtp_login', 'smtp_password', 'smtp_encryption')
        }),
        ('Status', {
            'fields': ('is_active', 'last_error')
        })
    )