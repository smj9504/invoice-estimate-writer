from utils.db import get_connection

def get_all_items():
    supabase = get_connection()
    res = supabase.table("est_items").select("*").order("category").execute()
    return res.data

def search_items_by_description(keyword: str):
    supabase = get_connection()
    result = (
        supabase.table("est_items")
        .select("*")
        .ilike("description", f"%{keyword}%")
        .execute()
    )
    return result.data or []