import streamlit as st
import datetime
import re
from modules.company_module import get_all_companies
from modules.invoice_item_module import get_all_invoice_items
from modules.invoice_module import get_invoice_by_id

st.set_page_config(page_title="Invoice Builder", page_icon="📄", layout="wide")

# 세션 상태 초기화
if "sections" not in st.session_state:
    st.session_state.sections = []
if "payments" not in st.session_state:
    st.session_state.payments = []
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.from_page = ""

# 트리거 처리 (페이지 최상단에서 모든 액션 처리)
# 섹션 추가 트리거
if "add_section_trigger" in st.session_state:
    title = st.session_state.add_section_trigger
    st.session_state.sections.append({
        "title": title,
        "items": [],
        "showSubtotal": True,
        "subtotal": 0.0,
        "amount": 0.0  # 섹션별 금액 추가
    })
    del st.session_state.add_section_trigger

# 섹션 삭제 트리거
if "delete_section_trigger" in st.session_state:
    section_idx = st.session_state.delete_section_trigger
    if 0 <= section_idx < len(st.session_state.sections):
        st.session_state.sections.pop(section_idx)
    del st.session_state.delete_section_trigger

# 추천 항목 추가 트리거
if "add_recommended_items_trigger" in st.session_state:
    section_idx, items_to_add = st.session_state.add_recommended_items_trigger
    if 0 <= section_idx < len(st.session_state.sections):
        for item in items_to_add:
            # 중복 체크
            if not any(existing_item.get("code") == item["code"] for existing_item in st.session_state.sections[section_idx]["items"]):
                st.session_state.sections[section_idx]["items"].append({
                    "code": item["code"],
                    "name": item["name"],
                    "unit": item["unit"],
                    "price": item["unit_price"],
                    "qty": 1.0,
                    "dec": "",
                    "description": [],  # 새로운 description 형식
                    "amount": 0.0,  # 개별 아이템 금액
                    "hide_price": False
                })
    del st.session_state.add_recommended_items_trigger

# 수동 항목 추가 트리거
if "manual_add_trigger" in st.session_state:
    section_idx = st.session_state.manual_add_trigger
    if 0 <= section_idx < len(st.session_state.sections):
        st.session_state.sections[section_idx]["items"].append({
            "code": "",
            "name": "",
            "unit": "",
            "price": 0.0,
            "qty": 0.0,
            "dec": "",
            "description": [],  # 새로운 description 형식
            "amount": 0.0,  # 개별 아이템 금액
            "hide_price": False
        })
    del st.session_state.manual_add_trigger

# 항목 삭제 트리거
if "delete_item_trigger" in st.session_state:
    section_idx, item_idx = st.session_state.delete_item_trigger
    if (0 <= section_idx < len(st.session_state.sections) and
        0 <= item_idx < len(st.session_state.sections[section_idx]["items"])):
        st.session_state.sections[section_idx]["items"].pop(item_idx)
    del st.session_state.delete_item_trigger

# 납부 내역 삭제 트리거
if "delete_payment_trigger" in st.session_state:
    payment_idx = st.session_state.delete_payment_trigger
    if 0 <= payment_idx < len(st.session_state.payments):
        st.session_state.payments.pop(payment_idx)
    del st.session_state.delete_payment_trigger

# URL 파라미터에서 ID 추출
query_params = st.query_params
raw_id = query_params.get("id")
invoice_id = raw_id[0] if isinstance(raw_id, list) else raw_id
uuid_pattern = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")

