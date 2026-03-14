# 🏥 Secure Patient Records Workflow

A production-grade secure microservice for managing patient records, demonstrating end-to-end healthcare data security with IAM, encryption, TLS, and CI/CD.

## 📋 Table of Contents
- [Architecture Overview](#architecture-overview)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [1. Backend Database (MySQL)](#1-backend-database-mysql)
- [2. Patient MicroService](#2-patient-microservice)
- [3. Security Constraints](#3-security-constraints)
- [4. CI/CD Pipeline (Jenkins)](#4-cicd-pipeline-jenkins)
- [Expected Outcomes](#expected-outcomes)
- [Screenshots](#screenshots)

---

## 🏗️ Architecture Overview
```
┌─────────────┐     JWT Token      ┌──────────────┐
│   Postman   │ ─────────────────► │   Keycloak   │
│   Client    │                    │  (IAM/RBAC)  │
└─────────────┘                    └──────────────┘
       │                                  │
       │ HTTPS (TLS)                      │ Verify Token
       ▼                                  ▼
┌─────────────┐    AES Encrypt    ┌──────────────┐
│  Flask API  │ ────────────────► │    MySQL     │
│  Port 8443  │                   │  (Encrypted  │
└─────────────┘                   │    BLOBs)    │
       │                          └──────────────┘
       │
┌──────┴───────┐
│   Jenkins    │  CI/CD: Build → Test → Deploy
│  Port 9090   │
└──────────────┘
```

---

## 🛠️ Technology Stack

| Component | Technology | Purpose |
|---|---|---|
| API Server | Python Flask | Patient records REST API |
| Database | MySQL 8.0 | Encrypted patient data storage |
| IAM | Keycloak 24.0 | Authentication & RBAC |
| Encryption | AES (Fernet) | Data at rest encryption |
| Transport | TLS/HTTPS | Data in transit encryption |
| CI/CD | Jenkins LTS | Automated build/test/deploy |
| Monitoring | Prometheus + Grafana | Metrics & dashboards |
| Logging | Loki + Promtail | Centralized log management |
| Container | Docker Compose | Service orchestration |

---

## 📁 Project Structure
```
secure-health-api/
├── app/
│   ├── server.py          # Flask API endpoints
│   ├── auth.py            # JWT verification + RBAC
│   ├── storage.py         # AES encryption + MySQL
│   ├── compliance.py      # Audit logging + data minimization
│   ├── Dockerfile         # Container definition
│   ├── requirements.txt   # Python dependencies
│   ├── conftest.py        # Pytest configuration
│   ├── pytest.ini         # Test settings
│   └── tests/
│       └── test_api.py    # 8 unit tests
├── db/
│   └── init.sql           # MySQL schema
├── certs/
│   ├── server.crt         # TLS certificate
│   └── server.key         # TLS private key
├── keys/
│   └── data.key           # AES encryption key
├── monitoring/
│   ├── prometheus.yml     # Prometheus config
│   ├── loki-config.yml    # Loki config
│   └── promtail-config.yml # Promtail config
├── jenkins/
│   └── Jenkinsfile        # CI/CD pipeline
├── scripts/
├── docker-compose.yml     # All services
├── Jenkinsfile            # Jenkins pipeline
├── keygen.py              # AES key generator
├── keyrotate.py           # AES key rotation
├── fix_keycloak.py        # Keycloak user setup
├── test_api.py            # End-to-end API tests
└── README.md
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Docker Desktop (with WSL2 on Windows)
- Python 3.10+
- Git

### Step 1: Clone the Repository
```bash
git clone https://github.com/umamaheswarip24/secure-health-api.git
cd secure-health-api
```

### Step 2: Generate AES Encryption Key
```bash
python keygen.py
```

### Step 3: Start All Services
```bash
docker compose up -d
```

### Step 4: Verify All Services Running
```bash
docker compose ps
```

All 8 services should be running:

![Docker Services](screenshots/01_docker_services.png)

### Step 5: Setup Keycloak
```bash
python fix_keycloak.py
```

This automatically:
- Creates the `health` realm
- Sets up `lab_editor` and `lab_viewer` users
- Assigns correct roles

---

## 1. Backend Database (MySQL)

### What it does
MySQL stores all patient records as **AES-encrypted BLOBs**. Even if someone accesses the database directly, they cannot read patient data.

### Database Schema
```sql
CREATE TABLE IF NOT EXISTS patients (
    patient_id     VARCHAR(64)  PRIMARY KEY,
    encrypted_data BLOB         NOT NULL,
    created_at     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);
```

### How Encryption Works
```python
# In storage.py
def save_record(obj):
    data = json.dumps(obj).encode('utf-8')   # dict → bytes
    enc = Fernet(key).encrypt(data)           # AES encrypt
    # Store encrypted BLOB in MySQL
    cur.execute("REPLACE INTO patients (patient_id, encrypted_data) VALUES (%s, %s)", (pid, enc))
```

### Proof: Data Cannot Be Read Directly
Running `SELECT * FROM patients` shows only encrypted binary data:

![MySQL Encrypted Data](screenshots/06_mysql_encrypted.png)

---

## 2. Patient MicroService

### API Endpoints

| Method | Endpoint | Role Required | Description |
|---|---|---|---|
| GET | `/health` | None | Health check |
| POST | `/records` | editor | Create patient record |
| GET | `/records/<pid>` | viewer, editor | Get one patient |
| GET | `/records` | viewer, editor | Get all patients |

### POST Patient Data API
Creates a new encrypted patient record in MySQL.

**Request:**
```json
{
  "patient_id": "patient001",
  "name": "John Doe",
  "age": 45,
  "diagnosis": "Diabetes",
  "consent": true
}
```

**Response:** `201 Created`
```json
{"id": "patient001"}
```

![Editor Creates Patient](screenshots/editor-creates-patient.png)

---

### GET One Patient API
Retrieves and decrypts a specific patient record.

**Response:** `200 OK`
```json
{
  "age": 45,
  "consent": true,
  "diagnosis": "Diabetes",
  "name": "John Doe",
  "patient_id": "patient001"
}
```

![Editor Reads One Patient](screenshots/editor-reads-one-patient.png)

---

### GET All Patients API
Retrieves and decrypts all patient records.

**Response:** `200 OK` — Returns array of all patients

![Editor Reads All Patients](screenshots/edirot-reads-all-patients.png)

---

## 3. Security Constraints

### 3.1 IAM with Keycloak (RBAC)

Two Lab Technician roles are enforced:

| User | Role | Can Read | Can Create |
|---|---|---|---|
| lab_viewer | viewer | ✅ Yes | ❌ No (403) |
| lab_editor | editor | ✅ Yes | ✅ Yes |

#### Keycloak Users
![Keycloak Users](screenshots/keycloak-users.png)

#### lab_editor Role Mapping
![Lab Editor Role](screenshots/lab-editor.png)

#### lab_viewer Role Mapping
![Lab Viewer Role](screenshots/lab-viewer.png)

#### Getting a JWT Token
```bash
curl -s -X POST http://localhost:8080/realms/health/protocol/openid-connect/token \
  -d "client_id=health-api&username=lab_editor&password=editor123&grant_type=password&client_secret=<secret>"
```

#### Viewer Can READ Records
![Viewer Reads Patient](screenshots/viewer-reads-one-patient.png)

#### Viewer Cannot CREATE Records (403 Forbidden)
![Viewer Forbidden](screenshots/viewer-creates-patient.png)

---

### 3.2 TLS Encryption in Transit

The API runs exclusively on HTTPS port 8443. Plain HTTP is rejected.
```bash
# HTTP fails
curl http://localhost:8443/health
# Result: Empty reply from server

# HTTPS works
curl -k https://localhost:8443/health
# Result: {"status": "ok"}
```

#### TLS Handshake Confirmation
![TLS Handshake](screenshots/tls-handshake.png)

#### Health Check via HTTPS
![Health Check](screenshots/health-check.png)

---

### 3.3 AES Encryption at Rest with Key Rotation

Patient data is encrypted using **Fernet (AES-128-CBC)** before storing in MySQL.

#### Key Generation
```bash
python keygen.py
# Generates: keys/data.key
```

#### Key Rotation
The `keyrotate.py` script:
1. Reads the current key
2. Generates a new key
3. Re-encrypts ALL records in MySQL with the new key
4. Backs up the old key
5. Saves the new key
```bash
python keyrotate.py
```

![Key Rotation](screenshots/key-rotation.png)

After rotation, restart the app to load the new key:
```bash
docker compose restart app
```

---

## 4. CI/CD Pipeline (Jenkins)

### Pipeline Stages
```
Checkout → Build → Test → Security Check → Deploy
```

| Stage | Action |
|---|---|
| Checkout | Get latest code |
| Build | Build Docker image |
| Test | Run 8 pytest unit tests |
| Security Check | Verify TLS + RBAC + AES |
| Deploy | Deploy via docker compose |

### Jenkins Dashboard
![Jenkins Dashboard](screenshots/02_jenkins_pipeline.png)

### Pipeline Console Output (All Tests Passing)
![Jenkins Pipeline](screenshots/03_jenkins_pipeline.png)

### Unit Tests (8 Tests)

| Test | What it Verifies |
|---|---|
| `test_data_minimize` | Sensitive fields stripped from patient data |
| `test_enforce_consent_denied` | Cannot store data without patient consent |
| `test_enforce_consent_granted` | Consent=True allows storage |
| `test_encryption_roundtrip` | AES encrypt→decrypt gives original data |
| `test_health_endpoint` | GET /health returns 200 OK |
| `test_post_record_editor` | POST /records works for editor role |
| `test_get_record_viewer` | GET /records/<pid> works for viewer role |
| `test_get_all_records_viewer` | GET /records works for viewer role |

![Tests Passing](screenshots/05_tests_passing.png)

---

## 📊 Expected Outcomes

### ✅ Secure Workflow via Postman
All API endpoints tested and verified with JWT tokens from Keycloak.

### ✅ Security & Compliance Proven
- **IAM enforces RBAC** — viewer gets 403 on POST, editor gets 201
- **TLS encrypts traffic** — schannel SSL/TLS handshake confirmed
- **AES encrypts data at rest** — MySQL shows unreadable binary BLOBs
- **Key rotation** — all records re-encrypted with new key seamlessly

### ✅ DevOps Integration
- Jenkins pipeline automates build → test → deploy
- 8 unit tests cover all API endpoints
- Docker Compose orchestrates all 8 services

### ✅ Real-World Workflow
- Models healthcare-grade security (HIPAA-ready audit logging)
- Demonstrates DevOps best practices
- Prometheus metrics + Grafana monitoring

![Prometheus Metrics](screenshots/03_prometheus.png)
![Grafana Dashboard](screenshots/04_grafana.png)

---

## 🔧 Service Ports

| Service | Port | URL |
|---|---|---|
| Flask API (HTTPS) | 8443 | https://localhost:8443 |
| Keycloak | 8080 | http://localhost:8080 |
| Jenkins | 9090 | http://localhost:9090 |
| MySQL | 3307 | localhost:3307 |
| Prometheus | 9091 | http://localhost:9091 |
| Grafana | 3000 | http://localhost:3000 |
| Loki | 3100 | http://localhost:3100 |

---

## 👤 Author
**umamaheswarip24**  
Secure Patient Records Workflow — Cloud & DevOps Security Assignment