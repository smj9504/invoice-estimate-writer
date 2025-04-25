import streamlit as st
import datetime
import re
from modules.company_module import get_all_companies
from modules.invoice_item_module import get_all_invoice_items
from modules.invoice_module import get_invoice_by_id

st.set_page_config(page_title="Invoice Builder", page_icon="📄", layout="wide")

# URL 파라미터에서 ID 추출
query_params = st.query_params
raw_id = query_params.get("id")
invoice_id = raw_id[0] if isinstance(raw_id, list) else raw_id

uuid_pattern = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")

if invoice_id and uuid_pattern.match(invoice_id):
    invoice = get_invoice_by_id(invoice_id)
    if invoice:
        st.title("📄 인보이스 수정")
        data = invoice.get("data", {})

        st.session_state.invoice_number = data.get("invoice_number", "")
        st.session_state.date_of_issue = data.get("date_of_issue", "")
        st.session_state.date_due = data.get("date_due", "")

        client = data.get("client", {})
        st.session_state.client_name = client.get("name", "")
        st.session_state.client_phone = client.get("phone", "")
        st.session_state.client_email = client.get("email", "")
        st.session_state.client_street = client.get("address", "")
        st.session_state.client_city = client.get("city", "")
        st.session_state.client_state = client.get("state", "")
        st.session_state.client_zip = client.get("zip", "")

        st.session_state.top_note = data.get("top_note", "")
        st.session_state.bottom_note = data.get("bottom_note", "")
        st.session_state.disclaimer = data.get("disclaimer", "")
        st.session_state.sections = data.get("serviceSections", [])
        st.session_state.payments = data.get("payments", [])
        st.session_state.selected_company = data.get("company", {})
        st.session_state.from_page = "build_invoice"
    else:
        st.error("❌ 해당 ID의 인보이스를 찾을 수 없습니다.")
        st.stop()
elif invoice_id:
    st.error("❌ 유효하지 않은 인보이스 ID 형식입니다.")
    st.stop()
else:
    # 인보이스 ID가 없는 경우, Reset session state 
    if st.session_state.get("from_page") != "build_invoice":
        st.title("📄 인보이스 생성")
        for key in [
            "invoice_number", "date_of_issue", "date_due",
            "client_name", "client_phone", "client_email",
            "client_street", "client_city", "client_state", "client_zip",
            "top_note", "bottom_note", "disclaimer", "sections",
            "payments", "selected_company"
        ]:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state.from_page = "build_invoice"

# 회사 정보
companies = get_all_companies()
if not companies:
    st.warning("⛔ 등록된 회사가 없습니다. 먼저 회사 정보를 등록하세요.")
    st.stop()

company_names = [c["name"] for c in companies]
default_company = st.session_state.get("selected_company", {}).get("name")
company_name = st.selectbox(
    "🏢 사용할 회사 선택",
    company_names,
    index=company_names.index(default_company) if default_company in company_names else 0
)
selected_company = next((c for c in companies if c["name"] == company_name), None)

# 인보이스 정보 
invoice_number = st.text_input("Invoice 번호", value=st.session_state.get("invoice_number", "INV-001"))
date_of_issue = st.date_input("날짜 (Date of Issue)", value=st.session_state.get("date_of_issue", datetime.date.today()))
date_due = st.date_input("납기일 (Date Due)", value=st.session_state.get("due_date", datetime.date.today()))

# 고객 정보
st.subheader("👤 고객 정보")
client_name = st.text_input("고객명", value=st.session_state.get("client_name", ""))
client_phone = st.text_input("전화번호", value=st.session_state.get("client_phone", ""))
client_email = st.text_input("이메일", value=st.session_state.get("client_email", ""))
client_street = st.text_input("Street Address", value=st.session_state.get("client_street", ""))
cols = st.columns([1, 1, 1])
with cols[0]:
    client_city = st.text_input("City", value=st.session_state.get("client_city", ""))
with cols[1]:
    client_state = st.text_input("State", value=st.session_state.get("client_state", ""))
with cols[2]:
    client_zip = st.text_input("ZIP Code", value=st.session_state.get("client_zip", ""))

# 상단 Note
st.subheader("📝 인보이스 노트 (상단)")
top_note = st.text_area("Note 입력", key="top_note")

if "sections" not in st.session_state:
    st.session_state.sections = []

st.subheader("📦 항목 섹션 추가")
cols = st.columns([1, 2])
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

ALL_ITEMS = get_all_invoice_items()

