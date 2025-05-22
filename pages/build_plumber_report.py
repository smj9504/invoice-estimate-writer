import streamlit as st
from jinja2 import Environment, FileSystemLoader
from datetime import date, datetime
# from weasyprint import HTML
from modules.company_module import get_all_companies

# Set up Jinja2 environment
env = Environment(loader=FileSystemLoader("templates"))

# Page configuration
st.set_page_config(page_title="Plumber Report Generator", layout="wide")
st.title("Plumber Report & Invoice Generator")

# Load companies
companies = get_all_companies()
if not companies:
    st.warning("등록된 회사가 없습니다. 먼저 회사 정보를 등록하세요.")
    st.stop()

company_names = [c["name"] for c in companies]
default_company = st.session_state.get("selected_company", {}).get("name")
company_name = st.selectbox(
    "🏢 사용할 회사 선택",
    company_names,
    index=company_names.index(default_company) if default_company in company_names else 0
)
selected_company = next((c for c in companies if c["name"] == company_name), None)

# Initialize session_state
if "invoice_items" not in st.session_state:
    st.session_state.invoice_items = []
if "payments" not in st.session_state:
    st.session_state.payments = []

st.markdown("---")

# --- Client Info ---
st.subheader("Client Information")
client = {}
client["name"] = st.text_input("Client Name")
col1, col2 = st.columns(2)
with col1:
    client["phone"] = st.text_input("Client Phone")
with col2:
    client["email"] = st.text_input("Client Email")
client["address"] = st.text_input("Service Address")


# --- Plumber Info ---
st.subheader("Plumber Information")
plumber = {}
col1, col2 = st.columns(2)
with col1:
    plumber["name"] = st.text_input("Plumber Name")
with col2:
    plumber["license"] = st.text_input("License Number")
plumber["company"] = st.text_input("Plumber Company", value=selected_company["name"])
plumber["phone"] = st.text_input("Plumber Phone", value=selected_company["phone"])


# --- Damage Assessment ---

def sync_dates_from_incident():
    new_date = st.session_state["incident_date"]
    st.session_state["start_date"] = new_date
    st.session_state["end_date"] = new_date
    st.session_state["report_date"] = new_date

    for i in range(len(st.session_state.payments)):
        st.session_state[f"paydate{i}"] = new_date
        st.session_state.payments[i]["date"] = new_date.strftime("%B %d, %Y")


st.subheader("Damage Assessment")
col1, col2 = st.columns(2)
with col1:
    incident_date = st.date_input(
        "Date of Incident",
        key="incident_date",
        on_change=sync_dates_from_incident
    )
with col2:
    category = st.radio("Water Intrusion Category", ["Cat 1", "Cat 2", "Cat 3"], horizontal=True, key="damage_category")

damage = {
    "incident_date": incident_date.strftime("%B %d, %Y"),
    "area": st.text_area("Affected Area"),
    "category": category,
    "cause": st.text_input("Cause of Damage"),
    "scope": st.text_area("Scope of Damage")
}

# Sync other dates with incident_date
if "date_synced" not in st.session_state or st.session_state["date_synced"] is False:
    st.session_state["start_date"] = incident_date
    st.session_state["end_date"] = incident_date
    st.session_state["report_date"] = incident_date
    # Update all payment dates too
    for i in range(len(st.session_state.payments)):
        st.session_state.payments[i]["date"] = incident_date.strftime("%B %d, %Y")
    st.session_state["date_synced"] = True

# --- Repair Details ---
st.subheader("Repair Details")
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date", key="start_date")
with col2:
    end_date = st.date_input("End Date", key="end_date")
repair = {
    "start_date": start_date,
    "end_date": end_date,
    "work": st.text_area("Scope of Work"),
    "materials": st.text_area("Materials Used"),
    "equipment": st.text_area("Equipment Used"),
    "result": st.text_area("Post-Repair Condition")
}

# --- Invoice Items ---
st.subheader("Invoice Items")

if st.button("➕ Add Invoice Item"):
    st.session_state.invoice_items.append({
        "description": "",
        "qty": "",
        "unit": "",
        "unit_price": "",
        "line_total": ""
    })

total_subtotal = 0.0

