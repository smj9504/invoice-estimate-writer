import streamlit as st
from utils.estimate_service import (
    get_all_items, get_item_by_id, insert_item, update_item, delete_item,
    get_descriptions_by_item_name, insert_description, delete_description
)
import datetime

# 🔁 상태 초기화
if "edit_item_id" not in st.session_state:
    st.session_state.edit_item_id = None

# 📄 항목 목록 불러오기
items = get_all_items()

st.subheader("📋 견적 항목 목록")
for item in items:
    with st.container():
        cols = st.columns([3, 1, 1, 1, 1, 1])
        cols[0].markdown(f"**{item['name']}** ({item['category']})")
        cols[1].markdown(f"{item['unit']}")
        cols[2].markdown(f"${item['price']:.2f}")
        cols[3].markdown(item.get("crystal_date", "-"))

        if cols[4].button("✏️ 수정", key=f"edit-{item['id']}"):
            st.session_state.edit_item_id = item["id"]

        if cols[5].button("🗑️ 삭제", key=f"delete-{item['id']}"):
            delete_item(item["id"])
            st.success(f"🗑️ '{item['name']}' 삭제 완료")
            st.rerun()

# 🔍 수정 항목 불러오기
edit_item = None
if st.session_state.edit_item_id:
    edit_item = get_item_by_id(st.session_state.edit_item_id)

# 📝 항목 등록/수정 폼
st.markdown("---")
st.subheader("➕ 항목 등록 / 수정")

with st.form("item_form"):
    category = st.text_input("카테고리", value=edit_item["category"] if edit_item else "")
    name = st.text_input("아이템 이름", value=edit_item["name"] if edit_item else "")
    unit = st.text_input("단위", value=edit_item["unit"] if edit_item else "")
    price = st.number_input("단가", value=edit_item["price"] if edit_item else 0.0, step=1.0)
    crystal_date = st.date_input("Crystal Date", value=datetime.date.today())

    submitted = st.form_submit_button("💾 저장")

    if submitted:
        data = {
            "category": category,
            "name": name,
            "unit": unit,
            "price": price,
            "crystal_date": str(crystal_date)
        }

        if edit_item:
            update_item(edit_item["id"], data)
            st.success("✅ 항목 수정 완료")
        else:
            insert_item(data)
            st.success("✅ 새 항목 등록 완료")

        st.session_state.edit_item_id = None
        st.rerun()

# 📝 설명 관리
if edit_item:
    st.markdown("---")
    st.subheader(f"📝 설명 관리 - {edit_item['name']}")

    descriptions = get_descriptions_by_item_name(edit_item["name"])

    for i, desc in enumerate(descriptions):
        cols = st.columns([8, 1])
        cols[0].text_input("설명", value=desc["description"], key=f"desc-{desc['id']}", disabled=True)
        if cols[1].button("🗑️", key=f"desc-del-{desc['id']}"):
            delete_description(desc["id"])
            st.success("🗑️ 설명 삭제 완료")
            st.rerun()

    with st.form("desc_add_form"):
        new_desc = st.text_input("설명 추가")
        sort_order = st.number_input("순서", min_value=1, value=len(descriptions) + 1)
        submitted = st.form_submit_button("➕ 설명 추가")

        if submitted and new_desc.strip():
            insert_description({
                "item_name": edit_item["name"],
                "description": new_desc.strip(),
                "sort_order": sort_order
            })
            st.success("✅ 설명 추가 완료")
            st.rerun()
