# server.py
from flask import Flask, g, request
import time, json, os

AUDIT_FILE = 'audit.log'
RETENTION_DAYS = int(os.environ.get('RETENTION_DAYS','7'))

app = Flask(__name__)

def audit_log(action, pid):
    user = getattr(g, 'user', {})
    entry = {
        'ts': int(time.time()),
        'user': user.get('preferred_username', 'unknown'),
        'action': action,
        'resource': pid,
        'ip': request.remote_addr
    }
    with open(AUDIT_FILE,'a') as f:
        f.write(json.dumps(entry)+'\n')

def data_minimize(payload):
    # Only keep necessary fields
    return {k: payload[k] for k in ['id','name','dob','consent'] if k in payload}

def enforce_consent(payload):
    if not payload.get('consent', False):
        raise ValueError('Consent required')

def retention_cleanup():
    cutoff = time.time() - RETENTION_DAYS*24*3600
    new_entries = []
    with open(AUDIT_FILE,'r') as f:
        for line in f:
            entry = json.loads(line)
            if entry['ts'] >= cutoff:
                new_entries.append(entry)
    with open(AUDIT_FILE,'w') as f:
        for e in new_entries:
            f.write(json.dumps(e)+'\n')

@app.route("/patient/<int:pid>")
def view_patient(pid):
    g.user = {"preferred_username": "doctor_alice"}
    # Payload includes SSN
    payload = {"id":pid,"name":"Alice","dob":"1990-01-01","consent":True,"ssn":"123-45-6789"}
    enforce_consent(payload)
    minimized = data_minimize(payload)
    audit_log("view", minimized["id"])
    return minimized

if __name__ == "__main__":
    app.run(debug=True)