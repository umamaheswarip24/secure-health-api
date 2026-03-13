\# Secure Patient Records API



A secure microservice for managing patient records with encryption, authentication, and CI/CD.



\## Architecture



\- \*\*Flask\*\* — REST API (HTTPS on port 8443)

\- \*\*MySQL\*\* — Encrypted patient data storage (AES/Fernet)

\- \*\*Keycloak\*\* — Identity \& Access Management (JWT + RBAC)

\- \*\*Jenkins\*\* — CI/CD pipeline with automated tests

\- \*\*Prometheus + Grafana\*\* — Monitoring and metrics

\- \*\*Loki + Promtail\*\* — Log aggregation



\## Security Features



\- AES encryption for all patient data at rest

\- JWT token authentication via Keycloak

\- Role-Based Access Control (viewer / editor roles)

\- TLS/HTTPS on port 8443

\- Audit logging for every data access



\## API Endpoints



| Method | Endpoint | Role Required | Description |

|--------|----------|---------------|-------------|

| POST | /records | editor | Create patient record |

| GET | /records/{id} | viewer, editor | Get one patient |

| GET | /records | viewer, editor | Get all patients |

| GET | /health | none | Health check |

| GET | /metrics | none | Prometheus metrics |



\## Quick Start



\### Prerequisites

\- Docker Desktop

\- Docker Compose



\### Run the stack

```bash

docker compose up -d

```



\### Services



| Service | URL |

|---------|-----|

| Flask API | https://localhost:8443 |

| Keycloak | http://localhost:8080 |

| Jenkins | http://localhost:9090 |

| Prometheus | http://localhost:9091 |

| Grafana | http://localhost:3000 |



\## Getting a Token

```bash

curl -X POST http://localhost:8080/realms/health/protocol/openid-connect/token \\

&#x20; -d "client\_id=health-api\&username=lab\_editor\&password=editor123\&grant\_type=password\&client\_secret=YOUR\_SECRET"

```



\## Testing the API

```bash

\# Create a patient record (editor role)

curl -k -X POST https://localhost:8443/records \\

&#x20; -H "Authorization: Bearer YOUR\_TOKEN" \\

&#x20; -H "Content-Type: application/json" \\

&#x20; -d '{"patient\_id":"p001","name":"John Doe","age":45,"diagnosis":"Diabetes"}'



\# Get a patient record (viewer role)

curl -k https://localhost:8443/records/p001 \\

&#x20; -H "Authorization: Bearer YOUR\_TOKEN"

```



\## Running Tests

```bash

docker run --rm -e APP\_DATA\_KEY=/tmp/test.key -e DB\_HOST=invalid -e TESTING=true health-api:local python -m pytest tests/ -v

```



\## Encrypted Data in MySQL



Data stored in MySQL is AES encrypted — unreadable without the key:

```

| patient\_id  | encrypted\_data                          |

|-------------|-----------------------------------------|

| patient456  | 0x6741414141414270744158303075477478...  |

```



\## Screenshots



\### 1. All Services Running

!\[Services](screenshots/01\_docker\_services.png)



\### 2. Jenkins Pipeline Success

!\[Jenkins](screenshots/02\_jenkins\_pipeline.png)



\### 3. Prometheus Metrics

!\[Prometheus](screenshots/03\_prometheus.png)



\### 4. Grafana Dashboard

!\[Grafana](screenshots/04\_grafana.png)



\### 5. All 7 Tests Passing

!\[Tests](screenshots/05\_tests\_passing.png)



\### 6. Encrypted Data in MySQL

!\[Encryption](screenshots/06\_mysql\_encrypted.png)



\## Project Structure

```

secure-health-api/

├── app/

│   ├── server.py         # Flask API

│   ├── auth.py           # JWT + RBAC

│   ├── storage.py        # MySQL + AES encryption

│   ├── compliance.py     # Audit log + consent

│   ├── Dockerfile

│   ├── requirements.txt

│   ├── conftest.py

│   ├── pytest.ini

│   └── tests/

│       └── test\_api.py   # 7 unit tests

├── db/

│   └── init.sql          # MySQL schema

├── monitoring/

│   ├── prometheus.yml

│   ├── loki-config.yml

│   └── promtail-config.yml

├── certs/                # TLS certificates

├── Jenkinsfile

├── docker-compose.yml

└── README.md

```



\## CI/CD Pipeline



Jenkins pipeline stages:

1\. \*\*Checkout\*\* — Get code

2\. \*\*Build\*\* — Build Docker image

3\. \*\*Test\*\* — Run 7 unit tests automatically

4\. \*\*Security Check\*\* — Verify security baseline

5\. \*\*Deploy\*\* — Start all services

