from cryptography.fernet import Fernet
from dotenv import load_dotenv
import os

load_dotenv()

def get_encryption_key():
    key = os.getenv('ENCRYPTION_KEY')
    
    if not key:
        raise ValueError("ENCRYPTION_KEY must be set in environment variables")
    return key.encode()  # konwertuj string na bytes

def encrypt_password(password):
    if not password:
        return None
        
    if isinstance(password, bytes):
        password = password.decode()
    
    f = Fernet(get_encryption_key())
    return f.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password):
    if not encrypted_password:
        return None
        
    if isinstance(encrypted_password, bytes):
        encrypted_password = encrypted_password.decode()
    
    f = Fernet(get_encryption_key())
    return f.decrypt(encrypted_password.encode()).decode()