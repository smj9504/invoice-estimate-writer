from utils.db import get_connection, with_retries
from uuid import uuid4
from datetime import datetime

def save_estimate(data: dict) -> bool:
    supabase = get_connection()
    now = datetime.now().isoformat()

    company_id = data.get("company", {}).get("id")
    estimate_number = data.get("estimate_number")

    # 최신 버전 조회 (with_retries 적용)
    existing = with_retries(lambda:
        supabase.table("estimates")
        .select("version")
        .eq("company_id", company_id)
        .eq("estimate_number", estimate_number)
        .order("version", desc=True)
        .limit(1)
        .execute()
    )
    if existing is None:
        print("[ERROR] DB 응답이 None입니다.")
        return False

    existing_version = existing.data[0]["version"] if existing.data else 0
    new_version = existing_version + 1

    # 기존 항목 is_latest = False로 업데이트
    if existing_version > 0:
        with_retries(lambda:
            supabase.table("estimates")
            .update({"is_latest": False, "updated_at": now})
            .eq("company_id", company_id)
            .eq("estimate_number", estimate_number)
            .eq("is_latest", True)
            .execute()
        )

    full_address = "{} {}, {} {}".format(
        data["client"].get("address", ""),
        data["client"].get("city", ""),
        data["client"].get("state", ""),
        data["client"].get("zip", "")
    ).strip()

    estimate_data = {
        "estimate_uid": str(uuid4()),
        "version": new_version,
        "is_latest": True,
        "status": "draft",
        "estimate_number": estimate_number,
        "estimate_date": data.get("estimate_date"),
        "company_id": company_id,
        "client_name": data["client"].get("name"),
        "client_phone": data["client"].get("phone"),
        "client_email": data["client"].get("email"),
        "client_address": full_address,
        "json_data": data,
        "created_at": now,
        "updated_at": now,
    }

    try:
        with_retries(lambda:
            supabase.table("estimates")
            .insert(estimate_data)
            .execute()
        )
        return True
    except Exception as e:
        print("[ERROR] 견적서 저장 실패:", e)
        return False
    
    
def get_latest_estimates() -> list[dict]:
    supabase = get_connection()
    result = with_retries(
        lambda: supabase.table("estimates")
        .select("*")
        .eq("is_latest", True)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []


def get_estimate_by_id(estimate_uid: str) -> dict | None:
    supabase = get_connection()
    try:
        result = with_retries(
            lambda: supabase.table("estimates")
            .select("*")
            .eq("estimate_uid", estimate_uid)
            .eq("is_latest", True)
            .single()
            .execute()
        )
        return result.data if result and hasattr(result, "data") else None
    except Exception as e:
        print("[get_estimate_by_id ERROR]", e)
        return None


# ======================
# 견적 항목 관리
# ======================

# 1. 모든 견적 항목 불러오기
def get_all_items():
    supabase = get_connection()
    if not supabase:
        return []
    result = with_retries(lambda: supabase.table("est_items").select("*").order("category").execute())
    return result.data or []

# 2. 항목 ID로 단일 아이템 조회
def get_item_by_id(item_id: str):
    supabase = get_connection()
    if not supabase:
        return None
    result = with_retries(lambda: supabase.table("est_items").select("*").eq("id", item_id).execute())
    return result.data[0] if result and result.data else None

# 3. 아이템 저장
def insert_item(data: dict):
    supabase = get_connection()
    return with_retries(lambda: supabase.table("est_items").insert(data).execute())

# 4. 아이템 수정
def update_item(item_id: str, data: dict):
    supabase = get_connection()
    return with_retries(lambda: supabase.table("est_items").update(data).eq("id", item_id).execute())

# 5. 아이템 삭제
def delete_item(item_id: str):
    supabase = get_connection()
    # 먼저 관련된 descriptions 삭제
    with_retries(lambda: supabase.table("est_item_descriptions").delete().eq("item_id", item_id).execute())
    # 그 다음 item 삭제
    return with_retries(lambda: supabase.table("est_items").delete().eq("id", item_id).execute())

def get_item_by_code(code: str):
    supabase = get_connection()
    if not supabase:
        return None

    try:
        result = supabase.table("est_items").select("*").eq("code", code).maybe_single().execute()
        return result.data if result and hasattr(result, "data") else None
    except Exception as e:
        print("[get_item_by_code ERROR]", e)
        return None


# ======================
# 설명 관련 기능
# ======================

# 6. 설명 목록 불러오기 (item_id 기준)
def get_descriptions_by_item_id(item_id: str):
    try:
        supabase = get_connection()
        result = with_retries(lambda: supabase.table("est_item_descriptions")
            .select("*")
            .eq("item_id", item_id)
            .order("sort_order")
            .execute())
        
        if result is None:
            return []
        
        return getattr(result, 'data', []) or []
        
    except Exception as e:
        print(f"Error in get_descriptions_by_item_id: {e}")
        return []

# 7. 설명 목록 불러오기 (item_name 기준) - 하위 호환성을 위해 유지
def get_descriptions_by_item_name(item_name: str):
    try:
        supabase = get_connection()
        # item_name으로 item_id를 먼저 찾아야 함
        item_result = with_retries(lambda: supabase.table("est_items")
            .select("id")
            .eq("name", item_name)
            .execute())
        
        if not item_result or not item_result.data:
            return []
        
        item_id = item_result.data[0]["id"]
        return get_descriptions_by_item_id(item_id)
        
    except Exception as e:
        print(f"Error in get_descriptions_by_item_name: {e}")
        return []

# 8. 설명 저장
def insert_description(data: dict):
    supabase = get_connection()
    return with_retries(lambda: supabase.table("est_item_descriptions").insert(data).execute())

# 9. 설명 수정
def update_description(desc_id: str, data: dict):
    supabase = get_connection()
    data["updated_at"] = datetime.now().isoformat()
    return with_retries(lambda: supabase.table("est_item_descriptions").update(data).eq("id", desc_id).execute())

# 10. 설명 삭제
def delete_description(desc_id: str):
    supabase = get_connection()
    return with_retries(lambda: supabase.table("est_item_descriptions").delete().eq("id", desc_id).execute())

# 11. 여러 설명 한번에 저장
def insert_multiple_descriptions(item_id: str, descriptions: list):
    """
    여러 설명을 한번에 저장
    descriptions: [{"description": str, "tag": str, "sort_order": int}, ...]
    """
    try:
        supabase = get_connection()
        now = datetime.now().isoformat()
        
        desc_data = []
        for desc in descriptions:
            desc_data.append({
                "item_id": item_id,
                "description": desc.get("description", ""),
                "tag": desc.get("tag", ""),
                "sort_order": desc.get("sort_order", 1),
                "created_at": now,
                "updated_at": now
            })
        
        if desc_data:
            return with_retries(lambda: supabase.table("est_item_descriptions").insert(desc_data).execute())
        return None
        
    except Exception as e:
        print(f"Error in insert_multiple_descriptions: {e}")
        return None

# 12. 항목의 모든 설명 삭제 후 새로 저장
def replace_item_descriptions(item_id: str, descriptions: list):
    """
    기존 설명들을 모두 삭제하고 새 설명들로 교체
    """
    try:
        supabase = get_connection()
        
        # 기존 설명들 삭제
        with_retries(lambda: supabase.table("est_item_descriptions").delete().eq("item_id", item_id).execute())
        
        # 새 설명들 저장
        if descriptions:
            return insert_multiple_descriptions(item_id, descriptions)
        return None
        
    except Exception as e:
        print(f"Error in replace_item_descriptions: {e}")
        return None