for i, section in enumerate(st.session_state.sections):
    st.markdown(f"---")
    cols = st.columns([1, 2])
    with cols[0]:
        new_title = st.text_input(f"📂 섹션 이름", value=section["title"], key=f"section-title-{i}")
        section["title"] = new_title
    with cols[1]:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("🗑️ 섹션 삭제", key=f"delete-section-{i}"):
            st.session_state.sections.pop(i)

    section_items = [item for item in ALL_ITEMS if item["category"] == section["title"]]
    item_names = [f"{item['code']} - {item['name']}" for item in section_items]
    item_lookup = {f"{item['code']} - {item['name']}": item for item in section_items}

    cols = st.columns([4.6, 1.2, 1.2])
    with cols[0]:
        selected_items = st.multiselect("추천 아이템 선택", item_names, key=f"multi-{i}")
    with cols[1]:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("➕ 추천추가", key=f"btn-add-{i}"):
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
                "qty": 0.0,
                "dec": ""
            })

    for j, item in enumerate(section["items"]):
        cols = st.columns([1, 5.4, 1.3, 1, 1.3, 1])
        with cols[0]:
            hide_price = st.checkbox("Hide Price", value=item.get("hide_price", False), key=f"hide_price_key-{i}-{j}")
            item["hide_price"] = hide_price
        with cols[1]:
            item["name"] = st.text_input("아이템명", value=item["name"], key=f"name-{i}-{j}")
        with cols[2]:
            item["qty"] = st.number_input("수량", value=item["qty"], step=1.00, key=f"qty-{i}-{j}")
        with cols[3]:
            item["unit"] = st.text_input("단위", value=item["unit"], key=f"unit-{i}-{j}")
        with cols[4]:
            item["price"] = st.number_input("단가", value=item["price"], step=0.01, key=f"price-{i}-{j}")
        with cols[5]:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("🗑️", key=f"delete-{i}-{j}"):
                section["items"].pop(j)
                st.rerun()

        desc_key = f"desc-{i}-{j}"
        with st.expander("📝 Description (선택)", expanded=bool(item.get("dec"))):
            item["dec"] = st.text_area("설명 입력", value=item.get("dec", ""), key=desc_key)

    section["subtotal"] = round(sum(float(it["qty"]) * float(it["price"]) for it in section["items"]), 2)
    st.markdown(f"<p style='text-align:right; font-weight:bold;'>Subtotal: ${section['subtotal']:,.2f}</p>", unsafe_allow_html=True)

# 납부 내역 입력란 UI
st.subheader("💵 납부 내역")
if "payments" not in st.session_state:
    st.session_state.payments = []

with st.form("payment_form", clear_on_submit=True):
    no_date_col, date_col, amount_col, btn_col = st.columns([1, 3, 2, 1])

    with no_date_col:
        no_date = st.checkbox("납부일 없음", key="no_pay_date")
    with date_col:
        if not no_date:
            pay_date = st.date_input("납부일", key="pay_date")
        else:
            pay_date = ""
    with amount_col:
        pay_amount = st.number_input("납부 금액", step=1.0, min_value=0.0)
    with btn_col:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        submit = st.form_submit_button("➕ 추가")

    if submit:
        st.session_state.payments.append({
            "date": str(pay_date) if pay_date else "",
            "amount": float(pay_amount)
        })

# 입력된 납부 내역 보여주기
if st.session_state.payments:
    for i, payment in enumerate(st.session_state.payments):
        st.markdown(f"- {payment['date']} — ${payment['amount']:,.2f}")
        if st.button("🗑️ 삭제", key=f"delete-payment-{i}"):
            st.session_state.payments.pop(i)
            st.rerun()

subtotal_total = round(sum(section["subtotal"] for section in st.session_state.sections), 2)
paid_total = round(sum(p["amount"] for p in st.session_state.get("payments", [])), 2)
total = round(subtotal_total - paid_total, 2)

st.markdown(f"<p style='text-align:right;'>Total Paid Amount: ${paid_total:,.2f}</p>", unsafe_allow_html=True)
st.markdown(f"<h4 style='text-align:right;'>💰 Total Due: ${total:,.2f}</h4>", unsafe_allow_html=True)


# 하단 Note / Disclaimer
st.subheader("📌 인보이스 하단 노트 및 고지사항")
bottom_note = st.text_area("Note", key="bottom_note")
disclaimer = st.text_area("Disclaimer", key="disclaimer")

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

    st.switch_page("pages/preview_invoice.py")
