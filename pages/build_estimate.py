import streamlit as st
from temp_db.companies import COMPANIES
import datetime
from temp_db.items_catalog import ITEM_CATALOG

# st.set_page_config(page_title="Document Builder", page_icon="📄", layout="wide")
st.title("🧾 견적서 생성")

# 1. 회사 선택
company_name = st.selectbox("🏢 사용할 회사 선택", list(COMPANIES.keys()))
selected_company = COMPANIES[company_name]

with st.expander("🔍 회사 정보 확인", expanded=False):
    st.json(selected_company)

# 2. 견적서 정보 입력
estimate_number = st.text_input("견적서 번호", value="EST-001")
estimate_date = st.date_input("작성일", value=datetime.date.today())

# 3. 고객 정보 입력
st.subheader("👤 고객 정보 입력")
client_name = st.text_input("고객명")
client_phone = st.text_input("전화번호")
client_email = st.text_input("이메일")
client_street = st.text_input("Street Address")
cols = st.columns([1, 1, 1]) 
with cols[0]:
    client_city = st.text_input("City")
with cols[1]:
    client_state = st.text_input("State")
with cols[2]:
    client_zip = st.text_input("ZIP Code")

# 상단 Note
st.subheader("📝 견적서 노트")
top_note = st.text_area("Note 입력", key="top_note")

# Streamlit 상태 초기화
if "sections" not in st.session_state:
    st.session_state.sections = []

# 섹션 추가
st.subheader("📦 견적서 섹션 추가")
cols = st.columns([4, 1])  # 입력창 : 버튼 = 4:1 비율
with cols[0]:
    new_section_title = st.text_input("섹션 이름 입력", key="new_section")
with cols[1]:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    if st.button("➕ 섹션 추가"):
        if new_section_title:
            st.session_state.sections.append({
                "title": new_section_title,
                "items": [],
                "showSubtotal": True,
                "subtotal": 0.0
            })

# 각 섹션 반복 렌더링
for i, section in enumerate(st.session_state.sections):
    st.markdown(f"---\n### [ {section['title']} ]")

    # 추천 아이템 존재 여부 확인
    catalog = ITEM_CATALOG.get(section["title"], [])
    cols = st.columns([4.6, 1.2, 1.2])  # 추천 선택 / 추천 추가 / 수동 추가

    # 왼쪽: multiselect
    with cols[0]:
        item_names = [item["name"] for item in catalog] if catalog else []
        selected_items = st.multiselect("추천 아이템 선택", item_names, key=f"multi-{i}")

    # 가운데: 추천 아이템 추가 버튼
    with cols[1]:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("➕ 추천추가", key=f"btn-add-{i}"):
            for name in selected_items:
                match = next(item for item in catalog if item["name"] == name)
                if not any(it["name"] == name for it in section["items"]):
                    section["items"].append({
                        "name": match["name"],
                        "unit": match["unit"],
                        "price": match["price"],
                        "qty": 1.0,
                        "dec": ""
                    })

    # 오른쪽: 수동 아이템 추가 버튼
    with cols[2]:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("➕ 수동추가", key=f"manual-add-{i}"):
            section["items"].append({
                "name": "",
                "unit": "",
                "price": 0.0,
                "qty": 1.0,
                "dec": ""
            })


    st.markdown("---")

    # 아이템 목록 렌더링 및 수정
    for j, item in enumerate(section["items"]):
        cols = st.columns([6.4, 1.3, 1, 1.3, 1])
        with cols[0]:
            item["name"] = st.text_input("아이템명", value=item["name"], key=f"name-{i}-{j}")
        with cols[1]:
            item["qty"] = st.number_input("수량", value=item["qty"], step=1.0, key=f"qty-{i}-{j}")
        with cols[2]:
            item["unit"] = st.text_input("단위", value=item["unit"], key=f"unit-{i}-{j}")
        with cols[3]:
            item["price"] = st.number_input("단가", value=item["price"], step=0.01, key=f"price-{i}-{j}")
        with cols[4]:
            # 삭제 버튼
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("🗑️", key=f"delete-{i}-{j}"):
                section["items"].pop(j)
                st.rerun()
        # optional description
        desc_key = f"desc-{i}-{j}"
        with st.expander("📝 Description (선택)", expanded=bool(item.get("dec"))):
            item["dec"] = st.text_area("설명 입력", value=item.get("dec", ""), key=desc_key)

    # 섹션 subtotal 계산
    section["subtotal"] = round(sum(it["qty"] * it["price"] for it in section["items"]), 2)

    # subtotal 표시
    st.markdown(f"<p style='text-align:right; font-weight:bold;'>Subtotal: ${section['subtotal']:,.2f}</p>", unsafe_allow_html=True)

# 🔢 전체 Total 계산
total = round(sum(section["subtotal"] for section in st.session_state.sections), 2)
st.markdown(f"<p style='text-align:right; font-size:25px; font-weight:600;'>Total: ${total:,.2f}</p>", unsafe_allow_html=True)

# 📝 하단 Note 및 Disclaimer 입력
st.subheader("Note 및 Disclaimer")
bottom_note = st.text_area("Note", key="bottom_note")
disclaimer = st.text_area("Disclaimer", key="disclaimer")


if st.button("👁️ 미리보기로 이동"):
    st.session_state.selected_company = selected_company
    st.session_state.estimate_number = estimate_number
    st.session_state.estimate_date = estimate_date
    st.session_state.client_name = client_name
    st.session_state.client_phone = client_phone
    st.session_state.client_email = client_email
    st.session_state.client_street = client_street
    st.session_state.client_city = client_city
    st.session_state.client_state = client_state
    st.session_state.client_zip = client_zip
    st.session_state.top_note_preview = st.session_state.get("top_note", "")
    st.session_state.bottom_note_preview = st.session_state.get("bottom_note", "")
    st.session_state.disclaimer_preview = st.session_state.get("disclaimer", "")
    
    st.switch_page("pages/preview_estimate.py")


        