for idx, item in enumerate(st.session_state.invoice_items):
    with st.expander(f"Item {idx+1}"):
        col1, col2, col3, col4, col5 = st.columns([5, 1, 1, 1.5, 1.5])

        with col1:
            raw_desc = st.text_area(f"Description {idx}", value=item["description"], key=f"desc{idx}")
            item["description"] = raw_desc.replace("\n", "<br>")  # 줄바꿈 변환
        with col2:
            item["qty"] = st.text_input(f"Qty {idx}", value=item["qty"], key=f"qty{idx}")
        with col3:
            item["unit"] = st.text_input(f"Unit {idx}", value=item["unit"], key=f"unit{idx}")
        with col4:
            item["unit_price"] = st.text_input(f"Unit Price {idx}", value=item["unit_price"], key=f"unit_price{idx}")

        try:
            qty_float = float(item["qty"])
            unit_price_float = float(item["unit_price"])
            line_total_value = qty_float * unit_price_float
            line_total_str = f"{line_total_value:.2f}"
        except (ValueError, TypeError):
            line_total_value = 0.0
            line_total_str = ""

        with col5:
            item["line_total"] = line_total_str
            st.text_input(f"Line Total {idx}", value=line_total_str, key=f"line_total{idx}", disabled=True)

        try:
            total_subtotal += line_total_value
        except NameError:
            pass

# --- Payments ---
st.subheader("Payments")

if st.button("➕ Add Payment"):
    st.session_state.payments.append({
        "date": "",
        "amount": ""
    })

total_payments = 0.0

for idx, payment in enumerate(st.session_state.payments):
    with st.expander(f"Payment {idx+1}"):
        col1, col2 = st.columns(2)
        with col1:
            selected_date = st.date_input(
                f"Payment Date {idx}",
                key=f"paydate{idx}"
            )
            payment["date"] = st.session_state[f"paydate{idx}"].strftime("%B %d, %Y")
            payment["date_parsed"] = selected_date

        with col2:
            payment["amount"] = st.text_input(f"Payment Amount {idx}", value=payment["amount"], key=f"payamount{idx}")

# --- Calculate total_payments numerically ---
for payment in st.session_state.payments:
    try:
        total_payments += float(payment["amount"])
    except:
        pass

# --- Format amounts for HTML display ---
for payment in st.session_state.payments:
    try:
        float_amt = float(payment["amount"])
        payment["amount_display"] = f"${float_amt:,.2f}"
    except:
        payment["amount_display"] = "$0.00"

# --- Subtotal & Total Due Calculation ---
calculated_subtotal = f"${total_subtotal:,.2f}"
calculated_due = f"${(total_subtotal - total_payments):,.2f}"


st.subheader("Summary")
col1, col2 = st.columns(2)
with col1:
    subtotal = st.text_input("Total Charges", value=calculated_subtotal, key="subtotal", disabled=True)
with col2:
    total_due = st.text_input("Total Due", value=calculated_due, key="totaldue", disabled=True)

# --- 기타 입력 ---
# 오늘 날짜 기준 YYMM 포맷
today = datetime.today()
prefix_date = today.strftime("%y%m")  # 예: '2505'

# 기본 ID 구성
default_report_id = f"PLM-{prefix_date}-001"
default_invoice_number = f"INV-{prefix_date}-001"

notes = st.text_area("Notes & Recommendations")
report_id = st.text_input("Report ID", value=default_report_id)
invoice_number = st.text_input("Invoice Number", value=default_invoice_number)
report_date = st.date_input("Report Date", key="report_date").strftime("%B %d, %Y")
today_str = date.today().strftime("%B %d, %Y")

# --- Generate Report ---
if st.button("Generate HTML Report"):
    # 줄바꿈 변환
    repair["work"] = repair["work"].replace("\n", "<br>")
    repair["materials"] = repair["materials"].replace("\n", "<br>")
    repair["equipment"] = repair["equipment"].replace("\n", "<br>")
    repair["result"] = repair["result"].replace("\n", "<br>")
    damage["scope"] = damage["scope"].replace("\n", "<br>")
    notes = notes.replace("\n", "<br>")

    # CSS 로딩
    with open("templates/plumber_report_style.css", "r", encoding="utf-8") as css_file:
        css_content = css_file.read()

    dynamic_footer_css = f"""
    @page {{
        @bottom-left {{
            content: "{client['address']}";
            font-size: 10px;
        }}
        @bottom-right {{
            content: "Page " counter(page);
            font-size: 10px;
        }}
    }}
    """

    final_css = css_content + "\n" + dynamic_footer_css

    invoice = {
        "number": invoice_number,
        "items": st.session_state.invoice_items,
        "payments": st.session_state.payments,
        "subtotal": calculated_subtotal,
        "total_due": calculated_due
    }

    template = env.get_template("plumber_report.html")
    html = template.render(
        company=selected_company,
        client=client,
        plumber=plumber,
        damage=damage,
        repair=repair,
        invoice=invoice,
        notes=notes,
        report_id=report_id,
        report_date=report_date,
        today=today_str,
        page_number="1",
        css_inline=final_css
    )

    # 저장
    with open("rendered_report.html", "w", encoding="utf-8") as f:
        f.write(html)

    st.success("✅ Report generated successfully!")
    st.download_button("⬇️ Download HTML", data=html, file_name="plumber_report.html", mime="text/html")
