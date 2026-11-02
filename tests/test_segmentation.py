import pandas as pd
import pytest

from helpers import build_orders
from nexmargin import segmentation as S


def test_assign_segment_rules():
    assert S.assign_segment(5, 5) == "Champions" and S.assign_segment(4, 4) == "Champions"
    assert S.assign_segment(3, 3) == "Loyal Customers" and S.assign_segment(4, 3) == "Loyal Customers"
    assert S.assign_segment(4, 2) == "Potential Loyalists" and S.assign_segment(3, 2.5) == "Potential Loyalists"
    assert S.assign_segment(2, 4) == "At Risk" and S.assign_segment(1, 3) == "At Risk"
    assert S.assign_segment(1, 1) == "Lost Customers" and S.assign_segment(2, 2.5) == "Lost Customers"


def test_every_input_maps_to_exactly_one_known_segment():
    for r in range(1, 6):
        for fm in [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5]:
            assert S.assign_segment(r, fm) in S.SEGMENTS


def _customers():
    rows = []
    for i, (n_orders, last, sales) in enumerate([(8, "12/20/2017", 900), (5, "12/1/2017", 500), (3, "6/1/2017", 300),
                                                  (2, "2/1/2016", 400), (1, "1/5/2015", 20)]):
        for k in range(n_orders):
            rows.append({"Order ID": f"C{i}-{k}", "Order Date": last if k == n_orders - 1 else "1/5/2015", "Customer ID": f"CU{i}",
                         "Customer Name": f"N{i}", "Sales": sales / n_orders, "Profit": 1.0})
    return build_orders(rows)


def test_rfm_table_values_and_scores():
    df = _customers()
    t = S.rfm_table(df, as_of="2017-12-31").set_index("customer_id")
    assert t.loc["CU0", "recency_days"] == 11 and t.loc["CU0", "frequency"] == 8 and t.loc["CU0", "monetary"] == pytest.approx(900)
    assert t["r_score"].between(1, 5).all() and t["f_score"].between(1, 5).all() and t["m_score"].between(1, 5).all()
    assert t.loc["CU0", "r_score"] > t.loc["CU4", "r_score"]          # more recent = higher score
    assert t.loc["CU0", "segment"] == "Champions" and t.loc["CU4", "segment"] == "Lost Customers"
    assert len(t) == 5 and set(t["segment"]) <= set(S.SEGMENTS)


def test_rfm_is_deterministic_and_ties_share_scores():
    df = _customers()
    a, b = S.rfm_table(df), S.rfm_table(df.sample(frac=1, random_state=1))
    pd.testing.assert_frame_equal(a.sort_values("customer_id").reset_index(drop=True), b.sort_values("customer_id").reset_index(drop=True))
    same = build_orders([{"Order ID": f"X{i}", "Customer ID": f"K{i}", "Customer Name": "n"} for i in range(4)])
    assert S.rfm_table(same)["f_score"].nunique() == 1


def test_rfm_edge_cases():
    assert S.rfm_table(_customers().iloc[0:0]).empty
    one = S.rfm_table(build_orders([{}]))
    assert len(one) == 1 and one.loc[0, "segment"] in S.SEGMENTS
    assert S.segment_summary(S.rfm_table(_customers()))["customers"].sum() == 5
    assert S.segment_summary(pd.DataFrame(columns=S.COLUMNS)).empty
