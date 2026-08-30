"""
End-to-end API tests for the Qredi backend.

Run with:
    pytest tests/test_api.py -v

Deps (on top of the app's own requirements):
    pip install pytest httpx --break-system-packages

Each test function gets a fully fresh in-memory SQLite database (see the
`client` fixture), so tests are isolated and order-independent.
"""

import os

# Must be set before `app.database` is imported anywhere, otherwise
# create_engine() will try to load the postgres driver and blow up if
# psycopg2 isn't installed in the test environment.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from main import app

API = "/api/v1"


# //====== FIXTURES ======//

@pytest.fixture()
def db_engine():
    """Fresh in-memory SQLite DB per test, all tables created via metadata."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def client(db_engine):
    TestingSessionLocal = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def register_user(client, email, password, full_name, role):
    r = client.post(
        f"{API}/auth/register",
        json={"email": email, "password": password, "full_name": full_name, "role": role},
    )
    assert r.status_code == 201, r.text
    return r.json()


def login(client, email, password):
    r = client.post(f"{API}/auth/login", data={"username": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def seeded(client):
    """Registers one admin, one UMKM, one lender, logs each in, and creates
    an organization for the lender to attach to. Returns a dict of
    ids/tokens used across most feature tests."""
    admin = register_user(client, "admin@test.com", "AdminPass123", "Admin", "admin")
    umkm = register_user(client, "umkm@test.com", "UmkmPass123", "UMKM Owner", "umkm")
    lender = register_user(client, "lender@test.com", "LenderPass123", "Lender Rep", "lender")

    admin_token = login(client, "admin@test.com", "AdminPass123")
    umkm_token = login(client, "umkm@test.com", "UmkmPass123")
    lender_token = login(client, "lender@test.com", "LenderPass123")

    org = client.post(
        f"{API}/organizations/",
        json={"name": "Bank Test", "type": "bank"},
        headers=auth_header(admin_token),
    )
    assert org.status_code == 200, org.text

    return {
        "admin": {"id": admin["id"], "token": admin_token},
        "umkm": {"id": umkm["id"], "token": umkm_token},
        "lender": {"id": lender["id"], "token": lender_token},
        "org_id": org.json()["id"],
    }


# //====== HEALTH ======//

def test_health_check(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "Backend Service is Running"}


# //====== AUTH ======//

def test_register_user_success(client):
    body = register_user(client, "new@test.com", "SomePass123", "New Person", "umkm")
    assert body["email"] == "new@test.com"
    assert body["role"] == "umkm"
    assert body["is_active"] is True
    assert "id" in body


def test_register_duplicate_email_fails(client):
    register_user(client, "dupe@test.com", "SomePass123", "First", "umkm")
    r = client.post(
        f"{API}/auth/register",
        json={"email": "dupe@test.com", "password": "SomePass123", "full_name": "Second", "role": "umkm"},
    )
    assert r.status_code == 400


def test_login_success(client):
    register_user(client, "loginok@test.com", "SomePass123", "Login OK", "umkm")
    token = login(client, "loginok@test.com", "SomePass123")
    assert isinstance(token, str) and len(token) > 0


def test_login_wrong_password_fails(client):
    register_user(client, "loginbad@test.com", "SomePass123", "Login Bad", "umkm")
    r = client.post(f"{API}/auth/login", data={"username": "loginbad@test.com", "password": "WrongPass"})
    assert r.status_code == 401


def test_login_unknown_email_fails(client):
    r = client.post(f"{API}/auth/login", data={"username": "ghost@test.com", "password": "whatever"})
    assert r.status_code == 401


def test_unauthenticated_request_rejected(client):
    r = client.get(f"{API}/users/me")
    assert r.status_code == 401


# //====== USERS ======//

def test_get_my_profile(client, seeded):
    r = client.get(f"{API}/users/me", headers=auth_header(seeded["umkm"]["token"]))
    assert r.status_code == 200
    assert r.json()["email"] == "umkm@test.com"


def test_list_users_requires_admin(client, seeded):
    r = client.get(f"{API}/users/", headers=auth_header(seeded["umkm"]["token"]))
    assert r.status_code == 403


def test_list_users_as_admin(client, seeded):
    r = client.get(f"{API}/users/", headers=auth_header(seeded["admin"]["token"]))
    assert r.status_code == 200
    assert len(r.json()) == 3


def test_list_users_filtered_by_role(client, seeded):
    r = client.get(f"{API}/users/?role=lender", headers=auth_header(seeded["admin"]["token"]))
    assert r.status_code == 200
    assert all(u["role"] == "lender" for u in r.json())


def test_deactivate_user_as_admin(client, seeded):
    target_id = seeded["umkm"]["id"]
    r = client.patch(f"{API}/users/{target_id}/deactivate", headers=auth_header(seeded["admin"]["token"]))
    assert r.status_code == 200
    assert r.json()["is_active"] is False


def test_deactivate_user_requires_admin(client, seeded):
    target_id = seeded["lender"]["id"]
    r = client.patch(f"{API}/users/{target_id}/deactivate", headers=auth_header(seeded["umkm"]["token"]))
    assert r.status_code == 403


# //====== ORGANIZATIONS ======//

def test_create_organization_as_admin(client, seeded):
    r = client.post(
        f"{API}/organizations/",
        json={"name": "Fintech Co", "type": "fintech"},
        headers=auth_header(seeded["admin"]["token"]),
    )
    assert r.status_code == 200
    assert r.json()["is_active"] is True


def test_create_organization_requires_admin(client, seeded):
    r = client.post(
        f"{API}/organizations/",
        json={"name": "Blocked Bank", "type": "bank"},
        headers=auth_header(seeded["lender"]["token"]),
    )
    assert r.status_code == 403


def test_create_organization_duplicate_name_fails(client, seeded):
    r = client.post(
        f"{API}/organizations/",
        json={"name": "Bank Test", "type": "bank"},
        headers=auth_header(seeded["admin"]["token"]),
    )
    assert r.status_code == 400


def test_get_organization(client, seeded):
    r = client.get(f"{API}/organizations/{seeded['org_id']}")
    assert r.status_code == 200
    assert r.json()["id"] == seeded["org_id"]


def test_list_organizations(client, seeded):
    r = client.get(f"{API}/organizations/")
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_deactivate_organization_as_admin(client, seeded):
    r = client.patch(
        f"{API}/organizations/{seeded['org_id']}/deactivate",
        headers=auth_header(seeded["admin"]["token"]),
    )
    assert r.status_code == 200
    assert r.json()["is_active"] is False


# //====== UMKM PROFILES ======//

def test_create_my_umkm_profile(client, seeded):
    r = client.post(
        f"{API}/umkm-profiles/me",
        json={"business_name": "Warung Ibu", "city": "Jakarta"},
        headers=auth_header(seeded["umkm"]["token"]),
    )
    assert r.status_code == 201
    assert r.json()["business_name"] == "Warung Ibu"


def test_create_umkm_profile_wrong_role_fails(client, seeded):
    r = client.post(
        f"{API}/umkm-profiles/me",
        json={"business_name": "Should Fail"},
        headers=auth_header(seeded["lender"]["token"]),
    )
    assert r.status_code == 403


def test_create_umkm_profile_duplicate_fails(client, seeded):
    client.post(
        f"{API}/umkm-profiles/me",
        json={"business_name": "First"},
        headers=auth_header(seeded["umkm"]["token"]),
    )
    r = client.post(
        f"{API}/umkm-profiles/me",
        json={"business_name": "Second"},
        headers=auth_header(seeded["umkm"]["token"]),
    )
    assert r.status_code == 400


def test_get_my_umkm_profile(client, seeded):
    client.post(
        f"{API}/umkm-profiles/me",
        json={"business_name": "Warung Ibu", "city": "Jakarta"},
        headers=auth_header(seeded["umkm"]["token"]),
    )
    r = client.get(f"{API}/umkm-profiles/me", headers=auth_header(seeded["umkm"]["token"]))
    assert r.status_code == 200
    assert r.json()["city"] == "Jakarta"


def test_update_my_umkm_profile(client, seeded):
    client.post(
        f"{API}/umkm-profiles/me",
        json={"business_name": "Warung Ibu", "city": "Jakarta"},
        headers=auth_header(seeded["umkm"]["token"]),
    )
    r = client.patch(
        f"{API}/umkm-profiles/me",
        json={"city": "Bandung"},
        headers=auth_header(seeded["umkm"]["token"]),
    )
    assert r.status_code == 200
    assert r.json()["city"] == "Bandung"
    assert r.json()["business_name"] == "Warung Ibu"  # untouched field preserved


def test_get_umkm_profile_by_user_as_owner(client, seeded):
    client.post(
        f"{API}/umkm-profiles/me",
        json={"business_name": "Warung Ibu"},
        headers=auth_header(seeded["umkm"]["token"]),
    )
    r = client.get(
        f"{API}/umkm-profiles/by-user/{seeded['umkm']['id']}",
        headers=auth_header(seeded["umkm"]["token"]),
    )
    assert r.status_code == 200


def test_get_umkm_profile_by_user_forbidden_for_other_user(client, seeded):
    client.post(
        f"{API}/umkm-profiles/me",
        json={"business_name": "Warung Ibu"},
        headers=auth_header(seeded["umkm"]["token"]),
    )
    r = client.get(
        f"{API}/umkm-profiles/by-user/{seeded['umkm']['id']}",
        headers=auth_header(seeded["lender"]["token"]),
    )
    assert r.status_code == 403


def test_list_umkm_profiles_requires_filter(client, seeded):
    r = client.get(f"{API}/umkm-profiles/", headers=auth_header(seeded["admin"]["token"]))
    assert r.status_code == 400


def test_list_umkm_profiles_by_city(client, seeded):
    client.post(
        f"{API}/umkm-profiles/me",
        json={"business_name": "Warung Ibu", "city": "Jakarta"},
        headers=auth_header(seeded["umkm"]["token"]),
    )
    r = client.get(f"{API}/umkm-profiles/?city=Jakarta", headers=auth_header(seeded["admin"]["token"]))
    assert r.status_code == 200
    assert len(r.json()) == 1


# //====== LENDER PROFILES ======//

def test_create_my_lender_profile(client, seeded):
    r = client.post(
        f"{API}/lender-profiles/me",
        json={"organization_id": seeded["org_id"], "position": "Analyst"},
        headers=auth_header(seeded["lender"]["token"]),
    )
    assert r.status_code == 201
    assert r.json()["position"] == "Analyst"


def test_create_lender_profile_wrong_role_fails(client, seeded):
    r = client.post(
        f"{API}/lender-profiles/me",
        json={"organization_id": seeded["org_id"]},
        headers=auth_header(seeded["umkm"]["token"]),
    )
    assert r.status_code == 403


def test_create_lender_profile_unknown_org_fails(client, seeded):
    fake_org_id = "00000000-0000-0000-0000-000000000000"
    r = client.post(
        f"{API}/lender-profiles/me",
        json={"organization_id": fake_org_id},
        headers=auth_header(seeded["lender"]["token"]),
    )
    assert r.status_code == 404


def test_get_my_lender_profile(client, seeded):
    client.post(
        f"{API}/lender-profiles/me",
        json={"organization_id": seeded["org_id"]},
        headers=auth_header(seeded["lender"]["token"]),
    )
    r = client.get(f"{API}/lender-profiles/me", headers=auth_header(seeded["lender"]["token"]))
    assert r.status_code == 200


def test_update_my_lender_profile(client, seeded):
    client.post(
        f"{API}/lender-profiles/me",
        json={"organization_id": seeded["org_id"]},
        headers=auth_header(seeded["lender"]["token"]),
    )
    r = client.patch(
        f"{API}/lender-profiles/me",
        json={"max_loan_amount": 10_000_000},
        headers=auth_header(seeded["lender"]["token"]),
    )
    assert r.status_code == 200
    assert r.json()["max_loan_amount"] == 10_000_000


def test_list_lender_profiles_by_organization_as_admin(client, seeded):
    client.post(
        f"{API}/lender-profiles/me",
        json={"organization_id": seeded["org_id"]},
        headers=auth_header(seeded["lender"]["token"]),
    )
    r = client.get(
        f"{API}/lender-profiles/by-organization/{seeded['org_id']}",
        headers=auth_header(seeded["admin"]["token"]),
    )
    assert r.status_code == 200
    assert len(r.json()) == 1


# //====== QRIS TRANSACTIONS ======//

def test_ingest_qris_transaction_as_admin(client, seeded):
    r = client.post(
        f"{API}/qris-transactions/",
        json={
            "user_id": seeded["umkm"]["id"],
            "amount": 50000,
            "transaction_type": "payment",
            "transaction_time": "2026-07-01T10:00:00",
        },
        headers=auth_header(seeded["admin"]["token"]),
    )
    assert r.status_code == 201
    assert r.json()["amount"] == 50000


def test_ingest_qris_transaction_requires_admin(client, seeded):
    r = client.post(
        f"{API}/qris-transactions/",
        json={
            "user_id": seeded["umkm"]["id"],
            "amount": 50000,
            "transaction_type": "payment",
            "transaction_time": "2026-07-01T10:00:00",
        },
        headers=auth_header(seeded["umkm"]["token"]),
    )
    assert r.status_code == 403


def test_ingest_qris_transaction_duplicate_reference_fails(client, seeded):
    payload = {
        "user_id": seeded["umkm"]["id"],
        "amount": 50000,
        "transaction_type": "payment",
        "transaction_time": "2026-07-01T10:00:00",
        "qris_reference": "REF-001",
    }
    ok = client.post(f"{API}/qris-transactions/", json=payload, headers=auth_header(seeded["admin"]["token"]))
    assert ok.status_code == 201

    dupe = client.post(f"{API}/qris-transactions/", json=payload, headers=auth_header(seeded["admin"]["token"]))
    assert dupe.status_code == 400


def test_list_my_qris_transactions(client, seeded):
    client.post(
        f"{API}/qris-transactions/",
        json={
            "user_id": seeded["umkm"]["id"],
            "amount": 25000,
            "transaction_type": "payment",
            "transaction_time": "2026-07-02T09:00:00",
        },
        headers=auth_header(seeded["admin"]["token"]),
    )
    r = client.get(f"{API}/qris-transactions/me", headers=auth_header(seeded["umkm"]["token"]))
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_list_fraud_flagged_requires_admin(client, seeded):
    r = client.get(f"{API}/qris-transactions/fraud-flagged", headers=auth_header(seeded["umkm"]["token"]))
    assert r.status_code == 403


def test_list_fraud_flagged_as_admin(client, seeded):
    client.post(
        f"{API}/qris-transactions/",
        json={
            "user_id": seeded["umkm"]["id"],
            "amount": 999999,
            "transaction_type": "payment",
            "transaction_time": "2026-07-02T09:00:00",
            "fraud_flag": True,
        },
        headers=auth_header(seeded["admin"]["token"]),
    )
    r = client.get(f"{API}/qris-transactions/fraud-flagged", headers=auth_header(seeded["admin"]["token"]))
    assert r.status_code == 200
    assert len(r.json()) == 1


# //====== SCORES ======//

def test_record_score_derives_low_risk(client, seeded):
    r = client.post(
        f"{API}/scores/",
        json={"user_id": seeded["umkm"]["id"], "acs_score": 720},
        headers=auth_header(seeded["admin"]["token"]),
    )
    assert r.status_code == 200
    assert r.json()["risk_level"] == "low"


def test_record_score_derives_medium_risk(client, seeded):
    r = client.post(
        f"{API}/scores/",
        json={"user_id": seeded["umkm"]["id"], "acs_score": 550},
        headers=auth_header(seeded["admin"]["token"]),
    )
    assert r.status_code == 200
    assert r.json()["risk_level"] == "medium"


def test_record_score_derives_high_risk(client, seeded):
    r = client.post(
        f"{API}/scores/",
        json={"user_id": seeded["umkm"]["id"], "acs_score": 300},
        headers=auth_header(seeded["admin"]["token"]),
    )
    assert r.status_code == 200
    assert r.json()["risk_level"] == "high"


def test_record_score_requires_admin(client, seeded):
    r = client.post(
        f"{API}/scores/",
        json={"user_id": seeded["umkm"]["id"], "acs_score": 700},
        headers=auth_header(seeded["lender"]["token"]),
    )
    assert r.status_code == 403


def test_get_my_latest_score(client, seeded):
    client.post(
        f"{API}/scores/",
        json={"user_id": seeded["umkm"]["id"], "acs_score": 650},
        headers=auth_header(seeded["admin"]["token"]),
    )
    r = client.get(f"{API}/scores/me/latest", headers=auth_header(seeded["umkm"]["token"]))
    assert r.status_code == 200
    assert r.json()["acs_score"] == 650


def test_get_my_latest_score_404_when_none(client, seeded):
    r = client.get(f"{API}/scores/me/latest", headers=auth_header(seeded["umkm"]["token"]))
    assert r.status_code == 404


def test_get_my_score_history_returns_all_recorded_scores(client, seeded):
    for value in (600, 650, 700):
        client.post(
            f"{API}/scores/",
            json={"user_id": seeded["umkm"]["id"], "acs_score": value},
            headers=auth_header(seeded["admin"]["token"]),
        )
    r = client.get(f"{API}/scores/me/history", headers=auth_header(seeded["umkm"]["token"]))
    assert r.status_code == 200
    scores = {s["acs_score"] for s in r.json()}
    assert scores == {600, 650, 700}


# //====== LOAN OUTCOMES ======//

def test_create_loan_as_lender(client, seeded):
    r = client.post(
        f"{API}/loans/",
        json={
            "user_id": seeded["umkm"]["id"],
            "loan_amount": 5_000_000,
            "loan_term_months": 6,
            "due_date": "2027-01-01T00:00:00",
        },
        headers=auth_header(seeded["lender"]["token"]),
    )
    assert r.status_code == 200
    assert r.json()["status"] == "active"


def test_create_loan_requires_lender(client, seeded):
    r = client.post(
        f"{API}/loans/",
        json={
            "user_id": seeded["umkm"]["id"],
            "loan_amount": 5_000_000,
            "loan_term_months": 6,
            "due_date": "2027-01-01T00:00:00",
        },
        headers=auth_header(seeded["umkm"]["token"]),
    )
    assert r.status_code == 403


def test_list_loans_by_borrower(client, seeded):
    client.post(
        f"{API}/loans/",
        json={
            "user_id": seeded["umkm"]["id"],
            "loan_amount": 5_000_000,
            "loan_term_months": 6,
            "due_date": "2027-01-01T00:00:00",
        },
        headers=auth_header(seeded["lender"]["token"]),
    )
    r = client.get(f"{API}/loans/by-borrower/me", headers=auth_header(seeded["umkm"]["token"]))
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_list_loans_by_lender(client, seeded):
    client.post(
        f"{API}/loans/",
        json={
            "user_id": seeded["umkm"]["id"],
            "loan_amount": 5_000_000,
            "loan_term_months": 6,
            "due_date": "2027-01-01T00:00:00",
        },
        headers=auth_header(seeded["lender"]["token"]),
    )
    r = client.get(f"{API}/loans/by-lender/me", headers=auth_header(seeded["lender"]["token"]))
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_mark_loan_paid(client, seeded):
    created = client.post(
        f"{API}/loans/",
        json={
            "user_id": seeded["umkm"]["id"],
            "loan_amount": 5_000_000,
            "loan_term_months": 6,
            "due_date": "2027-01-01T00:00:00",
        },
        headers=auth_header(seeded["lender"]["token"]),
    )
    loan_id = created.json()["id"]
    r = client.patch(f"{API}/loans/{loan_id}/mark-paid", headers=auth_header(seeded["lender"]["token"]))
    assert r.status_code == 200
    assert r.json()["status"] == "paid"
    assert r.json()["paid_at"] is not None


def test_mark_loan_defaulted(client, seeded):
    created = client.post(
        f"{API}/loans/",
        json={
            "user_id": seeded["umkm"]["id"],
            "loan_amount": 5_000_000,
            "loan_term_months": 6,
            "due_date": "2027-01-01T00:00:00",
        },
        headers=auth_header(seeded["lender"]["token"]),
    )
    loan_id = created.json()["id"]
    r = client.patch(f"{API}/loans/{loan_id}/mark-defaulted", headers=auth_header(seeded["lender"]["token"]))
    assert r.status_code == 200
    assert r.json()["status"] == "defaulted"


def test_list_overdue_loans_requires_admin(client, seeded):
    r = client.get(f"{API}/loans/overdue", headers=auth_header(seeded["lender"]["token"]))
    assert r.status_code == 403


def test_list_overdue_loans_as_admin(client, seeded):
    client.post(
        f"{API}/loans/",
        json={
            "user_id": seeded["umkm"]["id"],
            "loan_amount": 1_000_000,
            "loan_term_months": 1,
            "due_date": "2020-01-01T00:00:00",  # already in the past
        },
        headers=auth_header(seeded["lender"]["token"]),
    )
    r = client.get(f"{API}/loans/overdue", headers=auth_header(seeded["admin"]["token"]))
    assert r.status_code == 200
    assert len(r.json()) == 1


# //====== MATCHES ======//

def test_create_match_as_lender(client, seeded):
    r = client.post(
        f"{API}/matches/",
        json={"umkm_id": seeded["umkm"]["id"], "match_score": 0.87},
        headers=auth_header(seeded["lender"]["token"]),
    )
    assert r.status_code == 201
    assert r.json()["status"] == "pending"


def test_create_match_requires_lender_or_admin(client, seeded):
    r = client.post(
        f"{API}/matches/",
        json={"umkm_id": seeded["umkm"]["id"], "match_score": 0.5},
        headers=auth_header(seeded["umkm"]["token"]),
    )
    assert r.status_code == 403


def test_list_pending_matches_for_lender(client, seeded):
    client.post(
        f"{API}/matches/",
        json={"umkm_id": seeded["umkm"]["id"], "match_score": 0.87},
        headers=auth_header(seeded["lender"]["token"]),
    )
    r = client.get(f"{API}/matches/by-lender/me/pending", headers=auth_header(seeded["lender"]["token"]))
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_list_matches_for_umkm(client, seeded):
    client.post(
        f"{API}/matches/",
        json={"umkm_id": seeded["umkm"]["id"], "match_score": 0.87},
        headers=auth_header(seeded["lender"]["token"]),
    )
    r = client.get(f"{API}/matches/by-umkm/me", headers=auth_header(seeded["umkm"]["token"]))
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_accept_match(client, seeded):
    created = client.post(
        f"{API}/matches/",
        json={"umkm_id": seeded["umkm"]["id"], "match_score": 0.87},
        headers=auth_header(seeded["lender"]["token"]),
    )
    match_id = created.json()["id"]
    r = client.patch(f"{API}/matches/{match_id}/accept", headers=auth_header(seeded["umkm"]["token"]))
    assert r.status_code == 200
    assert r.json()["status"] == "accepted"


def test_reject_match(client, seeded):
    created = client.post(
        f"{API}/matches/",
        json={"umkm_id": seeded["umkm"]["id"], "match_score": 0.4},
        headers=auth_header(seeded["lender"]["token"]),
    )
    match_id = created.json()["id"]
    r = client.patch(f"{API}/matches/{match_id}/reject", headers=auth_header(seeded["umkm"]["token"]))
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"


def test_expire_match_requires_admin(client, seeded):
    created = client.post(
        f"{API}/matches/",
        json={"umkm_id": seeded["umkm"]["id"], "match_score": 0.6},
        headers=auth_header(seeded["lender"]["token"]),
    )
    match_id = created.json()["id"]
    r = client.patch(f"{API}/matches/{match_id}/expire", headers=auth_header(seeded["lender"]["token"]))
    assert r.status_code == 403

    r = client.patch(f"{API}/matches/{match_id}/expire", headers=auth_header(seeded["admin"]["token"]))
    assert r.status_code == 200
    assert r.json()["status"] == "expired"


# //====== AUDIT LOGS ======//

def test_audit_logs_require_admin(client, seeded):
    r = client.get(f"{API}/audit-logs/by-user/{seeded['umkm']['id']}", headers=auth_header(seeded["umkm"]["token"]))
    assert r.status_code == 403


def test_audit_logs_readable_by_admin(client, seeded):
    r = client.get(f"{API}/audit-logs/by-user/{seeded['umkm']['id']}", headers=auth_header(seeded["admin"]["token"]))
    assert r.status_code == 200
    assert r.json() == []  # nothing logged yet in this test, just confirms the route works


def test_audit_logs_by_action_readable_by_admin(client, seeded):
    r = client.get(f"{API}/audit-logs/by-action/LOGIN", headers=auth_header(seeded["admin"]["token"]))
    assert r.status_code == 200