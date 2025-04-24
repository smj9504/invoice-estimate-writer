from utils.db import get_connection
from uuid import uuid4
from datetime import datetime

def save_invoice(data: dict) -> bool:
    supabase = get_connection()
    now = datetime.now().isoformat()

    invoice_data = {
        "invoice_uid": str(uuid4()),
        "version": 1,
        "is_latest": True,
        "status": "completed",
        "company_id": data.get("company", {}).get("id"),
        "client_name": data["client"]["name"],
        "client_phone": data["client"]["phone"],
        "client_address": data["client"]["address"],
        "data": data,
        "created_at": now,
        "updated_at": now
    }

    try:
        supabase.table("invoices").insert(invoice_data).execute()
        return True
    except Exception as e:
        print("[Invoice Save Error]", e)
        return False


def get_latest_invoices() -> list[dict]:
    supabase = get_connection()
    result = supabase.table("invoices").select("*").eq("is_latest", True).order("created_at", desc=True).execute()
    return result.data or []
