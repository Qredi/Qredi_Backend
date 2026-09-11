"""
Seeder: 2 new Lender users + LenderProfile rows for all 3 organizations.

Ties the existing lender (lender@qredi.test) and 2 new lenders to the
3 organizations created earlier (Bank Nusantara Sejahtera, Fintech Maju
Bersama, Bank Cahaya Mandiri). Appends new credentials to
generated_credentials.json (does not overwrite existing entries).
"""

import uuid
import random
import json
import os
from sqlalchemy import create_engine, text
from pwdlib import PasswordHash
from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL
CREDENTIALS_OUTPUT_FILE = "generated_credentials.json"

random.seed(42)

password_hash = PasswordHash.recommended()

def hash_password(plain_password: str) -> str:
    return password_hash.hash(plain_password)

def random_phone():
    return "0813" + "".join(str(random.randint(0, 9)) for _ in range(8))

# --- Organizations created earlier (fixed UUIDs from the prior INSERT) ---
ORG_BANK_NUSANTARA = "a1f3c2e4-7b8d-4c1a-9e2f-3d4b5a6c7d8e"
ORG_FINTECH_MAJU = "b2e4d3f5-8c9e-4d2b-af3a-4e5c6b7d8e9f"
ORG_BANK_CAHAYA = "c3f5e4a6-9daf-4e3c-b04b-5f6d7c8e9fa0"

# --- Existing lender from the original seeder ---
EXISTING_LENDER_EMAIL = "lender@qredi.test"
EXISTING_LENDER_PASSWORD = "Lender12345!"

def main():
    engine = create_engine(DATABASE_URL)
    lender_password = "Lender12345!"

    print("Hashing password using Argon2id...")
    hashed_lender_pass = hash_password(lender_password)

    # --- New lender users ---
    lender2_id = str(uuid.uuid4())
    lender3_id = str(uuid.uuid4())

    new_users_data = [
        {
            "id": lender2_id,
            "email": "lender2@qredi.test",
            "hashed_password": hashed_lender_pass,
            "full_name": "Fintech Maju Bersama",
            "phone_number": random_phone(),
            "role": "LENDER",
        },
        {
            "id": lender3_id,
            "email": "lender3@qredi.test",
            "hashed_password": hashed_lender_pass,
            "full_name": "Bank Cahaya Mandiri",
            "phone_number": random_phone(),
            "role": "LENDER",
        },
    ]

    new_credentials = [
        {"role": "LENDER", "full_name": "Fintech Maju Bersama", "email": "lender2@qredi.test", "password": lender_password},
        {"role": "LENDER", "full_name": "Bank Cahaya Mandiri", "email": "lender3@qredi.test", "password": lender_password},
    ]

    with engine.begin() as conn:
        print("Inserting new lender users...")
        conn.execute(text("""
            INSERT INTO users (id, email, hashed_password, full_name, phone_number, role, email_verified, is_active)
            VALUES (cast(:id as uuid), :email, :hashed_password, :full_name, :phone_number, cast(:role as user_role), true, true)
            ON CONFLICT (email) DO NOTHING
        """), new_users_data)

        # Look up the existing lender's user_id (created by the original seeder)
        existing_lender = conn.execute(text("""
            SELECT id FROM users WHERE email = :email
        """), {"email": EXISTING_LENDER_EMAIL}).fetchone()

        if existing_lender is None:
            raise RuntimeError(
                f"Existing lender '{EXISTING_LENDER_EMAIL}' not found. "
                "Run the original seeder first before this one."
            )
        existing_lender_id = str(existing_lender[0])

        # --- LenderProfile rows for all 3 lenders ---
        lender_profiles_data = [
            {
                "id": str(uuid.uuid4()),
                "user_id": existing_lender_id,
                "organization_id": ORG_BANK_NUSANTARA,
                "position": "Relationship Manager",
                "max_loan_amount": 50_000_000,
                "min_acs_score": 70,
            },
            {
                "id": str(uuid.uuid4()),
                "user_id": lender2_id,
                "organization_id": ORG_FINTECH_MAJU,
                "position": "Credit Analyst",
                "max_loan_amount": 100_000_000,
                "min_acs_score": 55,
            },
            {
                "id": str(uuid.uuid4()),
                "user_id": lender3_id,
                "organization_id": ORG_BANK_CAHAYA,
                "position": "Loan Officer",
                "max_loan_amount": 25_000_000,
                "min_acs_score": 40,
            },
        ]

        print("Inserting lender_profiles...")
        conn.execute(text("""
            INSERT INTO lender_profiles (
                id, user_id, organization_id, position, max_loan_amount, min_acs_score
            )
            VALUES (
                cast(:id as uuid), cast(:user_id as uuid), cast(:organization_id as uuid),
                :position, :max_loan_amount, :min_acs_score
            )
            ON CONFLICT (user_id) DO NOTHING
        """), lender_profiles_data)

    # --- Append to credentials JSON (don't overwrite existing entries) ---
    existing_credentials = []
    if os.path.exists(CREDENTIALS_OUTPUT_FILE):
        with open(CREDENTIALS_OUTPUT_FILE, "r") as f:
            existing_credentials = json.load(f)

    existing_credentials.extend(new_credentials)

    with open(CREDENTIALS_OUTPUT_FILE, "w") as f:
        json.dump(existing_credentials, f, indent=4)

    print("✅ 2 new lenders + 3 lender_profiles inserted.")
    print(f"✅ Credentials appended to '{CREDENTIALS_OUTPUT_FILE}'.")

if __name__ == "__main__":
    main()