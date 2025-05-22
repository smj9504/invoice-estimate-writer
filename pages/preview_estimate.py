import streamlit as st
import tempfile
import json
import re
from pdf_generator import generate_estimate_pdf 
from modules.estimate_module import save_estimate, get_estimate_by_id

st.set_page_config(page_title="Estimate Preview", page_icon="🧾", layout="wide")
st.title("📄 견적서 미리보기")

# URL 파라미터에서 ID 추출
query_params = st.query_params
raw_id = query_params.get("id")
estimate_id = raw_id[0] if isinstance(raw_id, list) else raw_id

uuid_pattern = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")

if estimate_id and uuid_pattern.match(estimate_id):
    estimate = get_estimate_by_id(estimate_id)
    if estimate:
        data = estimate.get("json_data", {})
        st.session_state.selected_company = data.get("company", {})

        st.session_state.estimate_number = data.get("estimate_number", "")
        st.session_state.estimate_date = data.get("estimate_date", "")

        client = data.get("client", {})
        st.session_state.client_name = client.get("name", "")
        st.session_state.client_phone = client.get("phone", "")
        st.session_state.client_email = client.get("email", "")
        st.session_state.client_street = client.get("address", "")
        st.session_state.client_city = client.get("city", "")
        st.session_state.client_state = client.get("state", "")
        st.session_state.client_zip = client.get("zip", "")

        st.session_state.sections = data.get("serviceSections", [])
        st.session_state.top_note_preview = data.get("top_note", "")
        st.session_state.bottom_note_preview = data.get("bottom_note", "")
        st.session_state.disclaimer_preview = data.get("disclaimer", "")
        
        st.session_state.op_percent_preview = data.get("op_percent", "")
        st.session_state.op_amount_preview = data.get("op_amount", "")
        st.session_state.total_preview = data.get("toptal", "")
    else:
        st.error("❌ 해당 ID의 견적서를 찾을 수 없습니다.")
elif estimate_id:
    st.error("❌ 유효하지 않은 견적서 ID 형식입니다.")
else:
    st.info("ℹ️ 견적서 ID가 제공되지 않았습니다.")

if st.button("🔙 수정하기"):
    st.switch_page("pages/build_estimate.py")

# 필수 데이터 확인
if "sections" not in st.session_state or not st.session_state.sections:
    st.warning("⛔ 먼저 견적서를 작성해 주세요.")
    st.stop()

# O&P 값 가져오기
op_percent = st.session_state.get("op_percent_preview", 0.0)
op_amount = st.session_state.get("op_amount_preview", 0.0)

# subtotal 합산
subtotal = round(sum(section["subtotal"] for section in st.session_state.sections), 2)

# 총합 계산
total = round(subtotal + op_amount, 2)

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

    "op_percent": op_percent,
    "op_amount": op_amount,
    "subtotal": subtotal,
    "total": total,
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
    "작성일": st.session_state.get("estimate_date"),
}
st.json(estimate_info)

st.subheader("📝 상단 Note")
top_note = st.session_state.get("top_note_preview", "_(작성된 내용 없음)_").replace("\n", "<br>")
st.markdown(top_note, unsafe_allow_html=True)

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
st.markdown(f"""
<h4 style='text-align:right;'>Subtotal: ${subtotal:,.2f}</h4>
<h4 style='text-align:right;'>O&amp;P ({op_percent:.0f}%): ${op_amount:,.2f}</h4>
<h3 style='text-align:right; font-weight:bold;'>💰 Total: ${total:,.2f}</h3>
""", unsafe_allow_html=True)

# 하단 note & disclaimer
st.subheader("📌 하단 Note 및 Disclaimer")
note_text = st.session_state.get("bottom_note_preview", "_없음_").replace("\n", "<br>")
disclaimer_text = st.session_state.get("disclaimer_preview", "_없음_").replace("\n", "<br>")

st.markdown(f"**Note**:<br>{note_text}", unsafe_allow_html=True)
st.markdown(f"**Disclaimer**:<br>{disclaimer_text}", unsafe_allow_html=True)

# JSON 파일 다운로드
st.download_button(
    label="JSON 다운로드",
    data=json.dumps(estimate_data, indent=2, ensure_ascii=False),
    file_name="estimate.json",
    mime="application/json"
)

if st.button("💾 견적서 저장"):
    success = save_estimate(estimate_data)
    if success:
        st.success("✅ 견적서가 저장되었습니다!")
    else:
        st.error("❌ 저장 중 오류가 발생했습니다.")


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
                file_name="estimate.pdf",
                mime="application/pdf"
            )