"""
Direct PostgreSQL Data Seeder for Qredi ACS Pipeline.
Generates UMKMs, a Lender, an Admin, and tens of thousands of QRIS transactions
and loan outcomes, then batch inserts them directly into the database.
Outputs 'generated_credentials.json' for testing logins.
"""

import uuid
import random
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from pwdlib import PasswordHash

# --- Configuration ---
DATABASE_URL = "postgresql+psycopg://lilianne:CQkgG8BltX59zTLR4K8V2ljTJKKdWRS7UHk7HuJz5WwvL@localhost:5432/qredi_db_seedertest"
CREDENTIALS_OUTPUT_FILE = "generated_credentials.json"

random.seed(42)
END_DATE = datetime(2026, 7, 15)

# --- Password Hashing Setup (Matches your app.core.security) ---
password_hash = PasswordHash.recommended()

def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using Argon2id via pwdlib."""
    return password_hash.hash(plain_password)

# --- Reference Data ---
CITIES = ["Jakarta", "Bandung", "Surabaya", "Yogyakarta", "Semarang",
          "Medan", "Makassar", "Denpasar", "Malang", "Solo"]

CATEGORY_NAMES = {
    "food_beverage": ["Warung Bu Sari", "Nasi Goreng Pak Joko", "Angkringan Malam", "Kedai Kopi Senja", "Bakso Mang Ujang", "Soto Ayam Mbok Darmi", "Es Teh Segar Bang Yudi", "Gorengan Ceria"],
    "retail": ["Toko Sembako Makmur", "Mini Market Berkah", "Toko Kelontong Ibu Ani", "Toko Bangunan Jaya"],
    "services": ["Laundry Kilat", "Bengkel Motor Pak De", "Salon Cantika Sejahtera", "Servis HP Cepat Jaya"],
    "groceries": ["Pasar Segar Ibu Wati", "Sayur Bu Tini", "Buah Segar Jaya"],
    "fashion": ["Butik Melati", "Distro Anak Muda", "Toko Baju Rapi"],
    "electronics": ["Toko Elektronik Sinar", "Aksesoris HP Cell Point", "Toko Kabel & Charger"],
}

CATEGORY_HOUR_WEIGHTS = {
    "food_beverage": {7: 2, 8: 2, 11: 3, 12: 4, 13: 3, 18: 4, 19: 4, 20: 3},
    "retail": {9: 2, 10: 3, 11: 3, 14: 3, 15: 3, 16: 3, 17: 2},
    "services": {9: 2, 10: 3, 13: 2, 14: 3, 15: 3, 16: 2},
    "groceries": {6: 3, 7: 4, 8: 3, 9: 2, 16: 2, 17: 2},
    "fashion": {11: 2, 13: 2, 15: 3, 16: 3, 19: 3, 20: 2},
    "electronics": {11: 2, 14: 3, 15: 3, 16: 2, 19: 2},
}

CATEGORY_WEEKEND_BOOST = {
    "food_beverage": 1.6, "fashion": 1.5, "electronics": 1.2,
    "retail": 1.1, "groceries": 0.9, "services": 0.8,
}

AMOUNT_RANGES = {
    "food_beverage": (8_000, 75_000),
    "retail": (10_000, 250_000),
    "services": (15_000, 150_000),
    "groceries": (5_000, 100_000),
    "fashion": (30_000, 350_000),
    "electronics": (25_000, 900_000),
}
ALL_CATEGORIES = list(CATEGORY_NAMES.keys())

# --- Business Archetypes ---
BUSINESSES = [
    dict(key="cold_healthy_stable", category="food_beverage", months=6, trend="growing", avg_daily_tx=14, volatility=0.15, repeat_rate=0.55, refund_rate=0.02, category_noise=0.0, zero_week_prob=0.0, loans=[]),
    dict(key="cold_healthy_new", category="services", months=2, trend="flat", avg_daily_tx=6, volatility=0.15, repeat_rate=0.45, refund_rate=0.02, category_noise=0.0, zero_week_prob=0.0, loans=[]),
    dict(key="cold_struggling", category="retail", months=5, trend="declining", avg_daily_tx=7, volatility=0.35, repeat_rate=0.10, refund_rate=0.03, category_noise=0.0, zero_week_prob=0.22, loans=[]),
    dict(key="cold_borderline_mixed", category="fashion", months=7, trend="volatile", avg_daily_tx=9, volatility=0.55, repeat_rate=0.30, refund_rate=0.08, category_noise=0.18, zero_week_prob=0.06, loans=[]),
    dict(key="repay_good_1", category="groceries", months=8, trend="growing", avg_daily_tx=16, volatility=0.15, repeat_rate=0.50, refund_rate=0.02, category_noise=0.0, zero_week_prob=0.0, loans=[dict(status="PAID", dpd=0, months_ago_due=5, term=3, amount=3_000_000), dict(status="PAID", dpd=0, months_ago_due=1, term=2, amount=4_500_000)]),
    dict(key="repay_good_2", category="electronics", months=6, trend="flat", avg_daily_tx=5, volatility=0.20, repeat_rate=0.35, refund_rate=0.03, category_noise=0.0, zero_week_prob=0.0, loans=[dict(status="PAID", dpd=0, months_ago_due=2, term=3, amount=6_000_000)]),
    dict(key="repay_bad_1", category="food_beverage", months=7, trend="declining_before_due", avg_daily_tx=12, volatility=0.30, repeat_rate=0.25, refund_rate=0.04, category_noise=0.0, zero_week_prob=0.10, loans=[dict(status="DEFAULTED", dpd=75, months_ago_due=1, term=3, amount=3_500_000)]),
    dict(key="repay_bad_2", category="retail", months=6, trend="declining_before_due", avg_daily_tx=8, volatility=0.45, repeat_rate=0.15, refund_rate=0.05, category_noise=0.05, zero_week_prob=0.15, loans=[dict(status="OVERDUE", dpd=42, months_ago_due=1, term=2, amount=2_800_000)]),
    dict(key="repay_mid_1", category="services", months=7, trend="volatile", avg_daily_tx=7, volatility=0.40, repeat_rate=0.30, refund_rate=0.03, category_noise=0.05, zero_week_prob=0.04, loans=[dict(status="PAID", dpd=7, months_ago_due=2, term=3, amount=2_200_000)]),
    dict(key="repay_mid_2", category="fashion", months=8, trend="volatile", avg_daily_tx=8, volatility=0.35, repeat_rate=0.28, refund_rate=0.06, category_noise=0.10, zero_week_prob=0.05, loans=[dict(status="PAID", dpd=12, months_ago_due=3, term=4, amount=5_000_000)]),
    dict(key="repay_active_1", category="food_beverage", months=9, trend="growing", avg_daily_tx=13, volatility=0.20, repeat_rate=0.45, refund_rate=0.02, category_noise=0.0, zero_week_prob=0.0, loans=[dict(status="PAID", dpd=0, months_ago_due=6, term=3, amount=3_000_000), dict(status="ACTIVE", dpd=0, months_ago_due=-2, term=3, amount=5_500_000)]),
    dict(key="repay_active_2", category="groceries", months=9, trend="flat", avg_daily_tx=10, volatility=0.25, repeat_rate=0.35, refund_rate=0.03, category_noise=0.0, zero_week_prob=0.02, loans=[dict(status="PAID", dpd=9, months_ago_due=5, term=2, amount=2_500_000), dict(status="ACTIVE", dpd=0, months_ago_due=-1, term=3, amount=4_000_000)]),
]

KNOWN_USER_ID_HINT = {"cold_healthy_stable": "a74ac173-6343-4a9d-9c76-62e56379cfe0"}

# --- Helpers ---
def month_multipliers(n_months, trend, volatility, zero_week_prob):
    if trend == "flat": base = [1.0] * n_months
    elif trend == "growing": base = [0.55 + (0.9 * i / max(n_months - 1, 1)) for i in range(n_months)]
    elif trend == "declining": base = [1.25 - (0.85 * i / max(n_months - 1, 1)) for i in range(n_months)]
    elif trend == "declining_before_due":
        base = [1.0] * n_months
        for i in range(max(n_months - 2, 0), n_months): base[i] *= 0.45
    elif trend == "volatile": base = [random.uniform(0.5, 1.6) for _ in range(n_months)]
    elif trend == "sporadic": base = [random.uniform(0.3, 1.1) for _ in range(n_months)]
    else: base = [1.0] * n_months

    for i in range(n_months):
        if random.random() < zero_week_prob: base[i] *= random.uniform(0.0, 0.25)
    return [max(0.05, m * random.gauss(1.0, volatility)) for m in base]

def gen_amount(category):
    lo, hi = AMOUNT_RANGES[category]
    r = random.random() ** 1.8
    return round(lo + r * (hi - lo), -2)

def gen_hour(category):
    weights = CATEGORY_HOUR_WEIGHTS.get(category, {})
    hours = list(range(7, 22))
    return random.choices(hours, weights=[weights.get(h, 1) for h in hours], k=1)[0]


# --- Core Logic ---
def main():
    engine = create_engine(DATABASE_URL)
    
    users_data, profiles_data = [], []
    transactions_data, loans_data = [], []
    credentials_output = []
    
    # 1. Create shared Admin & Lender
    admin_id = str(uuid.uuid4())
    lender_id = str(uuid.uuid4())
    
    admin_pass = "AdminPass123!"
    lender_pass = "Lender12345!"
    umkm_pass = "Umkm12345!"

    print("Hashing passwords using Argon2id (this may take a few seconds)...")
    hashed_admin_pass = hash_password(admin_pass)
    hashed_lender_pass = hash_password(lender_pass)
    hashed_umkm_pass = hash_password(umkm_pass)

    users_data.extend([
        {"id": admin_id, "email": "admin@qredi.test", "hashed_password": hashed_admin_pass, "full_name": "Qredi Admin", "phone_number": "081200000000", "role": "ADMIN"},
        {"id": lender_id, "email": "lender@qredi.test", "hashed_password": hashed_lender_pass, "full_name": "Bank Partner", "phone_number": "081200000001", "role": "LENDER"}
    ])

    credentials_output.extend([
        {"role": "ADMIN", "full_name": "Qredi Admin", "email": "admin@qredi.test", "password": admin_pass},
        {"role": "LENDER", "full_name": "Bank Partner", "email": "lender@qredi.test", "password": lender_pass}
    ])

    # 2. Generate UMKM businesses, transactions, and loans
    for i, biz in enumerate(BUSINESSES, start=1):
        user_id = KNOWN_USER_ID_HINT.get(biz["key"], str(uuid.uuid4()))
        email = f"umkm{i:02d}.{biz['key']}@qredi.test"
        full_name = f"UMKM {i:02d} - {biz['key'].replace('_', ' ').title()}"
        
        users_data.append({
            "id": user_id, "email": email, "hashed_password": hashed_umkm_pass, 
            "full_name": full_name, "phone_number": f"0812{i:08d}", "role": "UMKM"
        })
        
        credentials_output.append({
            "role": "UMKM", "full_name": full_name, "email": email, "password": umkm_pass, "business_key": biz["key"]
        })
        
        profiles_data.append({
            "id": str(uuid.uuid4()), "user_id": user_id,
            "business_name": random.choice(CATEGORY_NAMES[biz["category"]]),
            "business_type": biz["category"], "city": random.choice(CITIES)
        })

        # --- Generate Transactions ---
        n_months = biz["months"]
        start_date = END_DATE - timedelta(days=30 * n_months)
        multipliers = month_multipliers(n_months, biz["trend"], biz["volatility"], biz["zero_week_prob"])
        customer_pool = [str(uuid.uuid4())[:16] for _ in range(40)]
        weekend_boost = CATEGORY_WEEKEND_BOOST.get(biz["category"], 1.0)
        
        day = start_date
        while day < END_DATE:
            months_elapsed = min((day - start_date).days // 30, n_months - 1)
            expected_count = biz["avg_daily_tx"] * multipliers[months_elapsed] * (weekend_boost if day.weekday() >= 5 else 1.0)
            n_tx = max(0, int(random.gauss(expected_count, expected_count * 0.35 + 0.3)))

            for _ in range(n_tx):
                tx_category = biz["category"]
                if biz["category_noise"] > 0 and random.random() < biz["category_noise"]:
                    tx_category = random.choice([c for c in ALL_CATEGORIES if c != biz["category"]])
                
                ttype = "payment"
                roll = random.random()
                if roll < biz["refund_rate"]: ttype = "refund"
                elif roll < biz["refund_rate"] + 0.02: ttype = "transfer"
                elif roll < biz["refund_rate"] + 0.04: ttype = "top_up"
                
                is_refund = (ttype == "refund") or (ttype == "payment" and random.random() < 0.01)

                transactions_data.append({
                    "id": str(uuid.uuid4()), "user_id": user_id,
                    "amount": gen_amount(tx_category), 
                    "transaction_type": ttype.upper(),
                    # 🟢 Removed payment_method here
                    "merchant_name": random.choice(CATEGORY_NAMES[tx_category]),
                    "merchant_category": tx_category,
                    "customer_hash": random.choice(customer_pool) if random.random() < biz["repeat_rate"] else str(uuid.uuid4())[:16],
                    "qris_reference": f"QRIS-{uuid.uuid4().hex[:12].upper()}",
                    "transaction_time": day.replace(hour=gen_hour(tx_category), minute=random.randint(0, 59), second=random.randint(0, 59)),
                    "city": random.choice(CITIES), "is_refund": is_refund,
                    "fraud_flag": random.random() < random.uniform(0.002, 0.015)
                })
            day += timedelta(days=1)

        # --- Generate Loans ---
        for spec in biz["loans"]:
            due_date = END_DATE - timedelta(days=30 * spec["months_ago_due"])
            paid_at = (due_date + timedelta(days=spec["dpd"])) if spec["status"] == "PAID" else None
            
            loans_data.append({
                "id": str(uuid.uuid4()), "user_id": user_id, "lender_id": lender_id,
                "loan_amount": spec["amount"], "loan_term_months": spec["term"],
                "due_date": due_date, "paid_at": paid_at,
                "days_past_due": spec["dpd"] if spec["status"] != "ACTIVE" else 0,
                "status": spec["status"] 
            })

    # 3. Database Execution
    print(f"Connecting to database...")
    print(f"Generated {len(users_data)} users, {len(transactions_data)} transactions, {len(loans_data)} loans.")
    
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO users (id, email, hashed_password, full_name, phone_number, role, email_verified, is_active)
            VALUES (cast(:id as uuid), :email, :hashed_password, :full_name, :phone_number, cast(:role as user_role), true, true)
            ON CONFLICT (email) DO NOTHING
        """), users_data)
        
        conn.execute(text("""
            INSERT INTO umkm_profiles (id, user_id, business_name, business_type, city)
            VALUES (cast(:id as uuid), cast(:user_id as uuid), :business_name, :business_type, :city)
            ON CONFLICT (user_id) DO NOTHING
        """), profiles_data)

        chunk_size = 5000
        print(f"Inserting transactions...")
        
        # 🟢 Removed payment_method from INSERT columns and VALUES below
        tx_query = text("""
            INSERT INTO qris_transactions (
                id, user_id, amount, transaction_type, 
                merchant_name, merchant_category, customer_hash, 
                qris_reference, transaction_time, city, is_refund, fraud_flag
            )
            VALUES (
                cast(:id as uuid), cast(:user_id as uuid), :amount, 
                cast(:transaction_type as transaction_type), 
                :merchant_name, :merchant_category, :customer_hash, 
                :qris_reference, :transaction_time, :city, :is_refund, :fraud_flag
            )
        """)
        for i in range(0, len(transactions_data), chunk_size):
            conn.execute(tx_query, transactions_data[i:i+chunk_size])

        if loans_data:
            print(f"Inserting loans...")
            conn.execute(text("""
                INSERT INTO loan_outcomes (
                    id, user_id, lender_id, loan_amount, loan_term_months, 
                    due_date, paid_at, days_past_due, status
                )
                VALUES (
                    cast(:id as uuid), cast(:user_id as uuid), cast(:lender_id as uuid), 
                    :loan_amount, :loan_term_months, :due_date, :paid_at, 
                    :days_past_due, cast(:status as loan_status)
                )
            """), loans_data)

    # 4. Save Credentials to JSON
    with open(CREDENTIALS_OUTPUT_FILE, "w") as f:
        json.dump(credentials_output, f, indent=4)

    print("✅ Seed complete! All generated data is in the database.")
    print(f"✅ Credentials saved to '{CREDENTIALS_OUTPUT_FILE}'.")

if __name__ == "__main__":
    main()