# 기존 인보이스 로드
if invoice_id and uuid_pattern.match(invoice_id):
    if "invoice_loaded" not in st.session_state:
        invoice = get_invoice_by_id(invoice_id)
        if invoice:
            st.title("📄 인보이스 수정")
            data = invoice.get("data", {})

            st.session_state.invoice_number = data.get("invoice_number", "")
            st.session_state.date_of_issue = data.get("date_of_issue", datetime.date.today())
            st.session_state.date_due = data.get("date_due", datetime.date.today() + datetime.timedelta(days=7))

            client = data.get("client", {})
            st.session_state.client_name = client.get("name", "")
            st.session_state.client_phone = client.get("phone", "")
            st.session_state.client_email = client.get("email", "")
            st.session_state.client_street = client.get("address", "")
            st.session_state.client_city = client.get("city", "")
            st.session_state.client_state = client.get("state", "")
            st.session_state.client_zip = client.get("zip", "")
            st.session_state.client_type = data.get("client_type", "individual")

            # 보험 정보 로드
            insurance = data.get("insurance", {})
            st.session_state.insurance_company = insurance.get("company", "")
            st.session_state.insurance_policy_number = insurance.get("policy_number", "")
            st.session_state.insurance_claim_number = insurance.get("claim_number", "")

            # Amount due 텍스트 로드
            st.session_state.amount_due_text = data.get("amount_due_text", "")

            # Line Item Total 및 Material Sales Tax 로드
            st.session_state.line_item_total = data.get("line_item_total", 0.0)
            st.session_state.material_sales_tax = data.get("material_sales_tax", 0.0)

            st.session_state.top_note = data.get("top_note", "")
            st.session_state.bottom_note = data.get("bottom_note", "")
            st.session_state.disclaimer = data.get("disclaimer", "")
            st.session_state.sections = data.get("serviceSections", [])
            st.session_state.payments = data.get("payments", [])
            st.session_state.selected_company = data.get("company", {})
            st.session_state.from_page = "build_invoice"
            st.session_state.invoice_loaded = True
        else:
            st.error("❌ 해당 ID의 인보이스를 찾을 수 없습니다.")
            st.stop()
elif invoice_id:
    st.error("❌ 유효하지 않은 인보이스 ID 형식입니다.")
    st.stop()
else:
    # 새 인보이스 기본값 설정
    if "new_invoice_initialized" not in st.session_state:
        st.session_state.invoice_number = "INV-001"
        st.session_state.date_of_issue = datetime.date.today()
        st.session_state.date_due = datetime.date.today() + datetime.timedelta(days=7)
        st.session_state.client_name = ""
        st.session_state.client_phone = ""
        st.session_state.client_email = ""
        st.session_state.client_street = ""
        st.session_state.client_city = ""
        st.session_state.client_state = ""
        st.session_state.client_zip = ""
        st.session_state.client_type = "individual"

        # 보험 정보 초기화
        st.session_state.insurance_company = ""
        st.session_state.insurance_policy_number = ""
        st.session_state.insurance_claim_number = ""

        # Amount due 텍스트 초기화
        st.session_state.amount_due_text = ""

        # Line Item Total 및 Material Sales Tax 초기화
        st.session_state.line_item_total = 0.0
        st.session_state.material_sales_tax = 0.0

        st.session_state.top_note = ""
        st.session_state.bottom_note = ""
        st.session_state.disclaimer = ""
        st.session_state.selected_company = {}
        st.session_state.from_page = "build_invoice"
        st.session_state.new_invoice_initialized = True

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
date_due = st.date_input("납기일 (Date Due)", value=st.session_state.get("date_due",
    datetime.date.today() + datetime.timedelta(days=7)))

# Amount Due 설정
st.subheader("💰 결제 조건")
use_custom_amount_text = st.checkbox(
    "사용자 정의 결제 조건 사용",
    value=True,  # 기본으로 체크되도록 설정
    key="use_custom_amount"
)

if use_custom_amount_text:
    # 기본 텍스트 설정
    default_amount_text = st.session_state.get("amount_due_text",
        "") or "Payment due upon receipt of insurance settlement"
    amount_due_text = st.text_input(
        "Payment due upon receipt of depreciation amount from insurer",
        value=default_amount_text,
        placeholder="예: Payment due upon receipt of insurance settlement"
    )
