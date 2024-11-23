from django.shortcuts import render
from django.http import HttpResponse
from .models import Mailbox, Email
import imaplib
import email
from email.header import decode_header
import json
from email.utils import parsedate_to_datetime
# Create your views here.
## metoda która będzie pobierać maila ze skrzynki mailowej
def fetch_emails(request):
    # Pobierz dane do logowania
    mailbox = Mailbox.objects.filter(is_active=True).first()
    
    if not mailbox:
        return HttpResponse("Brak aktywnej skrzynki pocztowej")
    
    try:
        # Połącz się ze skrzynką używając odpowiedniego szyfrowania
        if mailbox.imap_encryption == 'SSL':
            mail = imaplib.IMAP4_SSL(mailbox.imap_server, mailbox.imap_port)
        else:
            mail = imaplib.IMAP4(mailbox.imap_server, mailbox.imap_port)
            if mailbox.imap_encryption == 'TLS':
                mail.starttls()
        
        # Logowanie z odszyfrowanym hasłem
        mail.login(mailbox.imap_login, mailbox.get_imap_password())
        print(mailbox.get_imap_password())
        
        # Wybierz folder INBOX
        mail.select('INBOX')
        
        # Pobierz ostatni email 
        _, messages = mail.search(None, 'ALL')
        if not messages[0]:
            return HttpResponse("Brak maili w skrzynce")
            
        last_email_id = messages[0].split()[-1]
        _, msg = mail.fetch(last_email_id, '(RFC822)')
        email_body = msg[0][1]
        email_message = email.message_from_bytes(email_body)
        
        # Dekodowanie tematu
        subject = email_message['Subject']
        decoded_subject = decode_header(subject)[0][0]
        if isinstance(decoded_subject, bytes):
            decoded_subject = decoded_subject.decode()
            
        # Zamknij połączenie
        mail.close()
        mail.logout()
        
        email_data = extract_email_data(email_message)
        
        # Zapisz email do bazy
        email_obj = Email()
        if email_obj.save_from_json(json.loads(email_data)):
            return HttpResponse("Email został pomyślnie zapisany", status=200)
        else:
            return HttpResponse("Wystąpił błąd podczas zapisywania emaila", status=500)
        
    except Exception as e:
        # Zapisz błąd w modelu
        print(str(e))
        mailbox.last_error = str(e)
        mailbox.save()
        return HttpResponse(f"Wystąpił błąd podczas pobierania maila: {str(e)}")

def extract_email_data(email_message):
    # Podstawowe dane
    headers = {
        'from': decode_email_header(email_message['From']),
        'to': decode_email_header(email_message['To']),
        'subject': decode_email_header(email_message['Subject']),
        'date': parsedate_to_datetime(email_message['Date']).isoformat() if email_message['Date'] else None
    }
    
    # Pobieranie treści
    body = ""
    if email_message.is_multipart():
        for part in email_message.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode('utf-8')
                break
    else:
        body = email_message.get_payload(decode=True).decode('utf-8')
    
    # Tworzenie struktury JSON
    email_data = {
        'headers': headers,
        'content': body,
        'metadata': {
            'content_type': email_message.get_content_type(),
            'mime_version': email_message['MIME-Version'],
            'return_path': email_message['Return-Path'],
            'dkim_signature': email_message['DKIM-Signature'] if 'DKIM-Signature' in email_message else None,
        }
    }
    
    return json.dumps(email_data, ensure_ascii=False, indent=2)

def decode_email_header(header):
    """Pomocnicza funkcja do dekodowania nagłówków"""
    if not header:
        return None
    decoded_header = decode_header(header)
    return ' '.join([
        (str(t[0], t[1] or 'utf-8') if isinstance(t[0], bytes) else str(t[0]))
        for t in decoded_header
    ])
