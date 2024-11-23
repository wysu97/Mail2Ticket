# Mail2Ticket

**Mail2Ticket** to inteligentny system ticketowy, który automatyzuje obsługę zgłoszeń przesyłanych przez email. Dzięki integracji z AI, system umożliwia automatyczne klasyfikowanie ticketów, sugerowanie odpowiedzi oraz priorytetyzowanie zgłoszeń. Aplikacja została zaprojektowana z myślą o firmach, które chcą zoptymalizować proces obsługi klienta i poprawić efektywność działania swoich zespołów wsparcia.

---

## Funkcje Kluczowe:
- Automatyczne tworzenie ticketów z wiadomości email.
- Klasyfikacja AI zgłoszeń na podstawie treści.
- Generowanie odpowiedzi z wykorzystaniem modeli AI.
- Priorytetyzacja zgłoszeń na podstawie słów kluczowych i wcześniejszych danych.
- Panel administracyjny do zarządzania ticketami, użytkownikami i działami.
- Raporty i statystyki wydajności zespołu.

---

## Technologie:
- **Backend:** Python, Django, Django REST Framework.
- **AI:** OpenAI API, spaCy lub Hugging Face do przetwarzania tekstu.
- **Frontend:** React.js (opcjonalnie).
- **Baza Danych:** PostgreSQL.
- **Inne:** Redis (kolejki), Docker (konteneryzacja).

---

## Cel:
Mail2Ticket pomaga firmom:
- Zwiększyć efektywność obsługi klienta.
- Szybciej odpowiadać na zgłoszenia.
- Automatyzować rutynowe zadania.


# Mail2Ticket - Instrukcja uruchomienia

## Wymagania wstępne
- Docker Desktop
- Git

## Krok 1: Przygotowanie projektu

1. Sklonuj repozytorium:

```bash
git clone [adres-repo]
cd Mail2Ticket
```
2. Utwórz plik `.env` w głównym katalogu projektu:

```bash
MYSQL_ROOT_PASSWORD=twoje_haslo_root
MYSQL_DATABASE=mail2ticket
MYSQL_USER=mail2ticket_user
MYSQL_PASSWORD=twoje_haslo_user
ENCRYPTION_KEY=klucz_szyfrowania
```

## Krok 2: Budowa i uruchomienie kontenerów

1. Zbuduj i uruchom kontenery:
```bash
docker-compose up --build
```

2. W nowym oknie terminala wykonaj migracje:
```bash
docker-compose exec web python manage.py migrate
```
3. Utwórz superużytkownika Django:
```bash
docker-compose exec web python manage.py createsuperuser
```

## Krok 3: Weryfikacja działania

Aplikacja powinna być dostępna pod następującymi adresami:
- Panel administracyjny Django: http://localhost:8000/admin
- phpMyAdmin: http://localhost:8080
  - login: mail2ticket_user
  - hasło: [hasło z MYSQL_PASSWORD]

## Struktura projektu
Mail2Ticket/
├── app/
│ ├── manage.py
│ ├── config/
│ │ ├── settings.py
│ │ ├── urls.py
│ │ └── wsgi.py
│ └── mail_receiver/
│ ├── models.py
│ ├── services.py
│ └── ...
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env

## Przydatne komendy

### Zarządzanie kontenerami
```bash
Zatrzymanie kontenerów
docker-compose down
Uruchomienie kontenerów w tle
docker-compose up -d
Podgląd logów
docker-compose logs -f
Restart konkretnego serwisu
docker-compose restart web
```
### Zarządzanie Django
```bash
Tworzenie migracji
docker-compose exec web python manage.py makemigrations
Aplikowanie migracji
docker-compose exec web python manage.py migrate
Shell Django
docker-compose exec web python manage.py shell
Pobieranie maili (gdy zostanie zaimplementowane)
docker-compose exec web python manage.py fetch_emails
```

## Rozwiązywanie problemów

1. Jeśli kontenery nie chcą się uruchomić:
   - Sprawdź czy Docker Desktop jest uruchomiony
   - Sprawdź logi: `docker-compose logs`
   - Upewnij się, że porty 8000 i 8080 są wolne

2. Problemy z bazą danych:
   - Sprawdź połączenie przez phpMyAdmin
   - Zweryfikuj dane dostępowe w pliku `.env`
   - W razie potrzeby wyczyść wolumeny: `docker-compose down -v`

3. Problemy z uprawnieniami plików:
   - Sprawdź właściciela plików w kontenerze
   - W razie potrzeby zmień uprawnienia lokalnie

## Kontakt i wsparcie

W razie problemów z uruchomieniem projektu, proszę o kontakt:
- bartosz.klosinski@2k-web.pl