else:
    amount_due_text = ""

# 고객 정보
st.subheader("👤 고객 정보")

current_client_type = st.session_state.get("client_type", "individual")

client_type = st.radio(
    "고객 유형을 선택하세요:",
    options=["individual", "company"],
    format_func=lambda x: "🧑 개인 고객" if x == "individual" else "🏢 회사 고객",
    horizontal=True,
    index=0 if current_client_type == "individual" else 1,
    key="client_type_radio"
)

st.session_state.client_type = client_type

if client_type == "company":
    cols = st.columns([3, 1])
    with cols[0]:
        company_options = ["직접 입력"] + company_names
        current_client_company = st.session_state.get("selected_client_company", "직접 입력")
        try:
            client_company_index = company_options.index(current_client_company)
        except ValueError:
            client_company_index = 0

        selected_client_company = st.selectbox(
            "🏢 고객 회사 선택",
            company_options,
            index=client_company_index,
            key="client_company_select"
        )

    with cols[1]:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("🔄 회사 정보 적용", key="apply_company_info"):
            if selected_client_company != "직접 입력":
                selected_client_company_info = next((c for c in companies if c["name"] == selected_client_company),
                    None)
                if selected_client_company_info:
                    st.session_state.client_name = selected_client_company_info.get("name", "")
                    st.session_state.client_phone = selected_client_company_info.get("phone", "")
                    st.session_state.client_email = selected_client_company_info.get("email", "")
                    st.session_state.client_street = selected_client_company_info.get("address", "")
                    st.session_state.client_city = selected_client_company_info.get("city", "")
                    st.session_state.client_state = selected_client_company_info.get("state", "")
                    st.session_state.client_zip = selected_client_company_info.get("zip", "")
                    st.session_state.selected_client_company = selected_client_company
                    st.rerun()

# 고객 정보 입력 필드들
client_name = st.text_input("고객명/회사명", value=st.session_state.get("client_name", ""))
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

# 보험 정보 섹션 추가
st.subheader("🏥 보험 정보")
use_insurance = st.checkbox("보험 정보 포함", value=bool(st.session_state.get("insurance_company", "")))

if use_insurance:
    insurance_company = st.text_input("보험 회사", value=st.session_state.get("insurance_company", ""))
    cols = st.columns([1, 1])
    with cols[0]:
        insurance_policy_number = st.text_input("Policy Number", value=st.session_state.get("insurance_policy_number",
            ""))
    with cols[1]:
        insurance_claim_number = st.text_input("Claim Number", value=st.session_state.get("insurance_claim_number", ""))
else:
    insurance_company = ""
    insurance_policy_number = ""
    insurance_claim_number = ""

# 상단 Note
st.subheader("📝 인보이스 노트 (상단)")
top_note = st.text_area("Note 입력", value=st.session_state.get("top_note", ""), key="top_note")

# 섹션 추가
st.subheader("📦 항목 섹션 추가")
cols = st.columns([1, 2])
with cols[0]:
    new_section_title = st.text_input("섹션 이름 입력", key="new_section")
with cols[1]:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    if st.button("➕ 섹션 추가", key="add_section_btn") and new_section_title:
        st.session_state.add_section_trigger = new_section_title
        st.rerun()

# 항목 전체 불러오기
ALL_ITEMS = get_all_invoice_items()

