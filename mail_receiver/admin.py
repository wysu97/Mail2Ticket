from django.contrib import admin
from django import forms
from django.utils.safestring import mark_safe
from .models import Mailbox, Email, MailFolder
from django.db.models import Count, Q, Subquery, OuterRef

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
    list_display = ['name', 'imap_server', 'smtp_server', 'is_active', 'created_at', 'folder_count', 'email_count', 'last_sync']
    list_filter = ['imap_encryption', 'smtp_encryption', 'is_active']
    search_fields = ['name', 'imap_server', 'smtp_server', 'imap_login', 'smtp_login']
    list_editable = ['is_active']
    actions = ['update_folders_action']
    
    def update_folders_action(self, request, queryset):
        updated = 0
        errors = 0
        for mailbox in queryset:
            try:
                mailbox.update_folders()
                updated += 1
            except Exception as e:
                errors += 1
                self.message_user(request, f'Błąd dla {mailbox.name}: {str(e)}', level='ERROR')
        
        self.message_user(
            request,
            f'Zaktualizowano foldery dla {updated} skrzynek. Błędy: {errors}.'
        )
    update_folders_action.short_description = "Aktualizuj foldery wybranych skrzynek"
    
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
    
    def folder_count(self, obj):
        return obj.folders.count()
    folder_count.short_description = 'Liczba folderów'
    
    def email_count(self, obj):
        # Jeśli email_count został już obliczony przez annotate
        if hasattr(obj, 'email_count_annotated'):
            return obj.email_count_annotated
        # Fallback do oryginalnej metody
        folder_ids = obj.folders.values_list('id', flat=True)
        return Email.objects.filter(mail_folder_id__in=folder_ids).count()
    email_count.short_description = 'Liczba wiadomości'
    
    def last_sync(self, obj):
        latest_folder = obj.folders.order_by('-updated_at').first()
        if latest_folder:
            return latest_folder.updated_at
        return '-'
    last_sync.short_description = 'Ostatnia synchronizacja'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            email_count_annotated=Subquery(
                Email.objects.filter(
                    mailbox=OuterRef('pk')
                ).values('mailbox')
                .annotate(count=Count('id'))
                .values('count')
            )
        )
    
@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    list_display = ['subject', 'received_date', 'sender', 'recipient', 'date']
    list_filter = ['received_date']
    search_fields = ['subject', 'sender', 'recipient']
    readonly_fields = ['received_date', 'formatted_content']
    
    def formatted_content(self, obj):
        return mark_safe(obj.content)
    formatted_content.short_description = 'Treść wiadomości'
    

@admin.register(MailFolder)
class MailFolderAdmin(admin.ModelAdmin):
    list_display = ['mailbox', 'name', 'full_path', 'attributes', 'updated_at']
    list_filter = ['mailbox', 'attributes']
    search_fields = ['name', 'full_path']
    readonly_fields = ['created_at', 'updated_at']
