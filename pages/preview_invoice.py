import streamlit as st
import tempfile
import json
import re
from modules.invoice_module import save_invoice, get_invoice_by_id

st.set_page_config(page_title="Invoice Preview", page_icon="📄", layout="wide")

# JSON 업로드 및 직접 PDF 생성 기능
st.sidebar.header("📂 JSON 업로드")
uploaded_file = st.sidebar.file_uploader("JSON 파일 업로드", type=['json'])

if uploaded_file is not None:
    try:
        # 파일 내용을 문자열로 읽기
        uploaded_file.seek(0)  # 파일 포인터를 처음으로 리셋
        file_content = uploaded_file.read().decode('utf-8')
        json_data = json.loads(file_content)

        st.sidebar.markdown("**업로드된 파일:** " + uploaded_file.name)
        st.sidebar.markdown(f"**인보이스 번호:** {json_data.get('invoice_number', 'N/A')}")

        if st.sidebar.button("📄 바로 PDF 생성 및 다운로드"):
            # JSON 데이터로 직접 PDF 생성
            try:
                from pdf_generator import generate_invoice_pdf

                with tempfile.NamedTemporaryFile(delete=False, suffix=".pd") as tmpfile:
                    generate_invoice_pdf(json_data, tmpfile.name)
                    st.sidebar.success("📄 PDF 생성 완료!")

                    with open(tmpfile.name, "rb") as f:
                        st.sidebar.download_button(
                            label="📥 PDF 다운로드",
                            data=f,
                            file_name=f"{json_data.get('invoice_number', 'invoice')}.pdf",
                            mime="application/pd"
                        )
            except Exception as e:
                st.sidebar.error(f"❌ PDF 생성 실패: {e}")
                st.sidebar.error("🔧 해결방법:")
                st.sidebar.error("1. Streamlit을 종료하세요 (Ctrl+C)")
                st.sidebar.error("2. run_app.bat을 실행하세요")
                st.sidebar.error("3. 또는 CMD에서:")
                st.sidebar.code('set "PATH=C:\\Program Files\\GTK3-Runtime Win64\\bin;%PATH%" && streamlit run app.py')
    except Exception as e:
        st.sidebar.error(f"❌ JSON 파일 처리 오류: {e}")

# 직접 PDF 모드 처리 (build_invoice.py에서 넘어온 경우)
if st.session_state.get("direct_pdf_mode", False):
    # 직접 PDF 생성 모드
    st.title("📄 JSON에서 PDF 생성")

    # 세션 상태에서 JSON 데이터 복원
    invoice_data = {}
    for key in st.session_state.keys():
        if key.startswith("direct_"):
            real_key = key.replace("direct_", "")
            invoice_data[real_key] = st.session_state[key]

    if invoice_data:
        st.subheader("📋 업로드된 인보이스 정보")
        st.json({
            "Invoice No.": invoice_data.get("invoice_number", ""),
            "Date of Issue": invoice_data.get("date_of_issue", ""),
            "Date Due": invoice_data.get("date_due", ""),
            "Client": invoice_data.get("client", {}).get("name", ""),
            "Total": invoice_data.get("total", 0),
            "Tax Type": invoice_data.get("tax_type", "none"),
            "Tax Amount": invoice_data.get("tax_calculated", 0)
        })

        if st.button("📄 PDF 생성 및 다운로드"):
            try:
                from pdf_generator import generate_invoice_pdf

                with tempfile.NamedTemporaryFile(delete=False, suffix=".pd") as tmpfile:
                    generate_invoice_pdf(invoice_data, tmpfile.name)
                    st.success("📄 PDF 생성 완료!")

                    with open(tmpfile.name, "rb") as f:
                        st.download_button(
                            label="📥 PDF 다운로드",
                            data=f,
                            file_name=f"{invoice_data.get('invoice_number', 'invoice')}.pdf",
                            mime="application/pd"
                        )
            except Exception as e:
                st.error(f"❌ PDF 생성 실패: {e}")
                st.error("🔧 해결방법:")
                st.error("1. Streamlit을 종료하세요 (Ctrl+C)")
                st.error("2. run_app.bat을 실행하세요")
                st.error("3. 또는 CMD에서:")
                st.code('set "PATH=C:\\Program Files\\GTK3-Runtime Win64\\bin;%PATH%" && streamlit run app.py')

        if st.button("🔙 인보이스 빌더로 돌아가기"):
            # 직접 PDF 모드 관련 세션 상태 정리
            for key in list(st.session_state.keys()):
                if key.startswith("direct_") or key == "direct_pdf_mode":
                    del st.session_state[key]
            st.switch_page("pages/build_invoice.py")
    else:
        st.error("❌ JSON 데이터를 찾을 수 없습니다.")

    st.stop()  # 일반 미리보기 로직 실행 방지

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

        st.session_state.top_note_preview = data.get("top_note", "")
        st.session_state.bottom_note_preview = data.get("bottom_note", "")
        st.session_state.disclaimer_preview = data.get("disclaimer", "")
        st.session_state.sections = data.get("serviceSections", [])
        st.session_state.payments = data.get("payments", [])
        st.session_state.selected_company = data.get("company", {})

        # 세금 정보 로드
        st.session_state.tax_type = data.get("tax_type", "none")
        st.session_state.tax_rate = data.get("tax_rate", 0.0)
        st.session_state.tax_amount = data.get("tax_amount", 0.0)
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

