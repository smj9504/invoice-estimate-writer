from utils.db import get_connection, with_retries

def get_all_items():
    supabase = get_connection()
    res = with_retries(lambda: supabase.table("est_items").select("*").order("category").execute())
    return res.data or []

def search_items_by_description(keyword: str):
    supabase = get_connection()
    result = with_retries(lambda: (
        supabase.table("est_items")
        .select("*")
        .ilike("description", f"%{keyword}%")
        .execute()
    ))
    return result.data or []
