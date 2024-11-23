# Użyj oficjalnego obrazu Pythona
FROM python:3.12

# Ustaw katalog roboczy w kontenerze
WORKDIR /app

# Skopiuj pliki projektu
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Skopiuj resztę aplikacji
COPY . .

# Otwórz port 8000
EXPOSE 8000

# Uruchom aplikację
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
