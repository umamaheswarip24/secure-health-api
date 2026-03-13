import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# ═════════════════════════════════════════
# TEST 1 — Data Minimization
# ═════════════════════════════════════════
def test_data_minimize():
    from compliance import data_minimize
    patient = {
        'id': '1',
        'name': 'Alice',
        'dob': '2000-01-01',
        'consent': True,
        'ssn': 'SECRET-123',
        'passport': 'P123456'
    }
    result = data_minimize(patient)
    assert 'ssn' not in result, "SSN should be stripped"
    assert 'passport' not in result, "Passport should be stripped"
    assert 'name' in result, "Name should be kept"
    assert 'dob' in result, "DOB should be kept"
    assert 'consent' in result, "Consent should be kept"


# ═════════════════════════════════════════
# TEST 2 — Consent Denied
# ═════════════════════════════════════════
def test_enforce_consent_denied():
    from compliance import enforce_consent
    try:
        enforce_consent({'consent': False})
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert 'Consent' in str(e)


# ═════════════════════════════════════════
# TEST 3 — Consent Granted
# ═════════════════════════════════════════
def test_enforce_consent_granted():
    from compliance import enforce_consent
    enforce_consent({'consent': True})


# ═════════════════════════════════════════
# TEST 4 — AES Encryption Round-trip
# ═════════════════════════════════════════
def test_encryption_roundtrip():
    from cryptography.fernet import Fernet
    import json
    key = Fernet.generate_key()
    cipher = Fernet(key)
    original = {
        'patient_id': 'p001',
        'name': 'John Doe',
        'diagnosis': 'Diabetes'
    }
    data_bytes = json.dumps(original).encode('utf-8')
    encrypted = cipher.encrypt(data_bytes)
    assert encrypted != data_bytes, "Encrypted data should differ from original"
    decrypted = cipher.decrypt(encrypted)
    result = json.loads(decrypted.decode('utf-8'))
    assert result == original, "Decrypted data should match original"


# ═════════════════════════════════════════
# TEST 5 — Health Endpoint
# ═════════════════════════════════════════
def test_health_endpoint():
    import server
    server.app.config['TESTING'] = True
    client = server.app.test_client()
    response = client.get('/health')
    assert response.status_code == 200
    assert response.get_json()['status'] == 'ok'


# ═════════════════════════════════════════
# TEST 6 — POST /records (editor role)
# ═════════════════════════════════════════
def test_post_record_editor(monkeypatch):
    import server, storage
    monkeypatch.setattr(storage, 'save_record', lambda obj: 'mock-id-123')
    monkeypatch.setattr(server, 'save_record', lambda obj: 'mock-id-123')

    server.app.config['TESTING'] = True
    client = server.app.test_client()

    response = client.post(
        '/records',
        json={'patient_id': 'p001', 'name': 'John', 'diagnosis': 'Flu'},
        headers={
            'Authorization': 'Bearer fake-token',
            'X-Test-Role': 'editor'
        }
    )
    assert response.status_code == 201
    assert response.get_json()['id'] == 'mock-id-123'

# ═════════════════════════════════════════
# TEST 7 — GET /records/<pid> (viewer role)
# ═════════════════════════════════════════
def test_get_record_viewer(monkeypatch):
    import server, storage
    mock_patient = {'patient_id': 'p001', 'name': 'John', 'diagnosis': 'Flu'}
    monkeypatch.setattr(server, 'get_record', lambda pid: mock_patient)
    monkeypatch.setattr(storage, 'get_record', lambda pid: mock_patient)

    server.app.config['TESTING'] = True
    client = server.app.test_client()

    response = client.get(
        '/records/p001',
        headers={
            'Authorization': 'Bearer fake-token',
            'X-Test-Role': 'viewer'
        }
    )
    assert response.status_code == 200
    assert response.get_json()['name'] == 'John'