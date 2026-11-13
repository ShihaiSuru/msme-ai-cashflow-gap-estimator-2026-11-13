#!/usr/bin/env python3
"""
MSME Cash-Flow Gap Estimator
Simple, explainable starter that estimates short-term cash gaps for Indian MSMEs.
Factors delayed receivables and GST payment obligations that arise on invoice.
"""

from datetime import datetime, timedelta
from typing import List, Dict


def estimate_cashflow_gap(
    invoices: List[Dict],
    avg_collection_delay_days: int = 45,
    horizon_days: int = 30,
    opening_cash: float = 0.0,
) -> Dict:
    """
    Estimate cash-flow gap over a horizon.

    Each invoice dict expects:
      - amount: total invoice value (INR)
      - gst_rate: GST rate as decimal (e.g. 0.18)
      - invoice_date: datetime
      - expected_payment_days: contractual credit period

    GST liability is assumed payable roughly 1 month after the invoice month
    (simplified; real GSTR-3B timing can be plugged in later).
    """
    today = datetime.now().date()
    horizon_end = today + timedelta(days=horizon_days)

    projected_inflows = 0.0
    gst_outflows = 0.0
    details = []

    for inv in invoices:
        inv_date = inv["invoice_date"].date()
        taxable = inv["amount"] / (1 + inv["gst_rate"])
        gst = inv["amount"] - taxable

        # Expected collection date after delay
        collection_date = inv_date + timedelta(
            days=inv.get("expected_payment_days", 30) + avg_collection_delay_days
        )

        # Simplified GST due date: ~30 days after invoice month end
        gst_due = (inv_date.replace(day=1) + timedelta(days=32)).replace(day=1) + timedelta(days=20)

        if today <= collection_date <= horizon_end:
            projected_inflows += inv["amount"]
            details.append(
                {
                    "type": "inflow",
                    "date": collection_date.isoformat(),
                    "amount": inv["amount"],
                    "note": f"Invoice of {inv['amount']:,.0f} expected",
                }
            )

        if today <= gst_due <= horizon_end:
            gst_outflows += gst
            details.append(
                {
                    "type": "gst_outflow",
                    "date": gst_due.isoformat(),
                    "amount": gst,
                    "note": f"GST liability on invoice of {inv['amount']:,.0f}",
                }
            )

    net_gap = opening_cash + projected_inflows - gst_outflows
    status = "surplus" if net_gap >= 0 else "gap"

    return {
        "horizon_days": horizon_days,
        "opening_cash": opening_cash,
        "projected_inflows": projected_inflows,
        "gst_outflows": gst_outflows,
        "net_position": net_gap,
        "status": status,
        "details": details,
    }


def print_report(result: Dict):
    print("=" * 60)
    print("MSME CASH-FLOW GAP ESTIMATE")
    print("=" * 60)
    print(f"Horizon:           {result['horizon_days']} days")
    print(f"Opening cash:      ₹{result['opening_cash']:,.0f}")
    print(f"Projected inflows: ₹{result['projected_inflows']:,.0f}")
    print(f"GST outflows:      ₹{result['gst_outflows']:,.0f}")
    print("-" * 60)
    print(f"Net position:      ₹{result['net_position']:,.0f} ({result['status'].upper()})")
    print("\nDetails:")
    for d in result["details"]:
        sign = "+" if d["type"] == "inflow" else "-"
        print(f"  {d['date']}  {sign}₹{d['amount']:,.0f}  {d['note']}")
    print("=" * 60)


if __name__ == "__main__":
    # Sample realistic MSME invoices (amounts in INR)
    sample_invoices = [
        {
            "amount": 250000,
            "gst_rate": 0.18,
            "invoice_date": datetime(2026, 10, 15),
            "expected_payment_days": 45,
        },
        {
            "amount": 180000,
            "gst_rate": 0.12,
            "invoice_date": datetime(2026, 10, 28),
            "expected_payment_days": 30,
        },
        {
            "amount": 420000,
            "gst_rate": 0.18,
            "invoice_date": datetime(2026, 11, 5),
            "expected_payment_days": 60,
        },
        {
            "amount": 95000,
            "gst_rate": 0.05,
            "invoice_date": datetime(2026, 11, 10),
            "expected_payment_days": 30,
        },
    ]

    result = estimate_cashflow_gap(
        invoices=sample_invoices,
        avg_collection_delay_days=40,
        horizon_days=45,
        opening_cash=75000,
    )
    print_report(result)

    if result["status"] == "gap":
        print("\nRecommendation: Consider invoice discounting / TReDS for upcoming large receivables")
        print("or short-term working-capital line to cover GST timing mismatch.")