# 섹션 표시
for i, section in enumerate(st.session_state.sections):
    st.markdown("---")
    cols = st.columns([2, 1, 1])
    with cols[0]:
        new_title = st.text_input("📂 섹션 이름", value=section["title"], key=f"section-title-{i}")
        section["title"] = new_title
    with cols[1]:
        section_amount = st.number_input("섹션 금액", value=section.get("amount", 0.0), step=0.01,
            key=f"section-amount-{i}")
        section["amount"] = section_amount
    with cols[2]:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("🗑️ 섹션 삭제", key=f"delete-section-{i}"):
            st.session_state.delete_section_trigger = i
            st.rerun()

    # 해당 섹션 타이틀과 일치하는 카테고리의 항목들
    section_items = [item for item in ALL_ITEMS if item.get("category") == section["title"]]
    item_names = [f"{item['code']} - {item['name']}" for item in section_items]
    item_lookup = {f"{item['code']} - {item['name']}": item for item in section_items}

    # 항목 선택 및 추가
    cols = st.columns([4.6, 1.2, 1.2])
    with cols[0]:
        selected_items = st.multiselect("추천 아이템 선택", item_names, key=f"multi-{i}")
    with cols[1]:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("➕ 추천추가", key=f"btn-add-{i}") and selected_items:
            items_to_add = [item_lookup[name] for name in selected_items if name in item_lookup]
            if items_to_add:
                st.session_state.add_recommended_items_trigger = (i, items_to_add)
                st.rerun()
    with cols[2]:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("➕ 수동추가", key=f"manual-add-{i}"):
            st.session_state.manual_add_trigger = i
            st.rerun()

    # 항목 표시 및 편집
    for j, item in enumerate(section["items"]):
        st.markdown(f"**아이템 {j+1}**")

        cols = st.columns([3, 2, 1])
        with cols[0]:
            item["name"] = st.text_input("아이템명", value=item.get("name", ""), key=f"name-{i}-{j}")
        with cols[1]:
            item_amount = st.number_input("아이템 금액", value=item.get("amount", 0.0), step=0.01,
                key=f"item-amount-{i}-{j}")
            item["amount"] = item_amount
        with cols[2]:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("🗑️", key=f"delete-{i}-{j}"):
                st.session_state.delete_item_trigger = (i, j)
                st.rerun()

        # Description 입력 (리스트 형태로)
        with st.expander("📝 작업 상세 내역", expanded=bool(item.get("description", []))):
            # 기존 description을 문자열로 변환 (호환성)
            if isinstance(item.get("description"), str):
                desc_text = item["description"]
            elif isinstance(item.get("description"), list):
                desc_text = "\n".join(item["description"])
            else:
                desc_text = item.get("dec", "")  # 기존 dec 필드와의 호환성

            description_text = st.text_area(
                "작업 내역 (한 줄에 하나씩 입력)",
                value=desc_text,
                key=f"description-{i}-{j}",
                help="각 줄이 하나의 작업 항목이 됩니다"
            )

            # 텍스트를 리스트로 변환하여 저장
            item["description"] = [line.strip() for line in description_text.split('\n') if line.strip()]
            # 기존 dec 필드도 유지 (호환성)
            item["dec"] = description_text

    # 섹션 소계 계산 (기존 방식과 새로운 amount 방식 모두 고려)
    legacy_subtotal = round(sum(float(it.get("qty", 0)) * float(it.get("price", 0)) for it in section["items"]), 2)
    amount_subtotal = round(sum(float(it.get("amount", 0)) for it in section["items"]), 2)

    # amount가 설정되어 있으면 amount를 사용, 아니면 legacy 방식 사용
    if section.get("amount", 0) > 0:
        section["subtotal"] = section["amount"]
    elif amount_subtotal > 0:
        section["subtotal"] = amount_subtotal
    else:
        section["subtotal"] = legacy_subtotal

    st.markdown(f"<p style='text-align:right; font-weight:bold;'>Subtotal: ${section['subtotal']:,.2f}</p>",
        unsafe_allow_html=True)

# 총계 계산
subtotal_total = round(sum(section["subtotal"] for section in st.session_state.sections), 2)

# Line Item Total과 Material Sales Tax 입력
st.subheader("📊 추가 비용")
cols = st.columns([1, 1])
with cols[0]:
    line_item_total = st.number_input(
        "Line Item Total",
        value=st.session_state.get("line_item_total", 0.0),
        step=0.01,
        key="line_item_total_input"
    )
