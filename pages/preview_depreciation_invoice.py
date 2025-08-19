import streamlit as st
import tempfile
import json
import re
from pdf_generator import generate_invoice_pdf, generate_depreciation_invoice_pdf  # 새 함수 import 추가
from modules.invoice_module import save_invoice, get_invoice_by_id

st.set_page_config(page_title="Invoice Preview", page_icon="📄", layout="wide")

# URL 파라미터에서 ID 추출
query_params = st.query_params
raw_id = query_params.get("id")
invoice_id = raw_id[0] if isinstance(raw_id, list) else raw_id

uuid_pattern = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")

if invoice_id and uuid_pattern.match(invoice_id):
    invoice = get_invoice_by_id(invoice_id)
    if invoice:
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

        st.session_state.top_note_preview = data.get("top_note", "")
        st.session_state.bottom_note_preview = data.get("bottom_note", "")
        st.session_state.disclaimer_preview = data.get("disclaimer", "")
        st.session_state.sections = data.get("serviceSections", [])
        st.session_state.payments = data.get("payments", [])
        st.session_state.selected_company = data.get("company", {})
    else:
        st.error("❌ 해당 ID의 인보이스를 찾을 수 없습니다.")
elif invoice_id:
    st.error("❌ 유효하지 않은 인보이스 ID 형식입니다.")
else:
    st.info("ℹ️ 인보이스 ID가 제공되지 않았습니다.")

st.title("📄 인보이스 미리보기")

if st.button("🔙 수정하기"):
    st.switch_page("pages/build_invoice.py")

# 필수 데이터 확인
if "sections" not in st.session_state or not st.session_state.sections:
    st.warning("⛔ 먼저 인보이스를 작성해 주세요.")
    st.stop()

subtotal_total = round(sum(section["subtotal"] for section in st.session_state.sections), 2)
line_item_total = st.session_state.get("line_item_total", 0.0)
material_sales_tax = st.session_state.get("material_sales_tax", 0.0)
grand_total = round(subtotal_total + line_item_total + material_sales_tax, 2)
paid_total = round(sum(p["amount"] for p in st.session_state.get("payments", [])), 2)
total_due = round(grand_total - paid_total, 2)

# 보험 정보 조립
insurance_data = {}
if (st.session_state.get("insurance_company") or
    st.session_state.get("insurance_policy_number") or
    st.session_state.get("insurance_claim_number")):
    insurance_data = {
        "company": st.session_state.get("insurance_company", ""),
        "policy_number": st.session_state.get("insurance_policy_number", ""),
        "claim_number": st.session_state.get("insurance_claim_number", "")
    }

# JSON 데이터 조립
invoice_data = {
    "invoice_number": st.session_state.get("invoice_number", ""),
    "date_of_issue": str(st.session_state.get("date_of_issue", "")),
    "date_due": str(st.session_state.get("date_due", "")),
    "company": st.session_state.get("selected_company", {}),
    "client": {
        "name": st.session_state.get("client_name", ""),
        "phone": st.session_state.get("client_phone", ""),
        "email": st.session_state.get("client_email", ""),
        "address": st.session_state.get("client_street", ""),
        "city": st.session_state.get("client_city", ""),
        "state": st.session_state.get("client_state", ""),
        "zip": st.session_state.get("client_zip", "")
    },
    "client_type": st.session_state.get("client_type", "individual"),
    "insurance": insurance_data,
    "amount_due_text": st.session_state.get("amount_due_text", ""),
    "line_item_total": line_item_total,
    "material_sales_tax": material_sales_tax,
    "top_note": st.session_state.get("top_note_preview", ""),
    "disclaimer": st.session_state.get("disclaimer_preview", ""),
    "bottom_note": st.session_state.get("bottom_note_preview", ""),
    "serviceSections": st.session_state.sections,
    "total": total_due,
    "subtotal_total": grand_total,  # 전체 총계 (섹션 + Line Item + Tax)
    "payments": st.session_state.get("payments", []),
    "discount": 0.0
}

# ✅ UI 표시
st.subheader("🏢 회사 정보")
st.json(invoice_data["company"])

st.subheader("👤 고객 정보")
client_display = invoice_data["client"].copy()
client_display["client_type"] = invoice_data["client_type"]
st.json(client_display)

# 보험 정보 표시
if insurance_data:
    st.subheader("🏥 보험 정보")
    st.json(insurance_data)

st.subheader("📑 인보이스 정보")
invoice_info = {
    "Invoice No.": invoice_data["invoice_number"],
    "Date of Issue": invoice_data["date_of_issue"],
    "Date Due": invoice_data["date_due"],
}
if invoice_data["amount_due_text"]:
    invoice_info["Custom Amount Due Text"] = invoice_data["amount_due_text"]

st.json(invoice_info)

st.subheader("📝 상단 Note")
if invoice_data["top_note"]:
    st.markdown(invoice_data["top_note"])
else:
    st.markdown("_(작성된 내용 없음)_")

