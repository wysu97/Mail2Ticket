from django.contrib import admin
from django import forms
from .models import Mailbox, Email

class MailboxAdminForm(forms.ModelForm):
    imap_password = forms.CharField(
        widget=forms.PasswordInput(render_value=True),
        required=False
    )
    smtp_password = forms.CharField(
        widget=forms.PasswordInput(render_value=True),
        required=False
    )

    class Meta:
        model = Mailbox
        fields = '__all__'

@admin.register(Mailbox)
class MailboxAdmin(admin.ModelAdmin):
    form = MailboxAdminForm
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
    
@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    list_display = ['subject', 'received_date', 'sender', 'recipient']
    list_filter = ['received_date']
    search_fields = ['subject', 'sender', 'recipient']
    readonly_fields = ['received_date']
    
    