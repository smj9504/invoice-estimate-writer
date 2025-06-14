import streamlit as st
import json
import tempfile
import pandas as pd
from pdf_generator import generate_estimate_pdf, replace_nan_with_zero  # generate_pdf 함수 포함된 모듈
from utils.xlsx_to_json import excel_to_estimate_json
from pathlib import Path
from tempfile import NamedTemporaryFile

st.set_page_config(page_title="Estimate PDF 생성기", layout="centered")

# Excel to JSON 변환 섹션
st.title("📄 Excel → JSON Converter")

excel_file = st.file_uploader("엑셀 파일 업로드 (.xlsx, 'Estimate_Info'와 'Service_Items' 시트 포함)", 
                             type=["xlsx"], key="excel_uploader")

if excel_file:
    filename_by_address = st.checkbox("주소 기준으로 파일명 저장", value=True)
    
    if st.button("변환 실행"):
        with NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp.write(excel_file.read())
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
            
            # 변환된 JSON 내용 미리보기 (선택사항)
            with st.expander("변환된 JSON 미리보기"):
                st.json(json.loads(json_content))
                
        except Exception as e:
            st.error(f"변환 중 오류 발생: {e}")
            st.write("**오류 세부사항:**")
            st.exception(e)
            
            # 디버깅을 위한 추가 정보
            with st.expander("디버깅 정보"):
                try:
                    # 엑셀 파일의 시트 정보 확인
                    df_info = pd.read_excel(tmp_path, sheet_name="Estimate_Info", engine="openpyxl")
                    df_items = pd.read_excel(tmp_path, sheet_name="Service_Items", engine="openpyxl")
                    
                    st.write("**Estimate_Info 시트 정보:**")
                    st.dataframe(df_info.head())
                    
                    st.write("**Service_Items 시트 정보:**")
                    st.dataframe(df_items.head())
                    
                except Exception as debug_e:
                    st.write(f"엑셀 파일 읽기 오류: {debug_e}")

# 구분선 추가
st.divider()

# JSON to PDF 변환 섹션
st.title("📋 견적서 JSON → PDF 변환")

json_file = st.file_uploader("견적서 JSON 파일 업로드", type=["json"], key="json_uploader")

if json_file:
    try:
        # JSON 읽기
        estimate_data = json.load(json_file)
        estimate_data = replace_nan_with_zero(estimate_data)
        
        # JSON 내용 미리보기
        with st.expander("업로드된 JSON 미리보기"):
            st.json(estimate_data)
        
        # 필수 항목 확인
        required_keys = ["estimate_number", "client", "serviceSections"]
        missing_keys = [key for key in required_keys if key not in estimate_data]
        if missing_keys:
            st.error(f"필수 항목 누락: {', '.join(missing_keys)}")
            st.write("**필요한 JSON 구조:**")
            st.code("""{
  "estimate_number": "견적서 번호",
  "client": {
    "name": "고객명",
    "address": "주소"
  },
  "serviceSections": [
    {
      "title": "섹션 제목",
      "items": [...]
    }
  ]
}""", language="json")
            st.stop()
        
        # PDF 생성 전에 수치 필드 강제 변환
        numeric_fields = ["subtotal", "op_amount", "total", "discount", "op_percent"]
        for key in numeric_fields:
            try:
                value = estimate_data.get(key, 0)
                if pd.isna(value) or value is None:
                    estimate_data[key] = 0.0
                else:
                    estimate_data[key] = float(value)
            except (ValueError, TypeError):
                estimate_data[key] = 0.0
        
        # 각 section subtotal도 float으로
        for section in estimate_data.get("serviceSections", []):
            try:
                value = section.get("subtotal", 0)
                if pd.isna(value) or value is None:
                    section["subtotal"] = 0.0
                else:
                    section["subtotal"] = float(value)
            except (ValueError, TypeError):
                section["subtotal"] = 0.0
        
        # PDF 생성 버튼
        if st.button("PDF 생성", type="primary"):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
                    output_path = tmpfile.name
                    generate_estimate_pdf(estimate_data, output_path)
                
                st.success("PDF가 성공적으로 생성되었습니다! 🎉")
                
                with open(output_path, "rb") as f:
                    st.download_button(
                        label="📥 PDF 다운로드",
                        data=f,
                        file_name=f"estimate_{estimate_data.get('estimate_number', 'preview')}.pdf",
                        mime="application/pdf",
                        type="primary"
                    )
            except Exception as pdf_e:
                st.error(f"PDF 생성 중 오류: {pdf_e}")
                st.write("**오류 세부사항:**")
                st.exception(pdf_e)
    
    except json.JSONDecodeError as json_e:
        st.error("JSON 파일 형식이 잘못되었습니다.")
        st.write(f"JSON 파싱 오류: {json_e}")
        
        # JSON 수정 도움말
        with st.expander("JSON 형식 도움말"):
            st.write("JSON 파일이 올바른 형식인지 확인하세요:")
            st.write("- 모든 따옴표가 쌍으로 닫혔는지")
            st.write("- 중괄호 {} 와 대괄호 []가 올바르게 매칭되는지")
            st.write("- 마지막 항목 뒤에 쉼표가 없는지")
            
    except Exception as e:
        st.error(f"파일 처리 중 오류: {e}")
        st.write("**오류 세부사항:**")
        st.exception(e)

# 사이드바에 도움말 추가
with st.sidebar:
    st.header("📖 사용 가이드")
    st.write("""
    **Excel → JSON 변환:**
    1. Excel 파일에 'Estimate_Info'와 'Service_Items' 시트가 있어야 합니다
    2. 파일을 업로드하고 '변환 실행' 버튼을 클릭하세요
    
    **JSON → PDF 변환:**
    1. 변환된 JSON 파일을 업로드하세요
    2. 'PDF 생성' 버튼을 클릭하여 견적서를 생성하세요
    """)
    
    st.header("🛠️ 문제해결")
    st.write("""
    - **'float' object has no attribute 'strip'**: Excel의 빈 셀 문제 - 수정된 코드로 해결됩니다
    - **시트를 찾을 수 없음**: Excel 파일의 시트명을 확인하세요
    - **JSON 형식 오류**: JSON 구조가 올바른지 확인하세요
    """)