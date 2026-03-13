import time, json, os
from flask import g

AUDIT_FILE = 'audit.log'
RETENTION_DAYS = int(os.environ.get('RETENTION_DAYS', '30'))

# ─────────────────────────────────────────
# AUDIT LOG — records every action on data
# Required for healthcare compliance (HIPAA)
# ─────────────────────────────────────────
def audit_log(action, pid):
    """
    Called after every READ or CREATE operation.
    Writes a timestamped entry to audit.log.
    
    Example entry:
    {"ts": 1741840261, "user": "dr_smith", "action": "READ", "resource": "patient456"}
    """
    user = getattr(g, 'user', {})
    entry = {
        'ts': int(time.time()),
        'user': user.get('preferred_username', 'unknown'),
        'action': action,
        'resource': pid
    }
    # Print to console (visible in Docker logs)
    print(f"[AUDIT] {entry}")

    # Write to audit.log file
    with open(AUDIT_FILE, 'a') as f:
        f.write(json.dumps(entry) + '\n')

# ─────────────────────────────────────────
# DATA MINIMIZATION — only keep needed fields
# Never store more patient data than necessary
# ─────────────────────────────────────────
def data_minimize(payload):
    """
    Strips sensitive fields not needed for treatment.
    Example: removes SSN, passport number, etc.
    Only keeps: id, name, dob, consent
    """
    allowed = {k: payload[k] for k in ['id', 'name', 'dob', 'consent'] if k in payload}
    return allowed

# ─────────────────────────────────────────
# CONSENT ENFORCEMENT — patient must consent
# Cannot store data without patient agreement
# ─────────────────────────────────────────
def enforce_consent(payload):
    """
    Raises an error if patient has not given consent.
    This prevents storing data without permission.
    """
    if not payload.get('consent', False):
        raise ValueError('Consent required')

# ─────────────────────────────────────────
# RETENTION CLEANUP — delete old records
# Data must not be kept longer than necessary
# ─────────────────────────────────────────
def retention_cleanup():
    """
    Returns the cutoff timestamp.
    Records older than RETENTION_DAYS should be deleted.
    """
    cutoff = time.time() - RETENTION_DAYS * 24 * 3600
    return cutoff