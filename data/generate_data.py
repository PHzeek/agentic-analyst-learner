"""Generate a small, realistic online-store warehouse in DuckDB.

Synthetic on purpose: no private data, runs offline, and it contains the same
traps real warehouses have (test orders, cancellations, refunds, shipping fees,
discounts) so a naive "revenue" query gets the wrong answer.

Usage:  python data/generate_data.py   -> data/store.duckdb
"""
import random
from datetime import date, timedelta
from pathlib import Path

import duckdb

SEED = 42
random.seed(SEED)
DB = Path(__file__).parent / "store.duckdb"

CHANNELS = [("web", 0.55), ("marketplace", 0.30), ("instagram", 0.15)]
CATEGORIES = {
    "rings": (40, 220), "necklaces": (35, 180), "earrings": (20, 90),
    "bracelets": (25, 120), "care_kits": (10, 30),
}
START, END = date(2026, 1, 1), date(2026, 9, 30)


def pick(weighted):
    r, acc = random.random(), 0.0
    for v, w in weighted:
        acc += w
        if r <= acc:
            return v
    return weighted[-1][0]


def main():
    if DB.exists():
        DB.unlink()
    con = duckdb.connect(str(DB))
    con.execute("""
    create table customers (customer_id int primary key, signup_date date, region varchar, is_internal boolean);
    create table products (product_id int primary key, category varchar, list_price decimal(10,2));
    create table orders (order_id int primary key, customer_id int, order_date date, channel varchar,
                         status varchar,            -- placed | shipped | delivered | canceled
                         shipping_fee decimal(10,2), is_test boolean);
    create table order_items (order_id int, product_id int, quantity int,
                              unit_price decimal(10,2), discount decimal(10,2));
    create table refunds (refund_id int primary key, order_id int, refund_date date, amount decimal(10,2));
    """)

    products, pid = [], 1
    for cat, (lo, hi) in CATEGORIES.items():
        for _ in range(12):
            products.append((pid, cat, round(random.uniform(lo, hi), 2)))
            pid += 1
    con.executemany("insert into products values (?,?,?)", products)

    customers = []
    for cid in range(1, 901):
        signup = START - timedelta(days=random.randint(0, 400)) + timedelta(days=random.randint(0, 270))
        internal = cid <= 6  # staff accounts used for QA
        customers.append((cid, signup, random.choice(["west", "south", "midwest", "northeast"]), internal))
    con.executemany("insert into customers values (?,?,?,?)", customers)

    orders, items, refunds = [], [], []
    oid, rid = 1, 1
    days = (END - START).days + 1
    for d in range(days):
        day = START + timedelta(days=d)
        seasonal = 1.6 if day.month == 2 and day.day <= 14 else 1.0  # Valentine's bump
        for _ in range(int(random.gauss(22, 5) * seasonal)):
            cid = random.randint(1, 900)
            is_test = cid <= 6 or random.random() < 0.01
            status = pick([("delivered", 0.86), ("shipped", 0.05), ("placed", 0.02), ("canceled", 0.07)])
            if day > END - timedelta(days=7) and status == "delivered":
                status = "shipped"
            ship = 0.0 if random.random() < 0.4 else 6.95
            orders.append((oid, cid, day, pick(CHANNELS), status, ship, is_test))
            subtotal = 0.0
            for _ in range(random.choice([1, 1, 1, 2, 2, 3])):
                p = random.choice(products)
                qty = random.choice([1, 1, 1, 2])
                disc = round(p[2] * qty * random.choice([0, 0, 0, 0.1, 0.2]), 2)
                items.append((oid, p[0], qty, p[2], disc))
                subtotal += p[2] * qty - disc
            if status == "delivered" and random.random() < 0.06:
                amt = round(subtotal * random.choice([1.0, 0.5]), 2)
                refunds.append((rid, oid, day + timedelta(days=random.randint(3, 20)), amt))
                rid += 1
            oid += 1
    con.executemany("insert into orders values (?,?,?,?,?,?,?)", orders)
    con.executemany("insert into order_items values (?,?,?,?,?)", items)
    con.executemany("insert into refunds values (?,?,?,?)", refunds)
    n = con.execute("select count(*) from orders").fetchone()[0]
    print(f"Wrote {DB} with {n:,} orders, {len(items):,} items, {len(refunds):,} refunds")


if __name__ == "__main__":
    main()
