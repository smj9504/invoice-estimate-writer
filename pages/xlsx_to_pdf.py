import streamlit as st
import tempfile
import json
import os
from pathlib import Path

from utils.xlsx_to_json import excel_to_estimate_json
from pdf_generator import generate_estimate_pdf

st.set_page_config(page_title="엑셀 → PDF 견적서", layout="centered")
st.title("엑셀 → JSON → PDF 견적서 생성")

uploaded_file = st.file_uploader("엑셀 템플릿 파일 업로드", type=["xlsx"])

if uploaded_file:
    try:
        # 1. 엑셀 파일 임시 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_xlsx:
            tmp_xlsx.write(uploaded_file.read())
            xlsx_path = tmp_xlsx.name

        # 2. 엑셀 → JSON 변환
        json_path = excel_to_estimate_json(xlsx_path, output_dir=tempfile.gettempdir(), filename_by_address=True)

        # 3. JSON 로드
        with open(json_path, "r", encoding="utf-8") as f:
            estimate_data = json.load(f)

        st.success("JSON 변환 완료")
        st.download_button(
            label="JSON 다운로드",
            data=json.dumps(estimate_data, indent=2, ensure_ascii=False),
            file_name=Path(json_path).name,
            mime="application/json"
        )

        # 4. PDF 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pd") as tmp_pdf:
            pdf_path = tmp_pdf.name
            generate_estimate_pdf(estimate_data, pdf_path)

        st.success("PDF 생성 완료")
        with open(pdf_path, "rb") as f:
            st.download_button(
                label="PDF 다운로드",
                data=f,
                file_name=Path(pdf_path).name,
                mime="application/pd"
            )

        # 5. 임시 파일 삭제
        os.remove(xlsx_path)
        os.remove(json_path)

    except Exception as e:
        st.error(f"오류 발생: {e}")
