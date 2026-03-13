from flask import Flask, request, jsonify
from auth import verify_jwt, require_roles
from compliance import audit_log
from storage import save_record, get_record, get_all_records
from prometheus_client import Counter, Histogram, generate_latest

app = Flask(__name__)

# ─────────────────────────────────────────
# PROMETHEUS METRICS
# Counts requests and measures response time
# ─────────────────────────────────────────
REQUEST_COUNT = Counter(
    'api_requests_total',
    'Total API requests',
    ['endpoint', 'method', 'status']
)
REQ_LATENCY = Histogram(
    'api_request_latency_seconds',
    'Request latency',
    ['endpoint']
)

# ─────────────────────────────────────────
# HEALTH CHECK — no auth needed
# Used by Docker/Jenkins to verify app is up
# ─────────────────────────────────────────
@app.route('/health')
def health():
    return jsonify({'status': 'ok'}), 200

# ─────────────────────────────────────────
# METRICS — no auth needed
# Prometheus scrapes this endpoint
# ─────────────────────────────────────────
@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': 'text/plain; charset=utf-8'}

# ─────────────────────────────────────────
# POST /records — CREATE a patient record
# Only 'editor' role can create
# ─────────────────────────────────────────
@app.route('/records', methods=['POST'])
@verify_jwt
@require_roles(['editor'])
def create_patient():
    """
    1. Verify JWT token (auth.py)
    2. Check user has 'editor' role
    3. Encrypt + save to MySQL (storage.py)
    4. Log the action (compliance.py)
    5. Return the new patient_id
    """
    payload = request.get_json()
    pid = save_record(payload)
    audit_log('CREATE', pid)
    REQUEST_COUNT.labels('/records', 'POST', '201').inc()
    return jsonify({'id': pid}), 201

# ─────────────────────────────────────────
# GET /records/<pid> — GET one patient
# Both 'viewer' and 'editor' roles can read
# ─────────────────────────────────────────
@app.route('/records/<pid>', methods=['GET'])
@verify_jwt
@require_roles(['viewer', 'editor'])
def get_patient(pid):
    """
    1. Verify JWT token
    2. Check user has viewer or editor role
    3. Fetch + decrypt from MySQL
    4. Return patient data as JSON
    """
    with REQ_LATENCY.labels('/records').time():
        data = get_record(pid)
    audit_log('READ', pid)
    if data:
        REQUEST_COUNT.labels('/records', 'GET', '200').inc()
        return jsonify(data), 200
    REQUEST_COUNT.labels('/records', 'GET', '404').inc()
    return jsonify({'error': 'not found'}), 404

# ─────────────────────────────────────────
# GET /records — GET all patients
# Both 'viewer' and 'editor' roles can read
# ─────────────────────────────────────────
@app.route('/records', methods=['GET'])
@verify_jwt
@require_roles(['viewer', 'editor'])
def get_all_patients():
    """
    1. Verify JWT token
    2. Check user has viewer or editor role
    3. Fetch + decrypt ALL records from MySQL
    4. Return list of patient data as JSON
    """
    with REQ_LATENCY.labels('/records/all').time():
        data = get_all_records()
    audit_log('READ_ALL', 'all')
    REQUEST_COUNT.labels('/records', 'GET', '200').inc()
    return jsonify(data), 200

# ─────────────────────────────────────────
# START SERVER with TLS (HTTPS on port 8443)
# ─────────────────────────────────────────
if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=8443,
        ssl_context=('certs/server.crt', 'certs/server.key')
    )