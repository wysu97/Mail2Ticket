# Generated by Django 5.1.3 on 2024-11-24 21:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mail_receiver', '0007_alter_email_received_date'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='email_attachments/%Y/%m/%d/', verbose_name='Plik')),
                ('filename', models.CharField(max_length=255, verbose_name='Nazwa pliku')),
                ('content_type', models.CharField(max_length=100, verbose_name='Typ MIME')),
                ('size', models.IntegerField(verbose_name='Rozmiar pliku (bajty)')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Data dodania')),
            ],
            options={
                'verbose_name': 'Załącznik',
                'verbose_name_plural': 'Załączniki',
                'indexes': [models.Index(fields=['filename'], name='mail_receiv_filenam_37d179_idx'), models.Index(fields=['content_type'], name='mail_receiv_content_1cf4a7_idx')],
            },
        ),
        migrations.AddField(
            model_name='email',
            name='attachments',
            field=models.ManyToManyField(blank=True, related_name='emails', to='mail_receiver.emailattachment'),
        ),
    ]
