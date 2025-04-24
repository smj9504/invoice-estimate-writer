from utils.db import get_connection

def get_all_companies():
    """모든 회사 정보 가져오기"""
    supabase = get_connection()
    if not supabase:
        return []
    response = supabase.table("companies").select("*").order("name").execute()
    return response.data or []

def get_company_by_id(company_id: str):
    """회사 ID로 조회"""
    supabase = get_connection()
    if not supabase:
        return None

    response = supabase.table("companies").select("*").eq("id", company_id.strip()).execute()
    return response.data[0] if response.data else None

def insert_company(data: dict):
    """새 회사 등록"""
    supabase = get_connection()
    if not supabase:
        return None

    return supabase.table("companies").insert(data).execute()

def update_company(company_id: str, data: dict):
    """회사 정보 수정"""
    supabase = get_connection()
    if not supabase:
        return None

    return supabase.table("companies").update(data).eq("id", company_id).execute()

def delete_company(company_id: str):
    """회사 삭제"""
    supabase = get_connection()
    if not supabase:
        return None

    return supabase.table("companies").delete().eq("id", company_id).execute()
