from utils.db import get_connection

# 1. 모든 견적 항목 불러오기
def get_all_items():
    supabase = get_connection()
    if not supabase:
        return []
    result = supabase.table("est_items").select("*").order("category").execute()
    return result.data or []

# 2. 항목 ID로 단일 아이템 조회
def get_item_by_id(item_id: str):
    supabase = get_connection()
    if not supabase:
        return None
    result = supabase.table("est_items").select("*").eq("id", item_id).execute()
    return result.data[0] if result.data else None

# 3. 아이템 저장
def insert_item(data: dict):
    supabase = get_connection()
    return supabase.table("est_items").insert(data).execute()

# 4. 아이템 수정
def update_item(item_id: str, data: dict):
    supabase = get_connection()
    return supabase.table("est_items").update(data).eq("id", item_id).execute()

# 5. 아이템 삭제
def delete_item(item_id: str):
    supabase = get_connection()
    return supabase.table("est_items").delete().eq("id", item_id).execute()

# ======================
# 설명 관련 기능
# ======================

# 6. 설명 목록 불러오기
def get_descriptions_by_item_name(item_name: str):
    supabase = get_connection()
    result = supabase.table("est_item_desc")\
        .select("*")\
        .eq("item_name", item_name)\
        .order("sort_order")\
        .execute()
    return result.data or []

# 7. 설명 저장
def insert_description(data: dict):
    supabase = get_connection()
    return supabase.table("est_item_desc").insert(data).execute()

# 8. 설명 삭제
def delete_description(desc_id: str):
    supabase = get_connection()
    return supabase.table("est_item_desc").delete().eq("id", desc_id).execute()
