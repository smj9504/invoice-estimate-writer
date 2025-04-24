import streamlit as st
import datetime
from modules.company_module import get_all_companies
from modules.estimate_item_module import get_all_items

st.set_page_config(page_title="Estimate Builder", page_icon="📟", layout="wide")
st.title("📟 건적서 생성")

# 사업자 정보
companies = get_all_companies()
if not companies:
    st.warning("⛔ 등록된 회사가 없습니다. 먼저 회사 정보를 등록하세요.")
    st.stop()

company_names = [c["name"] for c in companies]
company_name = st.selectbox("🏢 사용할 회사 선택", company_names)
selected_company = next((c for c in companies if c["name"] == company_name), None)

with st.expander("🔍 회사 정보 확인", expanded=False):
    st.json(selected_company)

# 건적서 내용
estimate_number = st.text_input("건적서 번호", value="EST-001")
estimate_date = st.date_input("작성일", value=datetime.date.today())

# 고객 정보
st.subheader("👤 고객 정보 입력")
client_name = st.text_input("고객명")
client_phone = st.text_input("전화번호")
client_email = st.text_input("이메일")
client_street = st.text_input("Street Address")
cols = st.columns([1, 1, 1])
with cols[0]: client_city = st.text_input("City")
with cols[1]: client_state = st.text_input("State")
with cols[2]: client_zip = st.text_input("ZIP Code")

# 상단 Note
st.subheader("📝 건적서 노트")
top_note = st.text_area("Note 입력", key="top_note")

# 상태 설정
if "sections" not in st.session_state:
    st.session_state.sections = []

# 섹션 추가
st.subheader("📦 건적서 섹션 추가")
cols = st.columns([4, 1])
with cols[0]:
    new_section_title = st.text_input("섹션 이름", key="new_section")
with cols[1]:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    if st.button("➕ 추가") and new_section_title:
        st.session_state.sections.append({
            "title": new_section_title,
            "items": [],
            "showSubtotal": True,
            "subtotal": 0.0
        })

# DB에서 모든 항목 검색용으로 가져온다.
ALL_ITEMS = get_all_items()

# 건적서 섹션 복잡 생성
for i, section in enumerate(st.session_state.sections):
    st.markdown(f"---\n### [ {section['title']} ]")
    section_items = [item for item in ALL_ITEMS if item["category"] == section["title"]]
    item_names = [f"{item['code']} - {item['name']}" for item in section_items]
    item_lookup = {f"{item['code']} - {item['name']}": item for item in section_items}

    cols = st.columns([5, 1, 1])
    with cols[0]:
        selected_items = st.multiselect("항목 선택", item_names, key=f"multi-{i}")
    with cols[1]:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("➕ 추가", key=f"btn-add-{i}"):
            for full_name in selected_items:
                item = item_lookup[full_name]
                if not any(it["code"] == item["code"] for it in section["items"]):
                    section["items"].append({
                        "code": item["code"],
                        "name": item["name"],
                        "unit": item["unit"],
                        "price": item["unit_price"],
                        "qty": 1.0,
                        "dec": ""
                    })
    with cols[2]:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("➕ 수동추가", key=f"manual-add-{i}"):
            section["items"].append({
                "code": "",
                "name": "",
                "unit": "",
                "price": 0.0,
                "qty": 1.0,
                "dec": ""
            })

    st.markdown("---")

    for j, item in enumerate(section["items"]):
        cols = st.columns([6.4, 1.3, 1, 1.3, 1])
        with cols[0]:
            item["name"] = st.text_input("항목명", value=item["name"], key=f"name-{i}-{j}")
        with cols[1]:
            item["qty"] = st.number_input("수량", value=item["qty"], step=1.0, key=f"qty-{i}-{j}")
        with cols[2]:
            item["unit"] = st.text_input("단위", value=item["unit"], key=f"unit-{i}-{j}")
        with cols[3]:
            item["price"] = st.number_input("단가", value=item["price"], step=0.01, key=f"price-{i}-{j}")
        with cols[4]:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("🗑️", key=f"delete-{i}-{j}"):
                section["items"].pop(j)
                st.rerun()

        desc_key = f"desc-{i}-{j}"
        with st.expander("📝 Description (선택)", expanded=bool(item.get("dec"))):
            item["dec"] = st.text_area("설명 입력", value=item.get("dec", ""), key=desc_key)

    section["subtotal"] = round(sum(it["qty"] * it["price"] for it in section["items"]), 2)
    st.markdown(f"<p style='text-align:right; font-weight:bold;'>Subtotal: ${section['subtotal']:,.2f}</p>", unsafe_allow_html=True)

# Total
total = round(sum(section["subtotal"] for section in st.session_state.sections), 2)
st.markdown(f"<p style='text-align:right; font-size:25px; font-weight:600;'>Total: ${total:,.2f}</p>", unsafe_allow_html=True)

# Note / Disclaimer
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