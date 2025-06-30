import re
from typing import Dict, List, Tuple, Optional
import logging
import os
from openai import OpenAI
import base64
import json

logger = logging.getLogger(__name__)

def init_openai_client():
    """OpenAI 클라이언트를 초기화합니다."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
    
    return OpenAI(api_key=api_key)

def safe_float(value, default=0.0):
    """안전하게 float로 변환합니다."""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

class ImprovedAIImageAnalyzer:
    """개선된 AI 이미지 분석기 - 정확도 향상"""
    
    def __init__(self, openai_client):
        self.client = openai_client
    
    def analyze_construction_image(self, uploaded_file, room_name: str = "", room_type_hint: str = ""):
        """건축 이미지를 분석합니다 - 2단계 접근법"""
        try:
            logger.info(f"=== 개선된 AI 이미지 분석 시작 ===")
            
            # 파일에서 바이트 데이터 읽기
            if hasattr(uploaded_file, 'read'):
                image_bytes = uploaded_file.read()
                uploaded_file.seek(0)
            else:
                image_bytes = uploaded_file
            
            # base64로 인코딩
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            
            # 1단계: 텍스트 추출 및 검증
            text_analysis = self._extract_text_with_verification(base64_image)
            
            # 2단계: 구조화된 데이터 추출
            structured_analysis = self._extract_structured_data(
                base64_image, text_analysis, room_name, room_type_hint
            )
            
            # 3단계: 교차 검증 및 보정
            final_result = self._cross_validate_and_correct(text_analysis, structured_analysis)
            
            return final_result
            
        except Exception as e:
            logger.error(f"이미지 분석 중 치명적 오류: {str(e)}")
            return self._get_error_result(str(e))
    
    def _extract_text_with_verification(self, base64_image: str) -> Dict:
        """1단계: 텍스트 추출 및 검증"""
        prompt = """
        이 이미지에서 모든 텍스트를 정확히 읽어서 추출해주세요.
        
        **중요: 반드시 유효한 JSON 형태로만 응답하세요.**
        
        다음 형태로 응답해주세요:
        
        {
            "all_text_lines": [
                "이미지에서 읽은 모든 텍스트 라인들",
                "각 라인을 정확히 그대로 적어주세요"
            ],
            "room_info": {
                "room_name": "읽은 방 이름",
                "ceiling_height": "읽은 천장 높이",
                "total_lines_found": 숫자
            },
            "measurements_found": {
                "floor_area_sf": 숫자_또는_null,
                "wall_area_sf": 숫자_또는_null,
                "ceiling_area_sf": 숫자_또는_null,
                "perimeter_lf": 숫자_또는_null,
                "ceiling_perimeter_lf": 숫자_또는_null
            },
            "openings_found": [
                {
                    "type": "Door/Window/Missing Wall 등",
                    "text": "원본 텍스트",
                    "size_info": "크기 정보 (예: 3'0\" x 6'8\")",
                    "connection": "연결된 곳 (Goes to, Opens into 등)"
                }
            ],
            "verification": {
                "total_doors_counted": 숫자,
                "total_windows_counted": 숫자,
                "total_open_areas_counted": 숫자,
                "confidence_level": "high/medium/low"
            }
        }
        
        **읽기 지침:**
        1. 모든 텍스트를 빠뜨리지 말고 읽어주세요
        2. 숫자와 단위(SF, LF 등)를 정확히 읽어주세요
        3. Door, Window, Missing Wall 등을 정확히 구분해주세요
        4. 크기 정보(3'0" x 6'8" 등)를 정확히 읽어주세요
        5. JSON 외의 다른 텍스트는 출력하지 마세요
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=2000
        )
        
        try:
            result_text = response.choices[0].message.content
            # JSON 추출 및 파싱
            json_start = result_text.find('{')
            json_end = result_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = result_text[json_start:json_end]
                return json.loads(json_str)
            else:
                logger.error("텍스트 추출에서 JSON을 찾을 수 없음")
                return {"error": "JSON 파싱 실패", "raw_text": result_text}
                
        except json.JSONDecodeError as e:
            logger.error(f"텍스트 추출 JSON 파싱 오류: {e}")
            return {"error": f"JSON 파싱 오류: {e}", "raw_text": result_text}
    
    def _extract_structured_data(self, base64_image: str, text_analysis: Dict, 
                               room_name: str, room_type_hint: str) -> Dict:
        """2단계: 구조화된 데이터 추출"""
        
        # 텍스트 분석 결과를 프롬프트에 포함
        text_info = ""
        if "all_text_lines" in text_analysis:
            text_info = f"이미지에서 읽은 텍스트:\n" + "\n".join(text_analysis["all_text_lines"])
        
        openings_info = ""
        if "openings_found" in text_analysis:
            openings_info = f"\n발견된 개구부:\n"
            for opening in text_analysis["openings_found"]:
                openings_info += f"- {opening.get('type', 'Unknown')}: {opening.get('text', '')}\n"
        
        prompt = f"""
        이 건축 이미지를 분석해서 정확한 데이터를 JSON으로 추출해주세요.
        
        **텍스트 읽기 결과 참고:**
        {text_info}
        {openings_info}
        
        방 이름: {room_name if room_name else "미지정"}
        방 유형 힌트: {room_type_hint if room_type_hint else "없음"}
        
        **중요: 반드시 유효한 JSON 형태로만 응답하세요.**
        
        다음 정확한 JSON 형태로 응답해주세요:
        
        {{
            "room_identification": {{
                "detected_room_name": "이미지에서 읽은 방 이름",
                "room_shape": "rectangular",
                "confidence_level": "high/medium/low",
                "image_type": "insurance_estimate"
            }},
            "extracted_dimensions": {{
                "ceiling_height_ft": 8.0,
                "floor_area_sf": 200.0,
                "room_area_sf": 200.0,
                "wall_area_sf": 400.0,
                "ceiling_area_sf": 200.0,
                "perimeter_lf": 60.0,
                "ceiling_perimeter_lf": 60.0
            }},
            "room_geometry": {{
                "total_floor_area_sf": 200.0,
                "ceiling_height_ft": 8.0,
                "total_perimeter_lf": 60.0
            }},
            "openings_summary": {{
                "total_doors": 실제_문_개수,
                "total_windows": 실제_창문_개수,
                "total_open_areas": 실제_개방구간_개수,
                "total_interior_doors": 내부문_개수,
                "total_exterior_doors": 외부문_개수,
                "door_width_total_ft": 문_총_폭,
                "window_area_total_sf": 창문_총_면적,
                "open_area_width_total_ft": 개방구간_총_폭
            }},
            "detailed_openings": [
                {{
                    "type": "Door/Window/Missing Wall",
                    "width_ft": 3.0,
                    "height_ft": 6.67,
                    "area_sf": 20.0,
                    "location": "North Wall",
                    "connects_to": "연결된 곳",
                    "is_exterior": false
                }}
            ],
            "calculated_materials": {{
                "baseboard_length_lf": 계산된_베이스보드_길이,
                "crown_molding_length_lf": 계산된_크라운몰딩_길이,
                "flooring_area_sf": 바닥재_면적,
                "wall_paint_area_sf": 벽_페인트_면적,
                "ceiling_paint_area_sf": 천장_페인트_면적
            }},
            "confidence_level": "high/medium/low",
            "analysis_notes": "분석 메모",
            "dimension_source": "insurance_data"
        }}
        
        **분석 지침:**
        1. 위의 텍스트 읽기 결과를 우선적으로 참고하세요
        2. 실제로 보이는 문과 창문의 개수를 정확히 세어주세요
        3. "Door"로 시작하는 라인만 문으로 계산하세요
        4. "Window"로 시작하는 라인만 창문으로 계산하세요
        5. "Missing Wall"이나 "Goes to Floor" 등은 개방구간으로 분류하세요
        6. 모든 숫자는 소수점 형태로 입력하세요
        7. JSON 외의 다른 텍스트는 출력하지 마세요
        
        **베이스보드 계산 공식:**
        베이스보드 길이 = 둘레 - 문 총 폭 - 개방구간 총 폭
        
        반드시 유효한 JSON만 출력하세요!
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=2000
        )
        
        try:
            result_text = response.choices[0].message.content
            json_start = result_text.find('{')
            json_end = result_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = result_text[json_start:json_end]
                cleaned_json = self._clean_json_string(json_str)
                return json.loads(cleaned_json)
            else:
                logger.error("구조화된 데이터 추출에서 JSON을 찾을 수 없음")
                return {"error": "JSON 파싱 실패", "raw_text": result_text}
                
        except json.JSONDecodeError as e:
            logger.error(f"구조화된 데이터 추출 JSON 파싱 오류: {e}")
            return {"error": f"JSON 파싱 오류: {e}", "raw_text": result_text}
    
    def _cross_validate_and_correct(self, text_analysis: Dict, structured_analysis: Dict) -> Dict:
        """3단계: 교차 검증 및 보정"""
        logger.info("교차 검증 및 보정 시작")
        
        # 오류가 있는 경우 기본값 반환
        if "error" in text_analysis or "error" in structured_analysis:
            logger.error("분석 단계에서 오류 발생, 기본값 사용")
            return self._get_default_result()
        
        # 구조화된 분석 결과를 기본으로 사용
        result = structured_analysis.copy()
        
        # 텍스트 분석 결과와 교차 검증
        if "verification" in text_analysis:
            verification = text_analysis["verification"]
            openings_summary = result.get("openings_summary", {})
            
            # 개구부 개수 검증 및 보정
            text_doors = verification.get("total_doors_counted", 0)
            text_windows = verification.get("total_windows_counted", 0)
            text_opens = verification.get("total_open_areas_counted", 0)
            
            struct_doors = openings_summary.get("total_doors", 0)
            struct_windows = openings_summary.get("total_windows", 0)
            struct_opens = openings_summary.get("total_open_areas", 0)
            
            logger.info(f"텍스트 분석: 문={text_doors}, 창문={text_windows}, 개방={text_opens}")
            logger.info(f"구조 분석: 문={struct_doors}, 창문={struct_windows}, 개방={struct_opens}")
            
            # 차이가 큰 경우 텍스트 분석 결과를 우선시
            if abs(text_doors - struct_doors) > 2:
                logger.warning(f"문 개수 차이 큼: 텍스트 분석 결과({text_doors}) 사용")
                openings_summary["total_doors"] = text_doors
            
            if abs(text_windows - struct_windows) > 1:
                logger.warning(f"창문 개수 차이 큼: 텍스트 분석 결과({text_windows}) 사용")
                openings_summary["total_windows"] = text_windows
            
            if abs(text_opens - struct_opens) > 1:
                logger.warning(f"개방구간 개수 차이 큼: 텍스트 분석 결과({text_opens}) 사용")
                openings_summary["total_open_areas"] = text_opens
        
        # 베이스보드 길이 재계산
        self._recalculate_baseboard(result)
        
        # None 값들을 안전한 기본값으로 교체
        result = self._sanitize_result(result)
        
        # 신뢰도 조정
        if "verification" in text_analysis:
            confidence = text_analysis["verification"].get("confidence_level", "medium")
            result["confidence_level"] = confidence
        
        logger.info("교차 검증 및 보정 완료")
        return result
    
    def _recalculate_baseboard(self, result: Dict):
        """베이스보드 길이 재계산"""
        try:
            extracted_dims = result.get("extracted_dimensions", {})
            openings_summary = result.get("openings_summary", {})
            
            # 둘레 정보 가져오기
            perimeter = extracted_dims.get("perimeter_lf", 0)
            if perimeter <= 0:
                perimeter = extracted_dims.get("ceiling_perimeter_lf", 0)
            
            # 문 총 폭
            door_width_total = openings_summary.get("door_width_total_ft", 0)
            
            # 개방구간 총 폭
            open_area_width_total = openings_summary.get("open_area_width_total_ft", 0)
            
            # 베이스보드 길이 계산
            baseboard_length = max(0, perimeter - door_width_total - open_area_width_total)
            
            # calculated_materials 업데이트
            if "calculated_materials" not in result:
                result["calculated_materials"] = {}
            
            result["calculated_materials"]["baseboard_length_lf"] = baseboard_length
            
            logger.info(f"베이스보드 재계산: {perimeter} - {door_width_total} - {open_area_width_total} = {baseboard_length}")
            
        except Exception as e:
            logger.error(f"베이스보드 재계산 중 오류: {e}")
    
    def _clean_json_string(self, json_str: str) -> str:
        """JSON 문자열을 정리하여 파싱 가능하게 만듭니다."""
        import re
        
        # 주석 제거
        json_str = re.sub(r'//.*?\n', '\n', json_str)
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
        
        # 작은따옴표를 큰따옴표로
        json_str = re.sub(r"'([^']*)':", r'"\1":', json_str)
        json_str = re.sub(r":\s*'([^']*)'", r': "\1"', json_str)
        
        # 따옴표 없는 속성 이름 수정
        json_str = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_str)
        
        # 마지막 쉼표 제거
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        return json_str
    
    def _sanitize_result(self, result):
        """결과에서 None 값들을 안전한 기본값으로 교체"""
        
        # extracted_dimensions 처리
        if "extracted_dimensions" in result:
            dims = result["extracted_dimensions"]
            dims["ceiling_height_ft"] = safe_float(dims.get("ceiling_height_ft"), 8.0)
            dims["floor_area_sf"] = safe_float(dims.get("floor_area_sf"), 120.0)
            dims["room_area_sf"] = safe_float(dims.get("room_area_sf"), 120.0)
            dims["wall_area_sf"] = safe_float(dims.get("wall_area_sf"), 320.0)
            dims["ceiling_area_sf"] = safe_float(dims.get("ceiling_area_sf"), 120.0)
            dims["perimeter_lf"] = safe_float(dims.get("perimeter_lf"), 44.0)
            dims["ceiling_perimeter_lf"] = safe_float(dims.get("ceiling_perimeter_lf"), 44.0)
        
        # room_geometry 처리
        if "room_geometry" in result:
            geo = result["room_geometry"]
            geo["total_floor_area_sf"] = safe_float(geo.get("total_floor_area_sf"), 120.0)
            geo["ceiling_height_ft"] = safe_float(geo.get("ceiling_height_ft"), 8.0)
            geo["total_perimeter_lf"] = safe_float(geo.get("total_perimeter_lf"), 44.0)
        
        # openings_summary 처리
        if "openings_summary" in result:
            openings = result["openings_summary"]
            openings["total_doors"] = int(safe_float(openings.get("total_doors"), 1))
            openings["total_windows"] = int(safe_float(openings.get("total_windows"), 1))
            openings["total_open_areas"] = int(safe_float(openings.get("total_open_areas"), 0))
            openings["door_width_total_ft"] = safe_float(openings.get("door_width_total_ft"), 3.0)
            openings["window_area_total_sf"] = safe_float(openings.get("window_area_total_sf"), 12.0)
            openings["open_area_width_total_ft"] = safe_float(openings.get("open_area_width_total_ft"), 0.0)
            openings["total_interior_doors"] = int(safe_float(openings.get("total_interior_doors"), openings["total_doors"]))
            openings["total_exterior_doors"] = int(safe_float(openings.get("total_exterior_doors"), 0))
        
        # calculated_materials 처리
        if "calculated_materials" in result:
            materials = result["calculated_materials"]
            materials["baseboard_length_lf"] = safe_float(materials.get("baseboard_length_lf"), 41.0)
            materials["crown_molding_length_lf"] = safe_float(materials.get("crown_molding_length_lf"), 44.0)
            materials["flooring_area_sf"] = safe_float(materials.get("flooring_area_sf"), 120.0)
            materials["wall_paint_area_sf"] = safe_float(materials.get("wall_paint_area_sf"), 320.0)
            materials["ceiling_paint_area_sf"] = safe_float(materials.get("ceiling_paint_area_sf"), 120.0)
        
        return result
    
    def _get_default_result(self):
        """기본 결과 구조 반환"""
        return {
            "room_identification": {
                "detected_room_name": "Unknown Room",
                "room_shape": "rectangular",
                "confidence_level": "low"
            },
            "extracted_dimensions": {
                "ceiling_height_ft": 8.0,
                "floor_area_sf": 120.0,
                "room_area_sf": 120.0,
                "wall_area_sf": 320.0,
                "ceiling_area_sf": 120.0,
                "perimeter_lf": 44.0,
                "ceiling_perimeter_lf": 44.0
            },
            "room_geometry": {
                "total_floor_area_sf": 120.0,
                "ceiling_height_ft": 8.0,
                "total_perimeter_lf": 44.0
            },
            "openings_summary": {
                "total_doors": 1,
                "total_windows": 1,
                "total_open_areas": 0,
                "total_interior_doors": 1,
                "total_exterior_doors": 0,
                "door_width_total_ft": 3.0,
                "window_area_total_sf": 12.0,
                "open_area_width_total_ft": 0.0
            },
            "calculated_materials": {
                "baseboard_length_lf": 41.0,
                "crown_molding_length_lf": 44.0,
                "flooring_area_sf": 120.0,
                "wall_paint_area_sf": 320.0,
                "ceiling_paint_area_sf": 120.0
            },
            "confidence_level": "low",
            "analysis_notes": "기본값 사용됨",
            "dimension_source": "ai_analysis"
        }
    
    def _get_error_result(self, error_message: str):
        """오류 결과 반환"""
        result = self._get_default_result()
        result["error"] = error_message
        result["analysis_notes"] = f"분석 실패: {error_message}"
        return result


# 사용 예시
def test_improved_analyzer():
    """개선된 분석기 테스트"""
    client = init_openai_client()
    analyzer = ImprovedAIImageAnalyzer(client)
    
    # 이미지 파일로 테스트
    # with open("kitchen_image.jpg", "rb") as f:
    #     result = analyzer.analyze_construction_image(f, "Kitchen", "residential")
    #     print(json.dumps(result, indent=2, ensure_ascii=False))
    
    return analyzer