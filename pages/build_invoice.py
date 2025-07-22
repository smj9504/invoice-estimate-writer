import streamlit as st
import datetime
import re
import json
from modules.company_module import get_all_companies
from modules.invoice_item_module import get_all_invoice_items
from modules.invoice_module import get_invoice_by_id

st.set_page_config(page_title="Invoice Builder", page_icon="📄", layout="wide")

# JSON 업로드 기능
st.sidebar.header("📂 JSON 업로드")
uploaded_file = st.sidebar.file_uploader("JSON 파일 업로드", type=['json'])

# JSON 데이터를 한 번만 읽어서 저장
if uploaded_file is not None:
    try:
        # 파일 내용을 문자열로 읽기
        uploaded_file.seek(0)  # 파일 포인터를 처음으로 리셋
        file_content = uploaded_file.read().decode('utf-8')
        json_data = json.loads(file_content)
        
        st.sidebar.markdown(f"**업로드된 파일:** {uploaded_file.name}")
        st.sidebar.markdown(f"**인보이스 번호:** {json_data.get('invoice_number', 'N/A')}")
        
        if st.sidebar.button("📥 JSON 데이터 로드"):
            # JSON 데이터를 세션 상태로 로드
            st.session_state.invoice_number = json_data.get("invoice_number", "INV-001")
            st.session_state.date_of_issue = json_data.get("date_of_issue", datetime.date.today())
            st.session_state.date_due = json_data.get("date_due", datetime.date.today() + datetime.timedelta(days=7))
            
            # 날짜 문자열을 date 객체로 변환
            if isinstance(st.session_state.date_of_issue, str):
                try:
                    st.session_state.date_of_issue = datetime.datetime.strptime(st.session_state.date_of_issue, "%Y-%m-%d").date()
                except:
                    st.session_state.date_of_issue = datetime.date.today()
            
            if isinstance(st.session_state.date_due, str):
                try:
                    st.session_state.date_due = datetime.datetime.strptime(st.session_state.date_due, "%Y-%m-%d").date()
                except:
                    st.session_state.date_due = datetime.date.today() + datetime.timedelta(days=7)
            
            # 클라이언트 정보
            client = json_data.get("client", {})
            st.session_state.client_name = client.get("name", "")
            st.session_state.client_phone = client.get("phone", "")
            st.session_state.client_email = client.get("email", "")
            st.session_state.client_street = client.get("address", "")
            st.session_state.client_city = client.get("city", "")
            st.session_state.client_state = client.get("state", "")
            st.session_state.client_zip = client.get("zip", "")
            st.session_state.client_type = json_data.get("client_type", "individual")
            
            # 노트
            st.session_state.top_note = json_data.get("top_note", "")
            st.session_state.bottom_note = json_data.get("bottom_note", "")
            st.session_state.disclaimer = json_data.get("disclaimer", "")
            
            # 섹션 및 결제 정보
            st.session_state.sections = json_data.get("serviceSections", [])
            st.session_state.payments = json_data.get("payments", [])
            st.session_state.selected_company = json_data.get("company", {})
            
            # 세금 정보
            st.session_state.tax_type = json_data.get("tax_type", "none")
            st.session_state.tax_rate = json_data.get("tax_rate", 0.0)
            st.session_state.tax_amount = json_data.get("tax_amount", 0.0)
            
            st.sidebar.success("✅ JSON 데이터가 로드되었습니다!")
            st.rerun()

        # JSON 직접 PDF 생성 기능
        st.sidebar.markdown("---")
        st.sidebar.header("🚀 바로 PDF 생성")
        if st.sidebar.button("📄 JSON에서 바로 PDF 생성"):
            try:
                # 이미 읽은 json_data 사용
                for key, value in json_data.items():
                    st.session_state[f"direct_{key}"] = value
                st.session_state.direct_pdf_mode = True
                st.switch_page("pages/preview_invoice.py")
            except Exception as e:
                st.sidebar.error(f"❌ PDF 생성 오류: {e}")
                
    except Exception as e:
        st.sidebar.error(f"❌ JSON 파일 읽기 오류: {e}")

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
        "subtotal": 0.0
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
            if not any(existing_item["code"] == item["code"] for existing_item in st.session_state.sections[section_idx]["items"]):
                st.session_state.sections[section_idx]["items"].append({
                    "code": item["code"],
                    "name": item["name"],
                    "unit": item["unit"],
                    "price": item["unit_price"],
                    "qty": 1.0,
                    "dec": "",
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
            st.session_state.client_type = data.get("client_type", "individual")  # 기본값을 개인으로 설정

            st.session_state.top_note = data.get("top_note", "")
            st.session_state.bottom_note = data.get("bottom_note", "")
            st.session_state.disclaimer = data.get("disclaimer", "")
            st.session_state.sections = data.get("serviceSections", [])
            st.session_state.payments = data.get("payments", [])
            st.session_state.selected_company = data.get("company", {})
            
            # 세금 정보 로드
            st.session_state.tax_type = data.get("tax_type", "none")
            st.session_state.tax_rate = data.get("tax_rate", 0.0)
            st.session_state.tax_amount = data.get("tax_amount", 0.0)
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
        st.session_state.client_type = "individual"  # 기본값을 개인으로 설정
        st.session_state.top_note = ""
        st.session_state.bottom_note = ""
        st.session_state.disclaimer = ""
        st.session_state.selected_company = {}
        st.session_state.from_page = "build_invoice"
        
        # 세금 정보 초기화
        st.session_state.tax_type = "none"
        st.session_state.tax_rate = 0.0
        st.session_state.tax_amount = 0.0
        
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
date_due = st.date_input("납기일 (Date Due)", value=st.session_state.get("date_due", datetime.date.today() + datetime.timedelta(days=7)))

# 고객 정보
st.subheader("👤 고객 정보")

# 현재 세션에서 클라이언트 타입 가져오기 (기본값: individual)
current_client_type = st.session_state.get("client_type", "individual")

# 고객 유형 선택
client_type = st.radio(
    "고객 유형을 선택하세요:", 
    options=["individual", "company"],
    format_func=lambda x: "🧑 개인 고객" if x == "individual" else "🏢 회사 고객",
    horizontal=True,
    index=0 if current_client_type == "individual" else 1,
    key="client_type_radio"
)

# 선택된 고객 유형을 세션 상태에 저장
st.session_state.client_type = client_type

# 고객 정보 입력 필드들을 위한 변수 초기화
client_name = ""
client_phone = ""
client_email = ""
client_street = ""
client_city = ""
client_state = ""
client_zip = ""

if client_type == "company":
    # 회사 고객인 경우 - 회사 선택 드롭다운 추가
    cols = st.columns([3, 1])
    with cols[0]:
        # "직접 입력" 옵션을 포함한 회사 목록 생성
        company_options = ["직접 입력"] + company_names
        
        # 현재 선택된 고객 회사 찾기
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
                selected_client_company_info = next((c for c in companies if c["name"] == selected_client_company), None)
                if selected_client_company_info:
                    # 세션 상태에 회사 정보 저장
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
    st.markdown(f"---")
    cols = st.columns([1, 2])
    with cols[0]:
        new_title = st.text_input(f"📂 섹션 이름", value=section["title"], key=f"section-title-{i}")
        section["title"] = new_title
    with cols[1]:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("🗑️ 섹션 삭제", key=f"delete-section-{i}"):
            st.session_state.delete_section_trigger = i
            st.rerun()

    # 해당 섹션 타이틀과 일치하는 카테고리의 항목들 (또는 모든 항목)
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
        cols = st.columns([1, 5.4, 1.3, 1, 1.3, 1])
        with cols[0]:
            hide_price = st.checkbox("Hide Price", value=item.get("hide_price", False), key=f"hide_price_key-{i}-{j}")
            item["hide_price"] = hide_price
        with cols[1]:
            item["name"] = st.text_input("아이템명", value=item.get("name", ""), key=f"name-{i}-{j}")
        with cols[2]:
            item["qty"] = st.number_input("수량", value=item.get("qty", 0.0), step=1.00, key=f"qty-{i}-{j}")
        with cols[3]:
            item["unit"] = st.text_input("단위", value=item.get("unit", ""), key=f"unit-{i}-{j}")
        with cols[4]:
            item["price"] = st.number_input("단가", value=item.get("price", 0.0), step=0.01, key=f"price-{i}-{j}")
        with cols[5]:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("🗑️", key=f"delete-{i}-{j}"):
                st.session_state.delete_item_trigger = (i, j)
                st.rerun()

        # 설명 입력
        with st.expander("📝 Description (선택)", expanded=bool(item.get("dec"))):
            item["dec"] = st.text_area("설명 입력", value=item.get("dec", ""), key=f"desc-{i}-{j}")

    # 섹션 소계 계산
    section["subtotal"] = round(sum(float(it["qty"]) * float(it["price"]) for it in section["items"]), 2)
    st.markdown(f"<p style='text-align:right; font-weight:bold;'>Subtotal: ${section['subtotal']:,.2f}</p>", unsafe_allow_html=True)

# 납부 내역 입력란 UI
st.subheader("💵 납부 내역")

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
        cols = st.columns([6, 1])
        with cols[0]:
            payment_amount = float(payment['amount']) if payment['amount'] else 0.0
            st.markdown(f"- {payment['date']} — ${payment_amount:,.2f}")
        with cols[1]:
            if st.button("🗑️ 삭제", key=f"delete-payment-{i}"):
                st.session_state.delete_payment_trigger = i
                st.rerun()

# 세금 섹션
st.subheader("💸 세금")

cols = st.columns([1, 1, 1])
with cols[0]:
    tax_type = st.radio(
        "세금 타입",
        options=["none", "percentage", "fixed"],
        format_func=lambda x: "세금 없음" if x == "none" else "퍼센트 (%)" if x == "percentage" else "고정 금액 ($)",
        index=["none", "percentage", "fixed"].index(st.session_state.get("tax_type", "none"))
    )
    st.session_state.tax_type = tax_type

with cols[1]:
    if tax_type == "percentage":
        tax_rate = st.number_input("세금율 (%)", value=st.session_state.get("tax_rate", 0.0), step=0.1, min_value=0.0, max_value=100.0)
        st.session_state.tax_rate = tax_rate
    else:
        st.session_state.tax_rate = 0.0
        
with cols[2]:
    if tax_type == "fixed":
        tax_amount = st.number_input("세금 금액 ($)", value=st.session_state.get("tax_amount", 0.0), step=1.0, min_value=0.0)
        st.session_state.tax_amount = tax_amount
    else:
        st.session_state.tax_amount = 0.0

# 총계 계산 (세금 포함)
subtotal_total = round(sum(section["subtotal"] for section in st.session_state.sections), 2)

# 세금 계산
tax_calculated = 0.0
if tax_type == "percentage" and tax_rate > 0:
    tax_calculated = round((subtotal_total * tax_rate / 100), 2)
elif tax_type == "fixed" and tax_amount > 0:
    tax_calculated = tax_amount

total_with_tax = round(subtotal_total + tax_calculated, 2)
paid_total = round(sum(float(p["amount"]) if p["amount"] else 0.0 for p in st.session_state.payments), 2)
total_due = round(total_with_tax - paid_total, 2)

st.markdown(f"<p style='text-align:right;'>Subtotal: ${subtotal_total:,.2f}</p>", unsafe_allow_html=True)
if tax_calculated > 0:
    if tax_type == "percentage":
        st.markdown(f"<p style='text-align:right;'>Tax ({tax_rate}%): ${tax_calculated:,.2f}</p>", unsafe_allow_html=True)
    else:
        st.markdown(f"<p style='text-align:right;'>Tax: ${tax_calculated:,.2f}</p>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align:right;'>Total with Tax: ${total_with_tax:,.2f}</p>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align:right;'>Total Paid Amount: ${paid_total:,.2f}</p>", unsafe_allow_html=True)
st.markdown(f"<h4 style='text-align:right;'>💰 Total Due: ${total_due:,.2f}</h4>", unsafe_allow_html=True)

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
    st.session_state.client_type = client_type  # 고객 유형 저장
    st.session_state.top_note_preview = top_note
    st.session_state.bottom_note_preview = bottom_note
    st.session_state.disclaimer_preview = disclaimer
    
    # 세금 정보 저장
    st.session_state.tax_type_preview = tax_type
    st.session_state.tax_rate_preview = tax_rate if tax_type == "percentage" else 0.0
    st.session_state.tax_amount_preview = tax_amount if tax_type == "fixed" else 0.0

    st.switch_page("pages/preview_invoice.py")