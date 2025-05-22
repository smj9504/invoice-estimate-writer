import streamlit as st
import datetime
import uuid
import re
from modules.estimate_module import (
    get_all_items, get_item_by_id, insert_item, update_item, delete_item,
    get_descriptions_by_item_name, insert_description, delete_description,
    get_item_by_code
)

def generate_item_code(category, item_name):
    """
    카테고리와 아이템명으로 코드를 자동 생성
    예: Cabinetry + appliance garage → CABAG
    """
    if not category or not item_name:
        return f"AUTO-{uuid.uuid4().hex[:6]}"
    
    # 카테고리의 첫 3글자 (대문자)
    category_prefix = re.sub(r'[^A-Za-z]', '', category)[:3].upper()
    
    # 아이템명에서 중요한 단어들 추출 (전치사, 관사 제외)
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    
    # 아이템명을 단어들로 분할하고 정리 (하이픈, 콤마 등도 구분자로 사용)
    words = re.findall(r'\b[A-Za-z]+\b', item_name.lower())
    important_words = [word for word in words if word not in stop_words and len(word) > 1]
    
    if not important_words:
        # 중요한 단어가 없으면 모든 단어 사용
        important_words = [word for word in words if len(word) > 1]
    
    # 각 중요한 단어의 첫 글자들을 조합
    if len(important_words) == 1:
        # 단어가 1개면 그 단어의 첫 4글자까지
        item_suffix = important_words[0][:4].upper()
    elif len(important_words) == 2:
        # 단어가 2개면 각각 2글자씩 또는 첫 글자들
        first_word = important_words[0]
        second_word = important_words[1]
        
        if len(first_word) >= 2 and len(second_word) >= 2:
            item_suffix = first_word[:2].upper() + second_word[:2].upper()
        else:
            item_suffix = first_word[0].upper() + second_word[0].upper()
    else:
        # 단어가 3개 이상이면 첫 번째 단어는 2-3글자, 나머지는 첫 글자
        first_word = important_words[0]
        other_words = important_words[1:3]  # 최대 2개까지만
        
        if len(first_word) >= 3:
            item_suffix = first_word[:2].upper() + ''.join([word[0].upper() for word in other_words])
        else:
            item_suffix = first_word.upper() + ''.join([word[0].upper() for word in other_words])
    
    # 최종 코드 생성 (최대 8글자로 제한)
    generated_code = (category_prefix + item_suffix)[:8]
    
    # 코드가 너무 짧으면 보완
    if len(generated_code) < 4:
        generated_code += uuid.uuid4().hex[:2].upper()
    
    return generated_code

# 🔁 상태 초기화
if "edit_item_id" not in st.session_state:
    st.session_state.edit_item_id = None

# 📄 항목 목록 불러오기
try:
    items = get_all_items()
    if items is None:
        items = []
except Exception as e:
    st.error(f"항목을 불러오는 중 오류가 발생했습니다: {e}")
    items = []

st.subheader("📋 견적 항목 목록")
for item in items:
    with st.container():
        cols = st.columns([4, 1, 1, 1, 1, 1])
        cols[0].markdown(f"**{item['name']}** ({item['category']})")
        cols[1].markdown(f"{item['unit']}")
        cols[2].markdown(f"${item.get('unit_price', 0):.2f}")
        cols[3].markdown(item.get("created_at", "-"))

        if cols[4].button("✏️ 수정", key=f"edit-{item['id']}"):
            st.session_state.edit_item_id = item["id"]

        if cols[5].button("🗑️ 삭제", key=f"delete-{item['id']}"):
            try:
                delete_item(item["id"])
                st.success(f"🗑️ '{item['name']}' 삭제 완료")
                st.rerun()
            except Exception as e:
                st.error(f"삭제 중 오류가 발생했습니다: {e}")

# 🔍 수정 항목 불러오기
edit_item = None
if st.session_state.edit_item_id:
    try:
        edit_item = get_item_by_id(st.session_state.edit_item_id)
    except Exception as e:
        st.error(f"항목을 불러오는 중 오류가 발생했습니다: {e}")
        st.session_state.edit_item_id = None

# 📝 항목 등록/수정 폼
st.markdown("---")
st.subheader("➕ 항목 등록 / 수정")

# 코드 생성 규칙 설명
with st.expander("💡 자동 코드 생성 규칙"):
    st.markdown("""
    **코드를 비워두면 다음 규칙으로 자동 생성됩니다:**
    - 카테고리 첫 3글자 + 아이템명의 주요 단어 조합
    - 예시:
        - Cabinetry + appliance garage → **CABAG** (CAB + A + G)
        - Cabinetry + wood panel → **CABWOPA** (CAB + WO + PA)
        - Backsplash + stainless steel → **BACSTST** (BAC + ST + ST)
        - Service + counter → **SERCOUN** (SER + COUN)
    - 중복되는 경우 숫자가 자동으로 추가됩니다 (예: CABAG1, CABAG2...)
    - 최대 8글자로 제한됩니다
    """)

    # 실시간 예시 생성기
    st.markdown("**실시간 코드 생성 테스트:**")
    test_cols = st.columns(2)
    with test_cols[0]:
        test_category = st.text_input("테스트 카테고리", value="Cabinetry", key="test_cat")
    with test_cols[1]:
        test_item = st.text_input("테스트 아이템명", value="appliance garage", key="test_item")
    
    if test_category and test_item:
        test_code = generate_item_code(test_category, test_item)
        st.code(f"생성될 코드: {test_code}")

