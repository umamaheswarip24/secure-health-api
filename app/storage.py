import os, json, uuid
from cryptography.fernet import Fernet
import mysql.connector

# ─────────────────────────────────────────
# KEY MANAGEMENT — loads AES key from file
# ─────────────────────────────────────────
KEY_FILE = os.environ.get('APP_DATA_KEY', 'keys/data.key')

def _key():
    """Read the AES encryption key from file"""
    with open(KEY_FILE, 'rb') as f:
        return f.read()

def _cipher():
    """Create a Fernet cipher using the AES key"""
    return Fernet(_key())

# ─────────────────────────────────────────
# DATABASE CONNECTION
# ─────────────────────────────────────────
def _conn():
    """Connect to MySQL using environment variables"""
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'appuser'),
        password=os.environ.get('DB_PASSWORD', 'apppass'),
        database=os.environ.get('DB_NAME', 'patientdb')
    )

# ─────────────────────────────────────────
# SAVE — encrypt then store in MySQL
# ─────────────────────────────────────────
def save_record(obj):
    """
    1. Generate a patient_id if not provided
    2. Convert patient data to JSON string
    3. Encrypt it with AES (Fernet)
    4. Store encrypted blob in MySQL
    """
    pid = obj.get('patient_id') or str(uuid.uuid4())
    data = json.dumps(obj).encode('utf-8')   # dict → bytes
    enc = _cipher().encrypt(data)             # bytes → encrypted bytes

    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        "REPLACE INTO patients (patient_id, encrypted_data) VALUES (%s, %s)",
        (pid, enc)
    )
    conn.commit()
    cur.close()
    conn.close()
    return pid

# ─────────────────────────────────────────
# GET ONE — fetch and decrypt single record
# ─────────────────────────────────────────
def get_record(pid):
    """
    1. Query MySQL for this patient_id
    2. Decrypt the blob with AES
    3. Return as Python dict
    """
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT encrypted_data FROM patients WHERE patient_id = %s",
        (pid,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return None

    dec = _cipher().decrypt(bytes(row[0]))    # encrypted bytes → bytes
    return json.loads(dec.decode('utf-8'))    # bytes → dict

# ─────────────────────────────────────────
# GET ALL — fetch and decrypt all records
# ─────────────────────────────────────────
def get_all_records():
    """
    Fetch every patient record, decrypt each one,
    return as a list of dicts
    """
    conn = _conn()
    cur = conn.cursor()
    cur.execute("SELECT patient_id, encrypted_data FROM patients")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    result = []
    for pid, enc in rows:
        dec = _cipher().decrypt(bytes(enc))
        result.append(json.loads(dec.decode('utf-8')))
    return result