# 세금 계산
tax_calculated = 0.0
tax_type = st.session_state.get("tax_type_preview", st.session_state.get("tax_type", "none"))
tax_rate = st.session_state.get("tax_rate_preview", st.session_state.get("tax_rate", 0.0))
tax_amount = st.session_state.get("tax_amount_preview", st.session_state.get("tax_amount", 0.0))

if tax_type == "percentage" and tax_rate > 0:
    tax_calculated = round((subtotal_total * tax_rate / 100), 2)
elif tax_type == "fixed" and tax_amount > 0:
    tax_calculated = tax_amount

total_with_tax = round(subtotal_total + tax_calculated, 2)
paid_total = round(sum(p["amount"] for p in st.session_state.get("payments", [])), 2)
total_due = round(total_with_tax - paid_total, 2)

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
    "discount": 0.0,
    "tax_type": tax_type,
    "tax_rate": tax_rate,
    "tax_amount": tax_amount,
    "tax_calculated": tax_calculated,
    "total_with_tax": total_with_tax
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
        st.markdown(f"- **{item['name']}**")

        if not item.get("hide_price"):
            st.markdown(f"  - 수량: {item['qty']} {item['unit']} | 단가: ${item['price']:,.2f}")

        if item.get("dec"):
            st.markdown(f"  - _{item['dec']}_")

    st.markdown(f"<p style='text-align:right; font-weight:bold;'>Subtotal: ${section['subtotal']:,.2f}</p>",
        unsafe_allow_html=True)

# 납부 내역
st.subheader("💳 납부 내역")
for p in invoice_data["payments"]:  # 기존: st.session_state.payments
    if p.get("date"):
        st.markdown(f"- <span style='color:gray; font-style:italic;'>{p['date']}</span> : <strong>${p['amount']:,.2f}</strong>", unsafe_allow_html=True)
    else:
        st.markdown(f"- <strong>${p['amount']:,.2f}</strong>", unsafe_allow_html=True)

# 세금 정보 표시
if invoice_data['tax_calculated'] > 0:
    st.subheader("💸 세금 정보")
    if invoice_data['tax_type'] == "percentage":
        st.markdown(f"**세금율**: {invoice_data['tax_rate']}%")
    st.markdown(f"**세금**: ${invoice_data['tax_calculated']:,.2f}")
    st.markdown(f"**Total with Tax**: ${invoice_data['total_with_tax']:,.2f}")

# Total
st.markdown(f"<h4 style='text-align:right;'>💰 Total Due: ${invoice_data['total']:,.2f}</h4>", unsafe_allow_html=True)

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
    try:
        from pdf_generator import generate_invoice_pdf

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pd") as tmpfile:
            generate_invoice_pdf(invoice_data, tmpfile.name)
            st.success("📄 PDF 생성 완료!")
            with open(tmpfile.name, "rb") as f:
                st.download_button(
                    label="📥 PDF 다운로드",
                    data=f,
                    file_name=f"{invoice_data['invoice_number']}.pdf",
                    mime="application/pd"
                )
            for key in list(st.session_state.keys()):
                del st.session_state[key]
    except Exception as e:
        st.error(f"❌ PDF 생성 실패: {e}")
        st.error("🔧 해결방법:")
        st.error("1. Streamlit을 종료하세요 (Ctrl+C)")
        st.error("2. run_app.bat을 실행하세요")
        st.error("3. 또는 CMD에서:")
        st.code('set "PATH=C:\\Program Files\\GTK3-Runtime Win64\\bin;%PATH%" && streamlit run app.py')
