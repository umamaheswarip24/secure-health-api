-- Create the patients table
-- encrypted_data stores AES-encrypted JSON blobs
-- Nobody can read patient info directly from the DB

CREATE TABLE IF NOT EXISTS patients (
    patient_id   VARCHAR(64)  PRIMARY KEY,
    encrypted_data BLOB       NOT NULL,
    created_at   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);