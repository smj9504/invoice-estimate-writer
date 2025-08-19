from utils.db import get_connection, with_retries

def get_all_invoice_items():
    supabase = get_connection()
    result = with_retries(lambda: supabase.table("invoice_items").select("*").order("category").execute())
    return result.data or []
