import os
import base64
import hashlib
from datetime import datetime, timedelta
from typing import Any, Union
from jose import jwt
from passlib.context import CryptContext
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

from app.core.config import settings

# Password Hashing Setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Encryptor for sensitive database details (OLT passwords / SNMP community)
class CredentialEncryptor:
    def __init__(self, key: str):
        # Derives a 32-byte key from the configured key string using SHA-256
        self.key = hashlib.sha256(key.encode("utf-8")).digest()

    def encrypt(self, plain_text: str) -> str:
        if not plain_text:
            return ""
        iv = os.urandom(12)  # Recommended 12 bytes IV for GCM mode
        encryptor = Cipher(
            algorithms.AES(self.key),
            modes.GCM(iv),
            backend=default_backend()
        ).encryptor()
        
        ciphertext = encryptor.update(plain_text.encode("utf-8")) + encryptor.finalize()
        # Combine: iv (12 bytes) + ciphertext (variable) + auth tag (16 bytes)
        payload = iv + ciphertext + encryptor.tag
        return base64.b64encode(payload).decode("utf-8")

    def decrypt(self, cipher_text: str) -> str:
        if not cipher_text:
            return ""
        try:
            raw_data = base64.b64decode(cipher_text.encode("utf-8"))
            if len(raw_data) < 28: # IV(12) + Tag(16) minimum length
                raise ValueError("Cipher text too short")
            
            iv = raw_data[:12]
            tag = raw_data[-16:]
            ciphertext = raw_data[12:-16]
            
            decryptor = Cipher(
                algorithms.AES(self.key),
                modes.GCM(iv, tag),
                backend=default_backend()
            ).decryptor()
            
            decrypted_bytes = decryptor.update(ciphertext) + decryptor.finalize()
            return decrypted_bytes.decode("utf-8")
        except Exception as e:
            # Fallback/logging could go here, return empty or raise
            raise ValueError(f"Failed to decrypt credentials: {str(e)}")

encryptor = CredentialEncryptor(settings.ENCRYPTION_KEY)

# Password hashing utilities
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# JWT auth utilities
def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.ALGORITHM)
    return encoded_jwt
