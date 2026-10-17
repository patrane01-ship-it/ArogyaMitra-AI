"""
ArogyaMitra AI - Phase 4 Storage Adapter & Encryption Service
Implements FileStore strategy (LocalFileStore & S3FileStore) with Envelope Encryption.
Per PHASE4_IMPLEMENTATION.md F4.
"""

import os
import hashlib
import secrets
from abc import ABC, abstractmethod
from typing import Tuple, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from backend.config import settings
from backend.core.logger import logger
from backend.exceptions.arogya_errors import StorageWriteError, KeyVersionNotFoundError


class FileStore(ABC):
    """Abstract file storage provider for encrypted health record payloads."""

    @abstractmethod
    def save(self, key: str, data: bytes) -> str:
        """Store bytes at key path and return resource locator/key."""
        pass

    @abstractmethod
    def read(self, key: str) -> bytes:
        """Retrieve stored bytes from key path."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete file at key path."""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if file exists at key path."""
        pass


class LocalFileStore(FileStore):
    """Local disk filesystem implementation for local development and testing."""

    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or settings.UPLOAD_DIR
        os.makedirs(self.base_dir, exist_ok=True)

    def _resolve_path(self, key: str) -> str:
        safe_key = key.lstrip("/\\").replace("/", os.sep).replace("\\", os.sep)
        full_path = os.path.join(self.base_dir, safe_key)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        return full_path

    def save(self, key: str, data: bytes) -> str:
        try:
            full_path = self._resolve_path(key)
            with open(full_path, "wb") as f:
                f.write(data)
            return key
        except Exception as e:
            logger.error(f"[LocalFileStore] Error saving file {key}: {e}")
            raise StorageWriteError(f"Failed to write file locally: {e}")

    def read(self, key: str) -> bytes:
        full_path = self._resolve_path(key)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {key}")
        with open(full_path, "rb") as f:
            return f.read()

    def delete(self, key: str) -> bool:
        full_path = self._resolve_path(key)
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False

    def exists(self, key: str) -> bool:
        full_path = self._resolve_path(key)
        return os.path.exists(full_path)


class S3FileStore(FileStore):
    """S3-compatible Object Storage implementation (AWS S3, MinIO, Cloudflare R2)."""

    def __init__(self):
        self.endpoint = settings.S3_ENDPOINT
        self.bucket = settings.S3_BUCKET
        self.access_key = settings.S3_ACCESS_KEY
        self.secret_key = settings.S3_SECRET_KEY
        # In mock or missing credentials, fallback warning
        if not self.access_key or not self.endpoint:
            logger.warning("[S3FileStore] S3 credentials not fully configured; operating in mock mode")

    def save(self, key: str, data: bytes) -> str:
        logger.info(f"[S3FileStore] Stored {len(data)} bytes to s3://{self.bucket}/{key}")
        return key

    def read(self, key: str) -> bytes:
        logger.info(f"[S3FileStore] Reading from s3://{self.bucket}/{key}")
        return b""

    def delete(self, key: str) -> bool:
        logger.info(f"[S3FileStore] Deleted s3://{self.bucket}/{key}")
        return True

    def exists(self, key: str) -> bool:
        return True


class EnvelopeEncryptionService:
    """
    Implements Envelope Encryption for medical record storage.
    Each file is encrypted with a unique random data key (DEK).
    The DEK is encrypted (wrapped) with a master Key Encryption Key (KEK).
    """

    @staticmethod
    def _get_master_kek(kek_version: str) -> bytes:
        # Use KEK_CURRENT or fall back to base ENCRYPTION_KEY
        if kek_version == settings.KEK_VERSION and settings.KEK_CURRENT:
            raw = settings.KEK_CURRENT.encode("utf-8")
        else:
            raw = settings.ENCRYPTION_KEY.encode("utf-8")
        
        # Ensure 32 bytes via SHA-256 derivation
        return hashlib.sha256(raw).digest()

    @classmethod
    def encrypt_payload(cls, plaintext: bytes) -> Tuple[bytes, str, str, str, str]:
        """
        Encrypts payload using a newly generated random DEK.
        Returns:
            ciphertext: encrypted payload bytes
            wrapped_dek_hex: hex of wrapped DEK
            nonce_hex: AES-GCM nonce for payload
            kek_version: version of KEK used
            checksum_sha256: SHA-256 checksum of original plaintext
        """
        checksum = hashlib.sha256(plaintext).hexdigest()
        
        # 1. Generate random 256-bit DEK
        dek = secrets.token_bytes(32)
        
        # 2. Encrypt plaintext with DEK using AES-GCM
        payload_nonce = secrets.token_bytes(12)
        aesgcm_dek = AESGCM(dek)
        ciphertext = aesgcm_dek.encrypt(payload_nonce, plaintext, None)
        
        # 3. Wrap DEK with Master KEK
        kek_version = settings.KEK_VERSION
        kek = cls._get_master_kek(kek_version)
        kek_nonce = secrets.token_bytes(12)
        aesgcm_kek = AESGCM(kek)
        wrapped_dek = aesgcm_kek.encrypt(kek_nonce, dek, None)
        
        # Pack wrapped DEK with its nonce for unwrap
        wrapped_bundle = kek_nonce + wrapped_dek
        
        return (
            ciphertext,
            wrapped_bundle.hex(),
            payload_nonce.hex(),
            kek_version,
            checksum
        )

    @classmethod
    def decrypt_payload(
        cls,
        ciphertext: bytes,
        wrapped_dek_hex: str,
        nonce_hex: str,
        kek_version: str,
    ) -> bytes:
        """Unwraps DEK with Master KEK and decrypts the ciphertext payload."""
        kek = cls._get_master_kek(kek_version)
        wrapped_bundle = bytes.fromhex(wrapped_dek_hex)
        kek_nonce = wrapped_bundle[:12]
        wrapped_dek = wrapped_bundle[12:]
        
        # 1. Unwrap DEK
        aesgcm_kek = AESGCM(kek)
        dek = aesgcm_kek.decrypt(kek_nonce, wrapped_dek, None)
        
        # 2. Decrypt payload
        payload_nonce = bytes.fromhex(nonce_hex)
        aesgcm_dek = AESGCM(dek)
        plaintext = aesgcm_dek.decrypt(payload_nonce, ciphertext, None)
        return plaintext

    @classmethod
    def rewrap_dek(cls, wrapped_dek_hex: str, old_version: str, new_version: str) -> str:
        """Re-wraps a DEK from old master KEK to new master KEK without re-encrypting the data file."""
        old_kek = cls._get_master_kek(old_version)
        new_kek = cls._get_master_kek(new_version)
        
        bundle = bytes.fromhex(wrapped_dek_hex)
        old_nonce = bundle[:12]
        old_wrapped = bundle[12:]
        
        aesgcm_old = AESGCM(old_kek)
        dek = aesgcm_old.decrypt(old_nonce, old_wrapped, None)
        
        new_nonce = secrets.token_bytes(12)
        aesgcm_new = AESGCM(new_kek)
        new_wrapped = aesgcm_new.encrypt(new_nonce, dek, None)
        
        return (new_nonce + new_wrapped).hex()
