from utils.db import get_connection, with_retries
from uuid import uuid4
from datetime import datetime

def save_invoice(data: dict) -> bool:
    supabase = get_connection()
    now = datetime.now().isoformat()

    client = data.get("client", {})
    full_address = "{} {}, {} {}".format(
        client.get("street", ""),
        client.get("city", ""),
        client.get("state", ""),
        client.get("zip", "")
    ).strip()

    invoice_number = data.get("invoice_number")
    existing = with_retries(lambda: supabase.table("invoices")
        .select("version")
        .eq("invoice_number", invoice_number)
        .order("version", desc=True)
        .limit(1)
        .execute()
    )

    last_version = existing.data[0]["version"] if existing.data else 0
    new_version = last_version + 1

    # 기존 레코드 최신값 해제
    if existing.data:
        with_retries(lambda: supabase.table("invoices")
            .update({"is_latest": False})
            .eq("invoice_number", invoice_number)
            .eq("is_latest", True)
            .execute()
        )

    invoice_data = {
        "invoice_uid": str(uuid4()),
        "version": new_version,
        "is_latest": True,
        "status": "completed",
        "invoice_number": invoice_number,
        "date_of_issue": data.get("date_of_issue"),
        "company_id": data.get("company", {}).get("id"),
        "client_name": client.get("name"),
        "client_phone": client.get("phone"),
        "client_address": full_address,
        "data": data,
        "created_at": now,
        "updated_at": now
    }

    try:
        with_retries(lambda: supabase.table("invoices").insert(invoice_data).execute())
        return True
    except Exception as e:
        print("[Invoice Save Error]", e)
        return False


def get_latest_invoices() -> list[dict]:
    supabase = get_connection()
    result = with_retries(lambda: supabase.table("invoices").select("*").eq("is_latest", True).order("created_at", desc=True).execute())
    return result.data or []


def get_invoice_by_id(invoice_id: str) -> dict:
    supabase = get_connection()
    result = with_retries(lambda: supabase.table("invoices").select("*").eq("id", invoice_id).single().execute())
    return result.data