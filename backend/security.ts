import crypto from 'crypto';

/**
 * Derives a secure 32-byte key from the configured ENCRYPTION_KEY environment variable.
 */
export function getEncryptionKey(): Buffer {
  const rawKey = process.env.ENCRYPTION_KEY || 'arogya_mitra_enc_key_32bytes_default';
  return crypto.createHash('sha256').update(rawKey).digest();
}

/**
 * Encrypts a buffer using AES-256-GCM.
 * Prepends the 12-byte IV and 16-byte Auth Tag to the ciphertext.
 */
export function encryptFile(buffer: Buffer): { encryptedData: Buffer; hash: string } {
  const key = getEncryptionKey();
  const iv = crypto.randomBytes(12); // 12-byte IV is standard for GCM
  const cipher = crypto.createCipheriv('aes-256-gcm', key, iv);
  
  const encrypted = Buffer.concat([cipher.update(buffer), cipher.final()]);
  const tag = cipher.getAuthTag(); // 16-byte tag
  
  // Format: IV (12B) + Tag (16B) + Ciphertext
  const encryptedData = Buffer.concat([iv, tag, encrypted]);
  
  // Compute SHA-256 hash of original data for integrity
  const hash = crypto.createHash('sha256').update(buffer).digest('hex');
  
  return { encryptedData, hash };
}

/**
 * Decrypts a buffer that was encrypted using AES-256-GCM.
 */
export function decryptFile(encryptedData: Buffer): Buffer {
  const key = getEncryptionKey();
  
  // Extract IV (12B) and Tag (16B)
  const iv = encryptedData.subarray(0, 12);
  const tag = encryptedData.subarray(12, 28);
  const ciphertext = encryptedData.subarray(28);
  
  const decipher = crypto.createDecipheriv('aes-256-gcm', key, iv);
  decipher.setAuthTag(tag);
  
  return Buffer.concat([decipher.update(ciphertext), decipher.final()]);
}
