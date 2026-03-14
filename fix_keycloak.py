import requests, json

# Step 1: Get admin token
r = requests.post('http://localhost:8080/realms/master/protocol/openid-connect/token', data={'client_id':'admin-cli','username':'admin','password':'admin','grant_type':'password'})
token = r.json()['access_token']
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
print('Got admin token!')

# Step 2: Fix lab_editor
r = requests.put('http://localhost:8080/admin/realms/health/users/9fdba8e0-e80b-46d2-bc17-807de61a1cef', headers=headers, json={'requiredActions':[],'emailVerified':True,'firstName':'Lab','lastName':'Editor','email':'lab_editor@health.local'})
print('Fixed lab_editor:', r.status_code)

# Step 3: Get lab_viewer ID and fix
r = requests.get('http://localhost:8080/admin/realms/health/users?username=lab_viewer', headers=headers)
viewer_id = r.json()[0]['id']
r = requests.put(f'http://localhost:8080/admin/realms/health/users/{viewer_id}', headers=headers, json={'requiredActions':[],'emailVerified':True,'firstName':'Lab','lastName':'Viewer','email':'lab_viewer@health.local'})
print('Fixed lab_viewer:', r.status_code)

# Step 4: Test editor token
r = requests.post('http://localhost:8080/realms/health/protocol/openid-connect/token', data={'client_id':'health-api','username':'lab_editor','password':'editor123','grant_type':'password','client_secret':'nGHQ2vU74C3PbZtX67sHdjNz82wXr2HH'})
print('Editor token result:', r.status_code)
if 'access_token' in r.json():
    print('SUCCESS! Got token!')
else:
    print('Error:', r.json())