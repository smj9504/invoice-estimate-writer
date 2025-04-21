import streamlit as st
import datetime
from utils.company_service import get_all_companies
from temp_db.items_catalog import ITEM_CATALOG  # 향후 DB 연동 시 교체

st.set_page_config(page_title="📄 인보이스 작성", page_icon="📄", layout="wide")
st.title("📄 인보이스 생성")

# 회사 선택
companies = get_all_companies()
if not companies:
    st.warning("⛔ 등록된 회사가 없습니다. 먼저 회사 정보를 등록하세요.")
    st.stop()

company_names = [c["name"] for c in companies]
company_name = st.selectbox("🏢 사용할 회사 선택", company_names)
selected_company = next((c for c in companies if c["name"] == company_name), None)

with st.expander("🔍 회사 정보 확인", expanded=False):
    st.json(selected_company)

# 인보이스 정보
invoice_number = st.text_input("Invoice 번호", value="INV-001")
date_of_issue = st.date_input("날짜 (Date of Issue)", value=datetime.date.today())
date_due = st.date_input("납기일 (Date Due)", value=datetime.date.today())

# 고객 정보
st.subheader("👤 고객 정보")
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

# 상단 노트
st.subheader("📝 인보이스 노트 (상단)")
top_note = st.text_area("Note 입력", key="top_note")

# Streamlit 상태 초기화
if "sections" not in st.session_state:
    st.session_state.sections = []

# 섹션 추가
st.subheader("📦 항목 섹션 추가")
cols = st.columns([4, 1])
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

# 항목 입력
for i, section in enumerate(st.session_state.sections):
    st.markdown(f"---\n### 📂 섹션: {section['title']}")
    catalog = ITEM_CATALOG.get(section["title"], [])

    cols = st.columns([4.6, 1.2, 1.2])
    with cols[0]:
        item_names = [item["name"] for item in catalog] if catalog else []
        selected_items = st.multiselect("추천 아이템 선택", item_names, key=f"multi-{i}")
    with cols[1]:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("➕ 추천추가", key=f"btn-add-{i}"):
            for name in selected_items:
                match = next((item for item in catalog if item["name"] == name), None)
                if match and not any(it["name"] == name for it in section["items"]):
                    section["items"].append({
                        "name": match["name"],
                        "unit": match["unit"],
                        "price": match["price"],
                        "qty": 1.0,
                        "dec": ""
                    })
    with cols[2]:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("➕ 수동추가", key=f"manual-add-{i}"):
            section["items"].append({
                "name": "",
                "unit": "",
                "price": 0.0,
                "qty": 0.0,
                "dec": ""
            })

    # 아이템 수정 UI
    for j, item in enumerate(section["items"]):
        cols = st.columns([6.4, 1.3, 1, 1.3, 1])
        with cols[0]:
            item["name"] = st.text_input("아이템명", value=item["name"], key=f"name-{i}-{j}")
        with cols[1]:
            item["qty"] = st.number_input("수량", value=item["qty"], step=1.00, key=f"qty-{i}-{j}")
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

    # 유효한 항목만 subtotal 계산
    section["subtotal"] = round(sum(
        float(it["qty"]) * float(it["price"])
        for it in section["items"]
    ), 2)
    st.markdown(f"<p style='text-align:right; font-weight:bold;'>Subtotal: ${section['subtotal']:,.2f}</p>", unsafe_allow_html=True)

# 전체 Total
total = round(sum(section["subtotal"] for section in st.session_state.sections), 2)
st.markdown(f"<h4 style='text-align:right;'>💰 Total: ${total:,.2f}</h4>", unsafe_allow_html=True)

# 납부 내역 입력
st.subheader("💵 납부 내역 추가")

if "payments" not in st.session_state:
    st.session_state.payments = []

with st.form("payment_form", clear_on_submit=True):
    col1, col2 = st.columns([2, 1])
    with col1:
        no_date = st.checkbox("납부일 없음", key="no_pay_date")
        if not no_date:
            pay_date = st.date_input("납부일", key="pay_date")
        else:
            pay_date = ""
    with col2:
        pay_amount = st.number_input("납부 금액", step=1.0, min_value=0.0)

    if st.form_submit_button("➕ 납부 내역 추가"):
        st.session_state.payments.append({
            "date": str(pay_date) if pay_date else "",  # 빈값 허용
            "amount": float(pay_amount)
        })

# 입력된 납부 내역 보여주기
if st.session_state.payments:
    st.markdown("##### 💰 납부 내역")
    for i, payment in enumerate(st.session_state.payments):
        st.markdown(f"- {payment['date']} — ${payment['amount']:,.2f}")
        if st.button("🗑️ 삭제", key=f"delete-payment-{i}"):
            st.session_state.payments.pop(i)
            st.rerun()

# 하단 Note / Disclaimer
st.subheader("📌 인보이스 하단 노트 및 고지사항")
bottom_note = st.text_area("Note", key="bottom_note")
disclaimer = st.text_area("Disclaimer", key="disclaimer")

# 👉 미리보기 페이지로 전환
if st.button("👁️ 미리보기로 이동"):
    st.session_state.selected_company = selected_company
    st.session_state.invoice_number = invoice_number
    st.session_state.date_of_issue = date_of_issue
    st.session_state.date_due = date_due

    st.session_state.client_name = client_name
    st.session_state.client_phone = client_phone
    st.session_state.client_email = client_email
    st.session_state.client_street = client_street
    st.session_state.client_city = client_city
    st.session_state.client_state = client_state
    st.session_state.client_zip = client_zip

    st.session_state.top_note_preview = top_note
    st.session_state.bottom_note_preview = bottom_note
    st.session_state.disclaimer_preview = disclaimer
    st.session_state.payments = st.session_state.get("payments", [])

    st.switch_page("pages/preview_invoice.py")