with st.form("item_form"):
    code = st.text_input("코드", value=edit_item["code"] if edit_item else "")
    category = st.text_input("카테고리", value=edit_item["category"] if edit_item else "")
    subcategory = st.text_input("서브카테고리", value=edit_item["subcategory"] if edit_item else "")
    name = st.text_input("아이템 이름", value=edit_item["name"] if edit_item else "")
    unit = st.text_input("단위", value=edit_item["unit"] if edit_item else "")
    price = st.number_input("단가", value=edit_item["unit_price"] if edit_item else 0.0, step=1.0)
    
    # 코드 미리보기 (코드가 비어있고 카테고리와 아이템명이 있을 때)
    if not code.strip() and category.strip() and name.strip():
        preview_code = generate_item_code(category, name)
        st.info(f"💡 자동 생성될 코드: **{preview_code}**")

    submitted = st.form_submit_button("💾 저장")

    if submitted:
        try:
            if not code.strip():
                # 카테고리와 아이템명으로 코드 자동 생성
                code = generate_item_code(category, name)

            existing = get_item_by_code(code.strip())
            if existing and (not edit_item or existing["id"] != edit_item["id"]):
                # 코드가 중복되면 숫자를 추가해서 유니크하게 만들기
                base_code = code.strip()
                counter = 1
                while existing and (not edit_item or existing["id"] != edit_item["id"]):
                    code = f"{base_code}{counter}"
                    existing = get_item_by_code(code)
                    counter += 1
                    if counter > 99:  # 무한 루프 방지
                        code = f"{base_code}-{uuid.uuid4().hex[:4].upper()}"
                        break
                st.info(f"💡 코드가 중복되어 **{code}**로 저장됩니다.")

            # 데이터 저장
            data = {
                "code": code.strip(),
                "category": category,
                "subcategory": subcategory,
                "name": name,
                "unit": unit,
                "unit_price": price
            }

            if edit_item:
                update_item(edit_item["id"], data)
                st.success("✅ 항목 수정 완료")
            else:
                insert_item(data)
                st.success("✅ 새 항목 등록 완료")

            st.session_state.edit_item_id = None
            st.rerun()
        except Exception as e:
            st.error(f"저장 중 오류가 발생했습니다: {e}")

# 📝 설명 관리
if edit_item:
    st.markdown("---")
    st.subheader(f"📝 설명 관리 - {edit_item['name']}")

    # 설명 목록 안전하게 불러오기
    descriptions = []
    try:
        result = get_descriptions_by_item_name(edit_item["name"])
        if result is not None:
            descriptions = result
        else:
            descriptions = []
    except (AttributeError, TypeError) as e:
        # 'NoneType' object has no attribute 'data' 에러 처리
        st.warning("설명 데이터를 불러올 수 없습니다. 데이터베이스 연결을 확인해주세요.")
        descriptions = []
    except Exception as e:
        st.error(f"설명을 불러오는 중 오류가 발생했습니다: {e}")
        descriptions = []

    # 기존 설명 표시
    for i, desc in enumerate(descriptions):
        cols = st.columns([8, 1])
        cols[0].text_input("설명", value=desc.get("description", ""), key=f"desc-{desc.get('id', i)}", disabled=True)
        if cols[1].button("🗑️", key=f"desc-del-{desc.get('id', i)}"):
            try:
                delete_description(desc["id"])
                st.success("🗑️ 설명 삭제 완료")
                st.rerun()
            except Exception as e:
                st.error(f"설명 삭제 중 오류가 발생했습니다: {e}")

    # 새 설명 추가 폼
    with st.form("desc_add_form"):
        new_desc = st.text_input("설명 추가")
        sort_order = st.number_input("순서", min_value=1, value=len(descriptions) + 1)
        submitted = st.form_submit_button("➕ 설명 추가")

        if submitted and new_desc.strip():
            try:
                insert_description({
                    "item_name": edit_item["name"],
                    "description": new_desc.strip(),
                    "sort_order": sort_order
                })
                st.success("✅ 설명 추가 완료")
                st.rerun()
            except Exception as e:
                st.error(f"설명 추가 중 오류가 발생했습니다: {e}")

# 취소 버튼 (수정 모드일 때만 표시)
if edit_item:
    if st.button("❌ 수정 취소"):
        st.session_state.edit_item_id = None
        st.rerun()