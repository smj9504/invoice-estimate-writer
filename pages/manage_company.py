import streamlit as st
from modules.company_module import (
    get_all_companies, get_company_by_id,
    insert_company, update_company, delete_company
)

st.set_page_config(page_title="회사 관리", page_icon="🏢", layout="wide")
st.title("🏢 회사 정보 관리")

# 🔄 상태 초기화
if "edit_company_id" not in st.session_state:
    st.session_state.edit_company_id = None

# 📥 회사 목록 불러오기
companies = get_all_companies()

# 📋 회사 목록 표시
st.subheader("📃 등록된 회사 목록")

for company in companies:
    cols = st.columns([3, 2, 2, 1, 1])
    cols[0].markdown(f"**{company['name']}**")
    cols[1].markdown(f"{company['city']}, {company['state']}")
    cols[2].markdown(company.get("phone", ""))
    
    if cols[3].button("✏️ 수정", key=f"edit-{company['id']}"):
        st.session_state.edit_company_id = company["id"]
        
    if cols[4].button("🗑️ 삭제", key=f"delete-{company['id']}"):
        delete_company(company["id"])
        st.success(f"✅ {company['name']} 삭제 완료")
        st.rerun()

# 🔧 수정 모드인 경우 정보 불러오기
edit_data = None
if st.session_state.edit_company_id:
    edit_data = get_company_by_id(st.session_state.edit_company_id)

# 📝 회사 등록/수정 폼
st.markdown("---")
st.subheader("➕ 회사 정보 등록 / 수정")

with st.form("company_form"):
    name = st.text_input("회사명", value=edit_data["name"] if edit_data else "")
    address = st.text_input("주소", value=edit_data["address"] if edit_data else "")
    city = st.text_input("도시", value=edit_data["city"] if edit_data else "")
    state = st.text_input("주", value=edit_data["state"] if edit_data else "")
    zip_code = st.text_input("우편번호", value=edit_data["zip"] if edit_data else "")
    phone = st.text_input("전화번호", value=edit_data["phone"] if edit_data else "")
    email = st.text_input("이메일", value=edit_data["email"] if edit_data else "")
    logo = st.text_input("로고 이미지 URL", value=edit_data.get("logo", "") if edit_data else "")

    submitted = st.form_submit_button("💾 저장")

    if submitted:
        data = {
            "name": name,
            "address": address,
            "city": city,
            "state": state,
            "zip": zip_code,
            "phone": phone,
            "email": email,
            "logo": logo
        }

        if edit_data:
            update_company(edit_data["id"], data)
            st.success("✅ 회사 정보 수정 완료")
            st.session_state.edit_company_id = None
        else:
            insert_company(data)
            st.success("✅ 새 회사 등록 완료")

        st.rerun()
