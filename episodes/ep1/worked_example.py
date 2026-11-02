"""Worked example: sums, filters, and the fan-out trap on a 3-order toy store."""
import duckdb                                   # the database library

con = duckdb.connect()                          # no file name = a throwaway in-memory database

con.execute("create table orders (order_id int, status varchar, is_test boolean)")
con.execute("insert into orders values (1,'delivered',false), (2,'canceled',false), (3,'delivered',true)")

con.execute("create table items (order_id int, price decimal(10,2))")
con.execute("insert into items values (1,100), (1,50), (2,80), (3,30)")   # order 1 has TWO items

con.execute("create table refunds (order_id int, amount decimal(10,2))")
con.execute("insert into refunds values (1,20)")                          # one $20 refund on order 1

# 1) Naive: add up every item price. Counts the canceled order and the test order.
print("naive  ", con.execute("select sum(price) from items").fetchone()[0])

# 2) Filtered: join items to their order, keep only real, non-canceled orders.
print("real   ", con.execute("""
    select sum(i.price) from items i join orders o using (order_id)
    where o.status <> 'canceled' and not o.is_test""").fetchone()[0])

# 3) Refunds at their own grain: one row per refund, counted once.
print("refunds", con.execute("select sum(amount) from refunds").fetchone()[0])

# 4) Fan-out: join refunds to items first. Order 1 has 2 items, so the $20 appears twice.
print("fan-out", con.execute("select sum(r.amount) from refunds r join items i using (order_id)").fetchone()[0])
