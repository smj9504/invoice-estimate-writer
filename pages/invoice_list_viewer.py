import streamlit as st
import datetime
import json
from modules.invoice_module import get_latest_invoices
from modules.company_module import get_all_companies

st.set_page_config(page_title="🧾 인보이스 목록", page_icon="🧾", layout="wide")
st.title("🧾 인보이스 목록")

# 전체 인보이스 불러오기
all_invoices = get_latest_invoices()

# 회사 목록 가져오기
companies = get_all_companies()
company_options = ["전체"] + [c["name"] for c in companies]
selected_company = st.selectbox("🏢 회사 선택", company_options)

# 날짜 필터
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("시작일", value=datetime.date.today() - datetime.timedelta(days=30))
with col2:
    end_date = st.date_input("종료일", value=datetime.date.today())

# 검색어 필터
search_query = st.text_input("🔍 검색어 (고객명, 주소, 아이템명 등)")

# 필터링
filtered_invoices = []
for inv in all_invoices:
    created_at = datetime.datetime.fromisoformat(inv["created_at"]).date()
    if not (start_date <= created_at <= end_date):
        continue

    if selected_company != "전체":
        company = inv.get("data", {}).get("company", {})
        if company.get("name") != selected_company:
            continue

    if search_query:
        data = inv.get("data", {})
        if not any(
            search_query.lower() in str(v).lower()
            for v in [
                data.get("client", {}).get("name"),
                data.get("client", {}).get("address"),
                json.dumps(data.get("serviceSections", []))
            ]
        ):
            continue

    filtered_invoices.append(inv)

# 결과 출력
st.markdown(f"### 🔎 총 {len(filtered_invoices)}건 결과")
for inv in filtered_invoices:
    data = inv["data"]
    st.markdown("---")
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"**회사**: {data['company'].get('name')}  ")
        st.markdown(f"**고객**: {data['client'].get('name')}  ")
        st.markdown(f"**주소**: {data['client'].get('address')}  ")
        st.markdown(f"**날짜**: {inv['created_at'][:10]}")
    with col2:
        st.link_button("👁️ 미리보기", url=f"/preview_invoice?id={inv['id']}")
        st.link_button("✏️ 수정하기", url=f"/build_invoice?id={inv['id']}")