with cols[1]:
    material_sales_tax = st.number_input(
        "Material Sales Tax",
        value=st.session_state.get("material_sales_tax", 0.0),
        step=0.01,
        key="material_sales_tax_input"
    )

# 전체 총계 계산 (섹션 소계 + Line Item Total + Material Sales Tax)
grand_total = round(subtotal_total + line_item_total + material_sales_tax, 2)

# 납부 내역 입력란 UI
st.subheader("💵 납부 내역")

with st.form("payment_form", clear_on_submit=True):
    name_col, no_date_col, date_col, amount_col, btn_col = st.columns([2, 1, 2, 2, 1])

    with name_col:
        pay_name = st.text_input("납부 구분", placeholder="예: Deductible, 1st Check", key="pay_name")
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
            "name": pay_name if pay_name else "",  # payment 이름 추가
            "date": str(pay_date) if pay_date else "",
            "amount": float(pay_amount)
        })

# 입력된 납부 내역 보여주기
if st.session_state.payments:
    for i, payment in enumerate(st.session_state.payments):
        cols = st.columns([6, 1])
        with cols[0]:
            payment_amount = float(payment['amount']) if payment['amount'] else 0.0
            payment_name = payment.get('name', '')
            name_part = f"{payment_name} " if payment_name else ""
            date_part = f"({payment['date']}) " if payment['date'] else ""
            st.markdown(f"- {name_part}{date_part}— ${payment_amount:,.2f}")
        with cols[1]:
            if st.button("🗑️ 삭제", key=f"delete-payment-{i}"):
                st.session_state.delete_payment_trigger = i
                st.rerun()

paid_total = round(sum(float(p["amount"]) if p["amount"] else 0.0 for p in st.session_state.payments), 2)
total = round(grand_total - paid_total, 2)

st.markdown(f"<p style='text-align:right;'>Sections Subtotal: ${subtotal_total:,.2f}</p>", unsafe_allow_html=True)
if line_item_total > 0:
    st.markdown(f"<p style='text-align:right;'>Line Item Total: ${line_item_total:,.2f}</p>", unsafe_allow_html=True)
if material_sales_tax > 0:
    st.markdown(f"<p style='text-align:right;'>Material Sales Tax: ${material_sales_tax:,.2f}</p>",
        unsafe_allow_html=True)
st.markdown(f"<p style='text-align:right; font-weight:bold;'>Grand Total: ${grand_total:,.2f}</p>",
    unsafe_allow_html=True)
st.markdown(f"<p style='text-align:right;'>Total Paid Amount: ${paid_total:,.2f}</p>", unsafe_allow_html=True)
st.markdown(f"<h4 style='text-align:right;'>💰 Total Due: ${total:,.2f}</h4>", unsafe_allow_html=True)

# 하단 Note / Disclaimer
st.subheader("📌 인보이스 하단 노트 및 고지사항")
bottom_note = st.text_area("Note", value=st.session_state.get("bottom_note", ""), key="bottom_note")
disclaimer = st.text_area("Disclaimer", value=st.session_state.get("disclaimer", ""), key="disclaimer")

# 미리보기 이동
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
    st.session_state.client_type = client_type

    # 보험 정보 저장
    st.session_state.insurance_company = insurance_company
    st.session_state.insurance_policy_number = insurance_policy_number
    st.session_state.insurance_claim_number = insurance_claim_number

    # Amount due 텍스트 저장
    st.session_state.amount_due_text = amount_due_text

    # Line Item Total 및 Material Sales Tax 저장
    st.session_state.line_item_total = line_item_total
    st.session_state.material_sales_tax = material_sales_tax

    st.session_state.top_note_preview = top_note
    st.session_state.bottom_note_preview = bottom_note
    st.session_state.disclaimer_preview = disclaimer

    st.switch_page("pages/preview_depreciation_invoice.py")
