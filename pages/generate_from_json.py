import streamlit as st
import json
import tempfile
from pdf_generator import generate_estimate_pdf, replace_nan_with_zero  # generate_pdf 함수 포함된 모듈
from utils.xlsx_to_json import excel_to_estimate_json
from pathlib import Path
from tempfile import NamedTemporaryFile

st.set_page_config(page_title="Estimate PDF 생성기", layout="centered")
st.title("📄 Excel → JSON Converter")

uploaded_file = st.file_uploader("엑셀 파일 업로드 (.xlsx, 'Estimate_Info'와 'Service_Items' 시트 포함)", type=["xlsx"])

if uploaded_file:
    filename_by_address = st.checkbox("주소 기준으로 파일명 저장", value=True)

    if st.button("변환 실행"):
        with NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        try:
            json_path = excel_to_estimate_json(tmp_path, output_dir=".", filename_by_address=filename_by_address)
            with open(json_path, "r", encoding="utf-8") as f:
                json_content = f.read()

            st.success("JSON 변환 완료!")
            st.download_button(
                label="JSON 파일 다운로드",
                data=json_content,
                file_name=Path(json_path).name,
                mime="application/json"
            )
        except Exception as e:
            st.error(f"변환 중 오류 발생: {e}")


st.title("견적서 JSON → PDF 변환")

uploaded_file = st.file_uploader("견적서 JSON 파일 업로드", type=["json"])

if uploaded_file:
    try:
        # JSON 읽기
        estimate_data = json.load(uploaded_file)
        estimate_data = replace_nan_with_zero(estimate_data)

        # 필수 항목 확인
        required_keys = ["estimate_number", "client", "serviceSections"]
        missing_keys = [key for key in required_keys if key not in estimate_data]
        if missing_keys:
            st.error(f"필수 항목 누락: {', '.join(missing_keys)}")
            st.stop()
        
        # PDF 생성 전에 수치 필드 강제 변환
        for key in ["subtotal", "op_amount", "total", "discount", "op_percent"]:
            try:
                estimate_data[key] = float(estimate_data.get(key, 0))
            except (ValueError, TypeError):
                estimate_data[key] = 0.0

        # 각 section subtotal도 float으로
        for section in estimate_data.get("serviceSections", []):
            try:
                section["subtotal"] = float(section.get("subtotal", 0))
            except (ValueError, TypeError):
                section["subtotal"] = 0.0

        # PDF 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            output_path = tmpfile.name
            generate_estimate_pdf(estimate_data, output_path)

        st.success("PDF가 성공적으로 생성되었습니다.")
        with open(output_path, "rb") as f:
            st.download_button(
                label="PDF 다운로드",
                data=f,
                file_name=f"estimate_{estimate_data.get('estimate_number', 'preview')}.pdf",
                mime="application/pdf"
            )

    except json.JSONDecodeError:
        st.error("JSON 파일 형식이 잘못되었습니다.")
    except Exception as e:
        st.error(f"PDF 생성 중 오류: {e}")
