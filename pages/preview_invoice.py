import streamlit as st
import tempfile
import json
from pdf_generator import generate_invoice_pdf
from modules.invoice_module import save_invoice


st.set_page_config(page_title="Invoice Preview", page_icon="📄", layout="wide")
st.title("📄 인보이스 미리보기")

if st.button("🔙 돌아가기"):
    st.switch_page("pages/build_invoice.py")

# 필수 데이터 확인
if "sections" not in st.session_state or not st.session_state.sections:
    st.warning("⛔ 먼저 인보이스를 작성해 주세요.")
    st.stop()

subtotal_total = round(sum(section["subtotal"] for section in st.session_state.sections), 2)
paid_total = round(sum(p["amount"] for p in st.session_state.get("payments", [])), 2)
total_due = round(subtotal_total - paid_total, 2)

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
    "top_note": st.session_state.get("top_note_preview", ""),
    "disclaimer": st.session_state.get("disclaimer_preview", "").replace("\n", "<br>"),
    "bottom_note": st.session_state.get("bottom_note_preview", "").replace("\n", "<br>"),
    "serviceSections": st.session_state.sections,
    "total": total_due,
    "subtotal_total": subtotal_total,
    "payments": st.session_state.get("payments", []),
    "discount": 0.0
}

# ✅ UI 표시
st.subheader("🏢 회사 정보")
st.json(invoice_data["company"])

st.subheader("👤 고객 정보")
st.json(invoice_data["client"])

st.subheader("📑 인보이스 정보")
st.json({
    "Invoice No.": invoice_data["invoice_number"],
    "Date of Issue": invoice_data["date_of_issue"],
    "Date Due": invoice_data["date_due"],
})

st.subheader("📝 상단 Note")
st.markdown(invoice_data["top_note"] or "_(작성된 내용 없음)_")

st.markdown("---")
st.subheader("📦 항목 목록")
for section in invoice_data["serviceSections"]:
    st.markdown(f"### 🔹 {section['title']}")
    for item in section["items"]:
        st.markdown(f"- **{item['name']}** | 수량: {item['qty']} {item['unit']} | 단가: ${item['price']:,.2f}")
        if item.get("dec"):
            st.markdown(f"  - _{item['dec']}_")
    st.markdown(f"<p style='text-align:right; font-weight:bold;'>Subtotal: ${section['subtotal']:,.2f}</p>", unsafe_allow_html=True)

# 납부 내역
st.subheader("💳 납부 내역")
for p in invoice_data["payments"]:  # 기존: st.session_state.payments
    if p.get("date"):
        st.markdown(f"- <span style='color:gray; font-style:italic;'>{p['date']}</span> : <strong>${p['amount']:,.2f}</strong>", unsafe_allow_html=True)
    else:
        st.markdown(f"- <strong>${p['amount']:,.2f}</strong>", unsafe_allow_html=True)

# Total
st.markdown(f"<h4 style='text-align:right;'>💰 Total: ${invoice_data['total']:,.2f}</h4>", unsafe_allow_html=True)

# 하단
st.subheader("📌 하단 Note 및 고지사항")
st.markdown(f"**Note**: {invoice_data.get('bottom_note', '_없음_')}")
st.markdown(f"**Disclaimer**: {invoice_data.get('disclaimer', '_없음_')}")

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

# PDF 생성 버튼
if st.button("📄 인보이스 PDF 다운로드"):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        generate_invoice_pdf(invoice_data, tmpfile.name)
        st.success("📄 PDF 생성 완료!")
        with open(tmpfile.name, "rb") as f:
            st.download_button(
                label="📥 PDF 다운로드",
                data=f,
                file_name=f"{invoice_data['invoice_number']}.pdf",
                mime="application/pdf"
            )
