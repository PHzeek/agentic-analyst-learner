"""Episode 1 · Data + the problem. YOUR TURN.

Fill in the five TODOs in order. After each one, run:
    python checks/ep1_check.py
and watch one more line turn green.

Tables you'll use (see the lesson page for a diagram):
    orders       order_id, customer_id, order_date, channel, status, shipping_fee, is_test
    order_items  order_id, product_id, quantity, unit_price, discount
    customers    customer_id, signup_date, region, is_internal
    refunds      refund_id, order_id, refund_date, amount
"""
from pathlib import Path

import duckdb

# Boilerplate (given): where the database file lives, relative to this file.
DB = Path(__file__).resolve().parents[2] / "data" / "store.duckdb"


def connect():
    """Boilerplate (given): open the store's database, read-only."""
    return duckdb.connect(str(DB), read_only=True)


def count_traps(con):
    """TODO 1 · Meet the traps.
    Return a dict with three counts:
        {"test_orders": ..., "canceled_orders": ..., "refunds": ...}
    - test_orders: rows in orders where is_test is true
    - canceled_orders: rows in orders whose status is 'canceled'
    - refunds: rows in the refunds table

    Pattern: con.execute("select count(*) from ... where ...").fetchone()[0]
    """
    test = con.execute("select count(*) from orders where is_test").fetchone()[0]
    canceled = con.execute("select count(*) from orders where status = 'canceled'").fetchone()[0]
    refunds = con.execute("select count(*) from refunds ").fetchone()[0]
    # raise NotImplementedError("TODO 1")
    return {"test_orders": test, "canceled_orders": canceled, "refunds": refunds}


def naive_revenue(con):
    """TODO 2 · Query A, the naive answer.
    Return the sum of quantity * unit_price over EVERY row of order_items.
    No joins, no filters. (This is what an AI writes with no rules.)
    """
    return con.execute("select sum(quantity * unit_price) from order_items ").fetchone()[0]
    # raise NotImplementedError("TODO 2")



def net_item_sales(con):
    """TODO 3 · What real customers paid for items.
    Sum (quantity * unit_price - discount) over line items, keeping only:
      - orders that are NOT test orders
      - customers that are NOT internal (staff) accounts
      - orders that are NOT canceled
    You'll need to join orders, order_items and customers.
    """
    return con.execute("select sum(i.quantity * i.unit_price - discount) from orders o join order_items i using (order_id) join customers c using (customer_id) where not o.is_test and not c.is_internal and o.status <> 'canceled' ").fetchone()[0]
    # raise NotImplementedError("TODO 3")


def refunds_total(con):
    """TODO 4 · Refunds on real orders, counted once each.
    Sum refunds.amount, but only for orders that are not test orders
    and customers that are not internal.
    Start FROM refunds (one row per refund) and join outward to orders and customers.
    """
    return con.execute("select sum(r.amount) from refunds r join orders o using (order_id) join customers c using (customer_id) where not o.is_test and not c.is_internal").fetchone()[0]
    # raise NotImplementedError("TODO 4")


def governed_revenue(con):
    """Given: the finance rule = net item sales minus refunds.
    It works as soon as TODO 3 and TODO 4 do."""
    return net_item_sales(con) - refunds_total(con)


def refunds_via_join(con):
    """TODO 5 · Reproduce the fan-out bug on purpose.
    Join refunds to order_items on order_id and return sum(r.amount).
    No filters. Then compare it with a plain `select sum(amount) from refunds`.
    The check script tells you how far apart they are, and the lesson explains why.
    """
    return con.execute("select sum(r.amount) from refunds r join order_items i using (order_id)").fetchone()[0]
    # raise NotImplementedError("TODO 5")


if __name__ == "__main__":
    # Boilerplate (given): print your results once every TODO is done.
    con = connect()
    print("Traps:", count_traps(con))
    truth = governed_revenue(con)
    print(f"A  naive revenue      ${naive_revenue(con):>12,.2f}")
    print(f"   net item sales     ${net_item_sales(con):>12,.2f}")
    print(f" − refunds (once)     ${refunds_total(con):>12,.2f}")
    print(f"✓  governed revenue   ${truth:>12,.2f}")
    print(f"   refunds via join   ${refunds_via_join(con):>12,.2f}   ← fan-out")
