"""Checkpoint for Episode 1. Run from the repo folder:  python checks/ep1_check.py"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GREEN, RED, DIM, END = "\033[32m", "\033[31m", "\033[2m", "\033[0m"

if not (ROOT / "data" / "store.duckdb").exists():
    sys.exit(f"{RED}✗ data/store.duckdb not found.{END} Run: python data/generate_data.py")

spec = importlib.util.spec_from_file_location("ep1", ROOT / "episodes" / "ep1" / "five_answers.py")
ep1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ep1)
con = ep1.connect()

def close(a, b, tol=0.01):
    return a is not None and abs(float(a) - b) <= tol

CHECKS = [
    ("TODO 1 · count_traps", lambda: ep1.count_traps(con),
     lambda r: r == {"test_orders": 102, "canceled_orders": 387, "refunds": 322},
     "Expected {'test_orders': 102, 'canceled_orders': 387, 'refunds': 322}. "
     "Check the dict keys are spelled exactly, and that is_test needs no '= true'."),
    ("TODO 2 · naive_revenue", lambda: ep1.naive_revenue(con), lambda r: close(r, 877454.25),
     "Expected 877,454.25. Query order_items only, with no where clause."),
    ("TODO 3 · net_item_sales", lambda: ep1.net_item_sales(con), lambda r: close(r, 758613.19),
     "Expected 758,613.19. Too high? A filter is missing (test, internal, or canceled). "
     "Too low? Check you subtract discount per line, not twice."),
    ("TODO 4 · refunds_total", lambda: ep1.refunds_total(con), lambda r: close(r, 33210.68),
     "Expected 33,210.68. 33,534.41 means the test/staff filters are missing. "
     "Anything bigger means you joined order_items (fan-out)."),
    ("Given · governed_revenue", lambda: ep1.governed_revenue(con), lambda r: close(r, 725402.51),
     "Expected 725,402.51. This passes automatically once TODO 3 and TODO 4 pass."),
    ("TODO 5 · refunds_via_join", lambda: ep1.refunds_via_join(con), lambda r: close(r, 67901.98),
     "Expected 67,901.98. Join refunds to order_items on order_id, no filters, sum(r.amount)."),
]

passed = 0
for name, run, ok, hint in CHECKS:
    try:
        result = run()
    except NotImplementedError:
        print(f"{DIM}○ {name}: not started yet{END}")
        continue
    except Exception as e:  # show the real error so it can be fixed
        print(f"{RED}✗ {name}: error: {e}{END}")
        continue
    if ok(result):
        passed += 1
        shown = f"{float(result):,.2f}" if not isinstance(result, dict) else result
        print(f"{GREEN}✓ {name}: {shown}{END}")
    else:
        print(f"{RED}✗ {name}: got {result}{END}\n    {hint}")

print(f"\n{passed}/{len(CHECKS)} passed")
if passed == len(CHECKS):
    print(f"{GREEN}Episode 1 complete. Run: python episodes/ep1/five_answers.py{END}")
