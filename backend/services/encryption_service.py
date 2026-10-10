"""
ArogyaMitra AI - Encryption Service
Handles AES-256-GCM encryption and decryption for health documents at rest.
Per TECH_STACK.md §6 and PRODUCTION_BACKEND.md §9.2.
"""

import os
import base64
from typing import Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from backend.core.logger import logger
from backend.exceptions.arogya_errors import ArogyaError


class EncryptionService:
    """AES-256-GCM authenticated encryption service."""

    def __init__(self, key: bytes):
        """
        Initialize with a 32-byte AES key.
        If key length is not 32 bytes, attempts base64 decoding.
        """
        if len(key) != 32:
            try:
                decoded = base64.b64decode(key)
                if len(decoded) == 32:
                    key = decoded
                else:
                    raise ValueError("Key must decode to exactly 32 bytes.")
            except Exception as e:
                logger.critical(f"[EncryptionService] Invalid key provided: {e}")
                raise ArogyaError("Invalid encryption key configuration", status_code=500)
        
        self.key = key
        self.aesgcm = AESGCM(key)

    def encrypt_file(self, file_bytes: bytes) -> Tuple[bytes, bytes]:
        """
        Encrypt file bytes using AES-256-GCM.
        Returns: (nonce (12 bytes), ciphertext)
        """
        try:
            nonce = os.urandom(12)  # 96-bit nonce for AES-GCM
            ciphertext = self.aesgcm.encrypt(nonce, file_bytes, None)
            return nonce, ciphertext
        except Exception as e:
            logger.error(f"[EncryptionService] Encryption failed: {type(e).__name__}")
            raise ArogyaError("Encryption failed", status_code=500)

    def decrypt_file(self, nonce: bytes, ciphertext: bytes) -> bytes:
        """
        Decrypt ciphertext using nonce and key.
        """
        try:
            return self.aesgcm.decrypt(nonce, ciphertext, None)
        except Exception as e:
            logger.error(f"[EncryptionService] Decryption failed: {type(e).__name__}")
            raise ArogyaError("Decryption failed", status_code=500)

    def encrypt_to_payload(self, file_bytes: bytes) -> bytes:
        """
        Convenience: Encrypts bytes and returns combined payload [12 bytes nonce + ciphertext].
        """
        nonce, ciphertext = self.encrypt_file(file_bytes)
        return nonce + ciphertext

    def decrypt_from_payload(self, payload: bytes) -> bytes:
        """
        Convenience: Splits [12 bytes nonce + ciphertext] and decrypts.
        """
        if len(payload) < 12:
            raise ArogyaError("Encrypted payload too short to contain nonce", status_code=500)
        nonce = payload[:12]
        ciphertext = payload[12:]
        return self.decrypt_file(nonce, ciphertext)
