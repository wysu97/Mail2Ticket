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
    try:
        mailbox = Mailbox.objects.filter(is_active=True).first()
        if not mailbox:
            return HttpResponse("Brak aktywnej skonfigurowanej skrzynki", status=400)

        server = mailbox.imap_server
        port = 1143  # port dla STARTTLS w Proton Mail Bridge

        try:
            # Używamy IMAP4 (nie IMAP4_SSL) dla STARTTLS
            mail = imaplib.IMAP4(server, port)
            # Włączamy szyfrowanie STARTTLS
            if not mail.starttls():
                raise Exception("Nie udało się ustanowić połączenia STARTTLS")
        except Exception as e:
            return HttpResponse(f"Błąd połączenia z serwerem: {str(e)}", status=500)

        try:
            mail.login(mailbox.imap_login, mailbox.get_imap_password())
        except Exception as e:
            return HttpResponse(f"Błąd logowania: {str(e)}", status=500)
        
        # Wybierz folder INBOX
        mail.select('INBOX')
        skrzynki = mail.list()
        # Sprawdź czy istnieje folder Archive, jeśli nie - utwórz go
        if 'Archive' not in [folder.decode().split('"/"')[-1] for folder in mail.list()[1]]:
            mail.create('Archive')

        # Pobierz wszystkie maile
        _, messages = mail.search(None, 'ALL')
        message_numbers = messages[0].split()
        if not message_numbers:
            return HttpResponse("Brak wiadomości do pobrania", status=200)
            
        for num in message_numbers:
            try:
                # Konwertuj num na string, jeśli jest to potrzebne
                msg_num = num.decode('utf-8') if isinstance(num, bytes) else str(num)
                
                # Pobierz wiadomość
                _, msg_data = mail.fetch(msg_num, '(RFC822)')
                
                if msg_data[0] is None:
                    continue
                    
                email_message = email.message_from_bytes(msg_data[0][1])
                
                # Przetwórz i zapisz email
                email_data = extract_email_data(email_message)
                email_obj = Email()
                email_obj.mailbox = mailbox
                # print(email_message)
                # print(email_data)
                if email_obj.save_from_json(json.loads(email_data)):
                    try:
                        # Przenieś wiadomość do archiwum
                        mail.copy(msg_num, 'mail.Archive')
                        mail.store(msg_num, '+FLAGS', '\\Deleted')
                        mail.expunge()
                        break #TODO: zmienić na pętlę   
                    except Exception as e:
                        return HttpResponse(f"Email zapisany, ale wystąpił błąd podczas przenoszenia do archiwum: {str(e)}", status=500)
                else:
                    return HttpResponse("Wystąpił błąd podczas zapisywania emaila", status=500)
            except Exception as e:
                print(f"Błąd podczas przetwarzania wiadomości {msg_num}: {str(e)}")
                continue

        mail.close()
        mail.logout()
        
        return HttpResponse(f"Emaile zostały pomyślnie przetworzone i zarchiwizowane", status=200)
        
    except Exception as e:
        return HttpResponse(f"Wystąpił błąd podczas pobierania maila: {str(e)}", status=500)

def extract_email_data(email_message):
    # Podstawowe dane
    headers = {
        'from': decode_email_header(email_message['From']),
        'to': decode_email_header(email_message['To']),
        'subject': decode_email_header(email_message['Subject']),
        'date': parsedate_to_datetime(email_message['Date']).isoformat() if email_message['Date'] else None
    }
    
    # Pobieranie treści z obsługą różnych kodowań
    body = ""
    attachments = []
    if email_message.is_multipart():
        for part in email_message.walk():
            # Pomijamy części multipart
            if part.get_content_maintype() == 'multipart':
                continue
                
            # Pobieramy nazwę pliku
            filename = part.get_filename()
            if filename and part.get_content_type() != 'text/plain':
                # Pobieramy zawartość załącznika
                content = part.get_payload(decode=True)
                
                attachment_data = {
                    'filename': decode_email_header(filename),
                    'content': content,
                    'content_type': part.get_content_type(),
                    'size': len(content)
                }
                attachments.append(attachment_data)
            elif part.get_content_type() == "text/plain" or part.get_content_type() == "text/html":
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or 'utf-8'
                try:
                    content = payload.decode(charset)
                    if part.get_content_type() == "text/html":
                        body = content  # Priorytet dla wersji HTML
                    elif not body:  # Jeśli nie mamy jeszcze żadnej treści, użyj plain text
                        body = content
                except UnicodeDecodeError:
                    try:
                        # Próba innych popularnych kodowań
                        for encoding in ['iso-8859-2', 'windows-1250', 'latin1', 'ascii']:
                            try:
                                body = payload.decode(encoding)
                                break
                            except UnicodeDecodeError:
                                continue
                    except:
                        # Jeśli wszystko zawiedzie, użyj 'replace' aby pominąć problematyczne znaki
                        body = payload.decode('utf-8', errors='replace')
    else:
        payload = email_message.get_payload(decode=True)
        charset = email_message.get_content_charset() or 'utf-8'
        try:
            body = payload.decode(charset)
        except UnicodeDecodeError:
            try:
                # Próba innych popularnych kodowań
                for encoding in ['iso-8859-2', 'windows-1250', 'latin1', 'ascii']:
                    try:
                        body = payload.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
            except:
                # Jeśli wszystko zawiedzie, użyj 'replace'
                body = payload.decode('utf-8', errors='replace')
    
    # Tworzenie struktury JSON
    email_data = {
        'headers': headers,
        'content': body,
        'content_type': 'text/html' if '<html' in body.lower() else 'text/plain',
        'metadata': {
            'content_type': email_message.get_content_type(),
            'mime_version': email_message['MIME-Version'],
            'return_path': email_message['Return-Path'],
            'dkim_signature': email_message['DKIM-Signature'] if 'DKIM-Signature' in email_message else None,
        },
        'attachments': attachments
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
