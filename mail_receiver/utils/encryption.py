from cryptography.fernet import Fernet

# Klucz szyfrowania powinien być przechowywany w bezpiecznym miejscu (np. w pliku .env lub menedżerze haseł)
KEY = b'your-secret-key'  # Generowany raz przy pomocy Fernet.generate_key()

def encrypt_password(password):
    f = Fernet(KEY)
    return f.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password):
    f = Fernet(KEY)
    return f.decrypt(encrypted_password.encode()).decode()