st.markdown("---")
st.subheader("📦 항목 목록")
for section in invoice_data["serviceSections"]:
    # 섹션 제목과 금액 표시
    section_title = f"### 🔹 {section['title']}"
    if section.get("amount", 0) > 0:
        section_title += f" - ${section['amount']:,.2f}"
    st.markdown(section_title)

    for item in section["items"]:
        st.markdown(f"- **{item['name']}**")

        # 개별 아이템 금액 표시
        if item.get("amount", 0) > 0:
            st.markdown(f"  - 금액: ${item['amount']:,.2f}")
        elif not item.get("hide_price"):
            st.markdown(f"  - 수량: {item.get('qty', 0)} {item.get('unit', '')} | 단가: ${item.get('price', 0):,.2f}")

        # Description 표시 (새로운 형식과 기존 형식 모두 지원)
        if item.get("description") and isinstance(item["description"], list):
            st.markdown("  - 작업 내역:")
            for desc_line in item["description"]:
                st.markdown(f"    - {desc_line}")
        elif item.get("dec"):
            st.markdown(f"  - _{item['dec']}_")

    st.markdown(f"<p style='text-align:right; font-weight:bold;'>Subtotal: ${section['subtotal']:,.2f}</p>",
        unsafe_allow_html=True)

# 납부 내역
st.subheader("💳 납부 내역")
if invoice_data["payments"]:
    for p in invoice_data["payments"]:
        payment_text = ""

        # Payment 이름 표시
        if p.get("name"):
            payment_text += f"**{p['name']}**"

        # Payment 날짜 표시
        if p.get("date"):
            date_part = f" <span style='color:gray; font-style:italic;'>({p['date']})</span>"
            payment_text += date_part

        # Payment 금액 표시
        payment_text += f" : <strong>${p['amount']:,.2f}</strong>"

        st.markdown(f"- {payment_text}", unsafe_allow_html=True)
else:
    st.markdown("_(납부 내역 없음)_")

# Total
st.markdown("---")
st.markdown(f"<h4 style='text-align:right;'>Sections Subtotal: ${subtotal_total:,.2f}</h4>", unsafe_allow_html=True)
if line_item_total > 0:
    st.markdown(f"<h4 style='text-align:right;'>Line Item Total: ${line_item_total:,.2f}</h4>", unsafe_allow_html=True)
if material_sales_tax > 0:
    st.markdown(f"<h4 style='text-align:right;'>Material Sales Tax: ${material_sales_tax:,.2f}</h4>",
        unsafe_allow_html=True)
st.markdown(f"<h4 style='text-align:right;'>Grand Total: ${grand_total:,.2f}</h4>", unsafe_allow_html=True)
if paid_total > 0:
    st.markdown(f"<h4 style='text-align:right;'>Total Paid: ${paid_total:,.2f}</h4>", unsafe_allow_html=True)
st.markdown(f"<h4 style='text-align:right;'>💰 Amount Due: ${invoice_data['total']:,.2f}</h4>", unsafe_allow_html=True)

# 하단
st.subheader("📌 하단 Note 및 고지사항")
if invoice_data.get('bottom_note'):
    st.markdown(f"**Note**: {invoice_data['bottom_note']}")
else:
    st.markdown("**Note**: _없음_")

if invoice_data.get('disclaimer'):
    st.markdown(f"**Disclaimer**: {invoice_data['disclaimer']}")
else:
    st.markdown("**Disclaimer**: _없음_")

# JSON 다운로드
st.download_button(
    label="📁 JSON 다운로드",
    data=json.dumps(invoice_data, indent=2, ensure_ascii=False),
    file_name="invoice.json",
    mime="application/json"
)

# 작성한 인보이스정보 DB에 저장
if st.button("💾 인보이스 저장"):
    response = save_invoice(invoice_data)
    if response:
        st.success("✅ 인보이스가 저장되었습니다!")

# PDF 생성 버튼들
col1, col2 = st.columns(2)

with col1:
    if st.button("📄 기본 인보이스 PDF 다운로드"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pd") as tmpfile:
            generate_invoice_pdf(invoice_data, tmpfile.name)
            st.success("📄 기본 PDF 생성 완료!")
            with open(tmpfile.name, "rb") as f:
                st.download_button(
                    label="📥 기본 PDF 다운로드",
                    data=f,
                    file_name=f"{invoice_data['invoice_number']}_basic.pdf",
                    mime="application/pd"
                )

with col2:
    if st.button("🏗️ 건설업 인보이스 PDF 다운로드"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pd") as tmpfile:
            generate_depreciation_invoice_pdf(invoice_data, tmpfile.name)
            st.success("🏗️ 건설업 PDF 생성 완료!")
            with open(tmpfile.name, "rb") as f:
                st.download_button(
                    label="📥 건설업 PDF 다운로드",
                    data=f,
                    file_name=f"{invoice_data['invoice_number']}_WC.pdf",
                    mime="application/pd"
                )

# 세션 상태 초기화 (PDF 다운로드 후)
if st.button("🔄 새 인보이스 작성하기"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()
