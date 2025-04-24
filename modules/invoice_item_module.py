from utils.db import get_connection

def get_all_invoice_items():
    supabase = get_connection()
    result = supabase.table("invoice_items").select("*").order("category").execute()
    return result.data or []