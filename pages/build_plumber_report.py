import streamlit as st
from jinja2 import Environment, FileSystemLoader
from datetime import date
from weasyprint import HTML

# Set up Jinja2 environment
env = Environment(loader=FileSystemLoader("templates"))

# Page configuration
st.set_page_config(page_title="Plumber Report Generator", layout="wide")
st.title("🧰 Plumber Report & Invoice Generator")

# Initialize session_state
if "invoice_items" not in st.session_state:
    st.session_state.invoice_items = []
if "payments" not in st.session_state:
    st.session_state.payments = []

# --- Buttons OUTSIDE the form ---
st.header("Manage Invoice Items and Payments")

col1, col2 = st.columns(2)
with col1:
    if st.button("➕ Add Invoice Item"):
        st.session_state.invoice_items.append({
            "description": "",
            "qty": "",
            "unit": "",
            "unit_price": "",
            "line_total": ""
        })

with col2:
    if st.button("➕ Add Payment"):
        st.session_state.payments.append({
            "date": "",
            "amount": ""
        })

st.markdown("---")

# --- Main Form ---
with st.form("report_form"):
    st.subheader("Company Info")
    with st.sidebar:
        company = {
            "name": st.text_input("Company Name", "JJL Plumbing Services"),
            "address": st.text_input("Street Address", "123 Pipe St"),
            "city_state_zip": st.text_input("City/State/ZIP", "Flowtown, IL 60123"),
            "phone": st.text_input("Phone", "(987) 654-3210"),
            "email": st.text_input("Email", "info@jjlplumbing.com")
        }

    st.subheader("Client Information")
    client = {
        "name": st.text_input("Client Name"),
        "phone": st.text_input("Client Phone"),
        "email": st.text_input("Client Email"),
        "address": st.text_input("Service Address")
    }

    st.subheader("Plumber Information")
    plumber = {
        "name": st.text_input("Plumber Name"),
        "company": st.text_input("Plumber Company"),
        "phone": st.text_input("Plumber Phone"),
        "license": st.text_input("License Number")
    }

    st.subheader("Damage Assessment")
    damage = {
        "incident_date": st.date_input("Date of Incident", value=date.today()).strftime("%B %d, %Y"),
        "area": st.text_input("Affected Area", "Basement bathroom"),
        "category": st.radio("Water Intrusion Category", ["Cat 1", "Cat 2", "Cat 3"]),
        "cause": st.text_input("Cause of Damage", "Frozen pipe burst"),
        "scope": st.text_area("Scope of Damage", "Water-damaged drywall, flooring, insulation")
    }

    st.subheader("Repair Details")
    repair = {
        "service_date": st.text_input("Service Dates", "April 21, 2025 – April 22, 2025"),
        "work": st.text_area("Scope of Work", "- Replaced 6ft of pipe\n- Installed insulation"),
        "materials": st.text_area("Materials Used", "- PEX pipe, connectors"),
        "equipment": st.text_area("Equipment Used", "- Pipe cutter, leak detector"),
        "result": st.text_area("Post-Repair Condition", "- No leaks, joints sealed, system operational")
    }

    st.subheader("Invoice Items")
    for idx, item in enumerate(st.session_state.invoice_items):
        with st.expander(f"Item {idx+1}"):
            col1, col2, col3, col4, col5 = st.columns([5, 1, 1, 1.5, 1.5])  # 비율 조정
            with col1:
                item["description"] = st.text_input(f"Description", value=item["description"], key=f"desc{idx}")
            with col2:
                item["qty"] = st.text_input(f"Qty", value=item["qty"], key=f"qty{idx}")
            with col3:
                item["unit"] = st.text_input(f"Unit", value=item["unit"], key=f"unit{idx}")
            with col4:
                item["unit_price"] = st.text_input(f"Unit Price", value=item["unit_price"], key=f"unit_price{idx}")
            with col5:
                item["line_total"] = st.text_input(f"Line Total", value=item["line_total"], key=f"line_total{idx}")


    st.subheader("Payments")
    for idx, payment in enumerate(st.session_state.payments):
        with st.expander(f"Payment {idx+1}"):
            payment["date"] = st.text_input(f"Payment Date {idx}", value=payment["date"], key=f"paydate{idx}")
            payment["amount"] = st.text_input(f"Payment Amount {idx}", value=payment["amount"], key=f"payamount{idx}")

    subtotal = st.text_input("Total Charges", "$0.00")
    total_due = st.text_input("Total Due", "$0.00")

    invoice = {
        "number": st.text_input("Invoice Number", "INV-001"),
        "items": st.session_state.invoice_items,
        "payments": st.session_state.payments,
        "subtotal": subtotal,
        "total_due": total_due
    }

    notes = st.text_area("Notes & Recommendations", "Should any issues arise...")

    report_id = st.text_input("Report ID", "PLM-0424-001")
    report_date = st.date_input("Report Date", value=date.today()).strftime("%B %d, %Y")
    today_str = date.today().strftime("%B %d, %Y")

    submitted = st.form_submit_button("✅ Generate HTML Report")

# --- After form submission ---
if submitted:
    # 줄바꿈 <br> 변환
    repair["work"] = repair["work"].replace("\n", "<br>")
    repair["materials"] = repair["materials"].replace("\n", "<br>")
    repair["equipment"] = repair["equipment"].replace("\n", "<br>")
    repair["result"] = repair["result"].replace("\n", "<br>")
    damage["scope"] = damage["scope"].replace("\n", "<br>")
    notes = notes.replace("\n", "<br>")

    # Load CSS
    with open("templates/plumber_report_style.css", "r", encoding="utf-8") as css_file:
        css_content = css_file.read()

    today_str = date.today().strftime("%B %d, %Y")

    # Dynamic footer CSS
    dynamic_footer_css = f"""
    @page {{
    @bottom-left {{
        content: "Generated on {today_str}";
        font-size: 10px;
    }}
    @bottom-right {{
        content: "Page " counter(page);
        font-size: 10px;
    }}
    }}
    """

    # Combine static CSS + dynamic footer CSS
    final_css = css_content + "\n" + dynamic_footer_css

    # Render template
    template = env.get_template("plumber_report.html")
    html = template.render(
        company=company,
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

    # Save
    with open("rendered_report.html", "w", encoding="utf-8") as f:
        f.write(html)

    st.success("✅ Report generated successfully!")
    st.download_button("⬇️ Download HTML", data=html, file_name="plumber_report.html", mime="text/html")
