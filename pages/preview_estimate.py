import streamlit as st
import tempfile
import json
from pdf_generator import generate_estimate_pdf 

st.set_page_config(page_title="Estimate Preview", page_icon="🧾", layout="wide")
st.title("📄 견적서 미리보기")

if st.button("🔙 돌아가기"):
    st.switch_page("pages/build_estimate.py")

# 필수 데이터 확인
if "sections" not in st.session_state or not st.session_state.sections:
    st.warning("⛔ 먼저 견적서를 작성해 주세요.")
    st.stop()


# JSON 데이터 조립
estimate_data = {
    "estimate_number": st.session_state.get("estimate_number", ""),
    "estimate_date": str(st.session_state.get("estimate_date", "")),
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
    "disclaimer": st.session_state.get("disclaimer_preview", ""),
    "bottom_note": st.session_state.get("bottom_note_preview", ""),
    "serviceSections": st.session_state.sections,
    "total": round(sum(section["subtotal"] for section in st.session_state.sections), 2),
    "discount": 0.0  # 추후 지원 가능
}

# 상단 정보
st.subheader("🏢 회사 정보")
st.json(st.session_state.get("selected_company"))

st.subheader("👤 고객 정보")
client_info = {
    "고객명": st.session_state.get("client_name"),
    "전화번호": st.session_state.get("client_phone"),
    "이메일": st.session_state.get("client_email"),
    "Street": st.session_state.get("client_street"),
    "City": st.session_state.get("client_city"),
    "State": st.session_state.get("client_state"),
    "Zipcode": st.session_state.get("client_zip"),
}
st.json(client_info)

st.subheader("견적 정보")
estimate_info = {
    "견적서 정보": st.session_state.get("estimate_number"),
    "작성일일": st.session_state.get("estimate_date"),
}
st.json(estimate_info)

st.subheader("📝 상단 Note")
st.markdown(st.session_state.get("top_note_preview", "_(작성된 내용 없음)_"))

# 섹션별 아이템 및 subtotal
st.markdown("---")
st.subheader("📦 견적 항목")
for section in st.session_state.sections:
    st.markdown(f"### 🔹 {section['title']}")
    for item in section["items"]:
        st.markdown(f"- **{item['name']}** | 수량: {item['qty']} {item['unit']} | 단가: ${item['price']:,.2f}")
        if item.get("dec"):
            st.markdown(f"  - _{item['dec']}_")
    st.markdown(f"<p style='text-align:right; font-weight:bold;'>Subtotal: ${section['subtotal']:,.2f}</p>", unsafe_allow_html=True)

# 전체 Total
total = round(sum(section["subtotal"] for section in st.session_state.sections), 2)
st.markdown(f"<h4 style='text-align:right;'>💰 Total: ${total:,.2f}</h4>", unsafe_allow_html=True)

# 하단 note & disclaimer
st.subheader("📌 하단 Note 및 Disclaimer")
st.markdown(f"**Note**: {st.session_state.get('bottom_note_preview', '_없음_')}")
st.markdown(f"**Disclaimer**: {st.session_state.get('disclaimer_preview', '_없음_')}")

# JSON 파일 다운로드
st.download_button(
    label="JSON 다운로드",
    data=json.dumps(estimate_data, indent=2, ensure_ascii=False),
    file_name="estimate.json",
    mime="application/json"
)

if st.button("📄 견적서 PDF 다운로드"):
    # 1. JSON 파일 생성
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w", encoding="utf-8") as json_file:
        json.dump(estimate_data, json_file, ensure_ascii=False, indent=2)
        json_path = json_file.name

    # 2. context 로드
    with open(json_path, "r", encoding="utf-8") as f:
        context = json.load(f)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        output_path = tmpfile.name
        generate_estimate_pdf(context, output_path)

        st.success("PDF 생성 완료!")
        with open(output_path, "rb") as f:
            st.download_button(
                label="견적서 PDF 다운로드",
                data=f,
                file_name="invoice.pdf",
                mime="application/pdf"
            )