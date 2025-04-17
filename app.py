import streamlit as st
import tempfile
from pathlib import Path
from pdf_generator import generate_invoice_pdf, generate_estimate_pdf
import json

from sample_data.company_data import COMPANIES

st.set_page_config(page_title="Invoice Generator", page_icon="🧾")
st.title("Invoice Generator")

st.markdown("업로드한 JSON 데이터를 기반으로 견적서 PDF를 생성합니다.")

# 회사 선택
company_name = st.selectbox("🏢 사용할 회사 선택", list(COMPANIES.keys()))
selected_company = COMPANIES[company_name]

# JSON 업로드
uploaded_file = st.file_uploader("견적서 데이터 JSON 업로드", type=["json"])

if uploaded_file:
    context = json.load(uploaded_file)

    if "company" not in context:
        context["company"] = selected_company
        
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        output_path = tmpfile.name
        #generate_invoice_pdf(context, output_path)
        generate_estimate_pdf(context, output_path)

        st.success("PDF 생성 완료!")
        with open(output_path, "rb") as f:
            st.download_button(
                label="견적서 PDF 다운로드",
                data=f,
                file_name="invoice.pdf",
                mime="application/pdf"
            )
