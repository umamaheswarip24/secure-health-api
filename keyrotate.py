import os, json
from cryptography.fernet import Fernet
import mysql.connector

KEY_FILE = 'keys/data.key'

print('Starting key rotation...')

# Step 1: Read old key (strip any whitespace)
old_key = open(KEY_FILE, 'rb').read().strip()
old_cipher = Fernet(old_key)

# Step 2: Generate new key
new_key = Fernet.generate_key()
new_cipher = Fernet(new_key)

# Step 3: Connect to MySQL
conn = mysql.connector.connect(
    host='localhost',
    port=3307,
    user='appuser',
    password='apppass',
    database='patientdb'
)
cur = conn.cursor()
cur.execute("SELECT patient_id, encrypted_data FROM patients")
rows = cur.fetchall()
print(f'Found {len(rows)} records to re-encrypt...')

for pid, enc_data in rows:
    try:
        # Convert to bytes properly
        if isinstance(enc_data, (bytearray, memoryview)):
            enc_bytes = bytes(enc_data)
        else:
            enc_bytes = enc_data

        print(f'  Decrypting {pid} ({len(enc_bytes)} bytes)...')

        # Decrypt with old key
        decrypted = old_cipher.decrypt(enc_bytes)

        # Re-encrypt with new key
        re_encrypted = new_cipher.encrypt(decrypted)

        # Update in MySQL
        cur.execute(
            "UPDATE patients SET encrypted_data = %s WHERE patient_id = %s",
            (re_encrypted, pid)
        )
        print(f'  Re-encrypted: {pid} ✓')

    except Exception as e:
        print(f'  ERROR on {pid}: {e}')
        print(f'  Raw type: {type(enc_data)}, value[:20]: {bytes(enc_data)[:20]}')

conn.commit()
cur.close()
conn.close()

# Step 4: Save new key
open(KEY_FILE + '.bak', 'wb').write(old_key)
open(KEY_FILE, 'wb').write(new_key)

print(f'Key rotation complete! {len(rows)} records re-encrypted.')
print('Old key backed up to keys/data.key.bak')
print('New key saved to keys/data.key')
print('Restart the app container to use the new key!')