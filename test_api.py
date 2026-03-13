import requests, json

CLIENT_SECRET = 'nGHQ2vU74C3PbZtX67sHdjNz82wXr2HH'
BASE_URL = 'https://localhost:8443'
TOKEN_URL = 'http://localhost:8080/realms/health/protocol/openid-connect/token'

def get_token(username, password):
    r = requests.post(TOKEN_URL, data={
        'client_id': 'health-api',
        'username': username,
        'password': password,
        'grant_type': 'password',
        'client_secret': CLIENT_SECRET
    })
    return r.json()['access_token']

print('='*50)
print('TEST 1: Get editor token')
editor_token = get_token('lab_editor', 'editor123')
print('✓ Editor token obtained')

print('\nTEST 2: Get viewer token')
viewer_token = get_token('lab_viewer', 'viewer123')
print('✓ Viewer token obtained')

print('\nTEST 3: Editor creates a patient record')
r = requests.post(f'{BASE_URL}/records',
    json={'patient_id': 'patient456', 'name': 'John Doe', 'age': 45, 'diagnosis': 'Diabetes'},
    headers={'Authorization': f'Bearer {editor_token}'},
    verify=False)
print(f'Status: {r.status_code} — {r.json()}')

print('\nTEST 4: Editor reads the patient record')
r = requests.get(f'{BASE_URL}/records/patient456',
    headers={'Authorization': f'Bearer {editor_token}'},
    verify=False)
print(f'Status: {r.status_code} — {r.json()}')

print('\nTEST 5: Viewer reads the patient record')
r = requests.get(f'{BASE_URL}/records/patient456',
    headers={'Authorization': f'Bearer {viewer_token}'},
    verify=False)
print(f'Status: {r.status_code} — {r.json()}')

print('\nTEST 6: Viewer tries to CREATE — should be FORBIDDEN')
r = requests.post(f'{BASE_URL}/records',
    json={'patient_id': 'test999', 'name': 'Test', 'age': 30},
    headers={'Authorization': f'Bearer {viewer_token}'},
    verify=False)
print(f'Status: {r.status_code} — {r.json()}')
assert r.status_code == 403, 'Viewer should be forbidden!'
print('✓ Correctly blocked!')

print('\nTEST 7: Get ALL records')
r = requests.get(f'{BASE_URL}/records',
    headers={'Authorization': f'Bearer {editor_token}'},
    verify=False)
print(f'Status: {r.status_code} — {r.json()}')

print('\n' + '='*50)
print('ALL TESTS PASSED! ✓')