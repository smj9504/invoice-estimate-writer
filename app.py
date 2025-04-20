# app.py
import streamlit as st

st.set_page_config(page_title="Document Builder", page_icon="📄", layout="wide")
st.title("📂 Document Generator")

st.markdown("견적서 또는 인보이스를 생성하려면 아래에서 선택하세요.")

col1, col2 = st.columns(2)
with col1:
    if st.button("🧾 Create Estimate", use_container_width=True):
        st.switch_page("pages/build_estimate.py")

with col2:
    if st.button("📄 Create Invoice", use_container_width=True):
        #st.switch_page("pages/build_invoice.py")  
        st.warning("페이지가 준비중입니다.")