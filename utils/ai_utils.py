import re
from typing import Dict, List, Tuple, Optional
import logging
import os
from openai import OpenAI
import base64

logger = logging.getLogger(__name__)

# OpenAI 클라이언트 초기화
def init_openai_client():
    """OpenAI 클라이언트를 초기화합니다."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
    
    return OpenAI(api_key=api_key)

def encode_image_to_base64(image_path: str) -> str:
    """이미지를 base64로 인코딩합니다."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        logger.error(f"이미지 인코딩 중 오류: {e}")
        raise

def safe_float(value, default=0.0):
    """안전하게 float로 변환합니다."""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def analyze_image_with_gpt4_vision(image_path: str, prompt: str = None) -> str:
    """GPT-4 Vision을 사용하여 이미지를 분석합니다."""
    try:
        client = init_openai_client()
        
        # 이미지를 base64로 인코딩
        base64_image = encode_image_to_base64(image_path)
        
        # 기본 프롬프트 설정
        if not prompt:
            prompt = """
            이 건축 도면을 분석해주세요. 다음 정보를 추출해주세요:
            1. 방 이름과 크기
            2. 벽, 천장, 바닥 면적 (SF)
            3. 문과 창문의 크기와 위치
            4. 기타 중요한 치수 정보
            
            모든 수치는 정확히 읽어서 제공해주세요.
            """
        
        response = client.chat.completions.create(
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
            max_tokens=1500
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"GPT-4 Vision 분석 중 오류: {e}")
        raise

def extract_text_from_image_gpt4(image_path: str) -> str:
    """GPT-4 Vision을 사용하여 이미지에서 텍스트를 추출합니다."""
    prompt = """
    이 이미지에서 모든 텍스트와 숫자를 정확히 읽어서 추출해주세요.
    특히 다음 항목들을 주의 깊게 읽어주세요:
    - 방 이름
    - 면적 정보 (SF, SY, LF 단위)
    - 문과 창문의 크기 (feet와 inches)
    - 높이 정보
    - 연결 정보 (Opens into, Goes to 등)
    
    모든 텍스트를 원본 그대로 정확히 출력해주세요.
    """
    
    return analyze_image_with_gpt4_vision(image_path, prompt)

# Enhanced AI Image Analyzer (기존 Streamlit 호환성 유지)
class EnhancedAIImageAnalyzer:
    """기존 Streamlit용 AI 분석기 - 호환성 유지"""
    
    def __init__(self, openai_client):
        self.client = openai_client
    
    def analyze_construction_image(self, uploaded_file, room_name: str = "", room_type_hint: str = ""):
        """건축 이미지를 분석합니다."""
        try:
            logger.info(f"=== AI 이미지 분석 시작 ===")
            logger.info(f"방 이름: {room_name}, 방 유형: {room_type_hint}")
            
            # 파일에서 바이트 데이터 읽기
            if hasattr(uploaded_file, 'read'):
                image_bytes = uploaded_file.read()
                uploaded_file.seek(0)  # 파일 포인터 리셋
            else:
                image_bytes = uploaded_file
            
            logger.info(f"이미지 크기: {len(image_bytes)} bytes")
            
            # base64로 인코딩
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            logger.info(f"Base64 인코딩 완료: {len(base64_image)} 문자")
            
            # 분석 프롬프트
            prompt = f"""
            이 건축 도면/이미지를 분석해서 건설 작업에 필요한 실용적인 정보를 JSON 형태로 추출해주세요.
            
            방 이름: {room_name if room_name else "미지정"}
            방 유형 힌트: {room_type_hint if room_type_hint else "없음"}
            
            다음 형태의 JSON으로 응답해주세요:
            {{
                "room_identification": {{
                    "detected_room_name": "Recreation Room",
                    "room_shape": "rectangular",
                    "confidence_level": "high"
                }},
                "extracted_dimensions": {{
                    "ceiling_height_ft": 8.58,
                    "floor_area_sf": 1134.88,
                    "room_area_sf": 1134.88,
                    "wall_area_sf": 1331.92,
                    "ceiling_area_sf": 1134.88,
                    "perimeter_lf": 147.55,
                    "ceiling_perimeter_lf": 185.58
                }},
                "room_geometry": {{
                    "total_floor_area_sf": 1134.88,
                    "ceiling_height_ft": 8.58,
                    "total_perimeter_lf": 147.55
                }},
                "openings_summary": {{
                    "total_doors": 9,
                    "total_windows": 3,
                    "total_missing_walls": 2,
                    "door_width_total_ft": 25.0,
                    "window_area_total_sf": 12.0,
                    "missing_wall_width_total_ft": 8.0
                }},
                "calculated_materials": {{
                    "baseboard_length_lf": "perimeter_lf에서 door_width_total_ft와 missing_wall_width_total_ft를 뺀 값을 계산해서 숫자로 입력",
                    "crown_molding_length_lf": "ceiling_perimeter_lf에서 missing_wall_width_total_ft를 뺀 값을 계산해서 숫자로 입력",
                    "flooring_area_sf": "floor_area_sf 값을 그대로 복사",
                    "wall_paint_area_sf": "wall_area_sf 값을 그대로 복사",
                    "ceiling_paint_area_sf": "ceiling_area_sf 값을 그대로 복사"
                }},
                "confidence_level": "high",
                "analysis_notes": "분석 완료",
                "dimension_source": "ai_analysis"
            }}
            
            중요한 구분사항:
            1. Door: 실제 문이 있는 곳 (baseboard만 제외)
            2. Window: 창문 (baseboard에 영향 없음)
            3. Missing Wall: 벽이 없는 개방된 통로 (baseboard와 crown molding 모두 제외)
            
            계산 규칙:
            1. baseboard_length_lf = perimeter_lf - door_width_total_ft - missing_wall_width_total_ft
            2. crown_molding_length_lf = ceiling_perimeter_lf - missing_wall_width_total_ft
            3. 벽면적과 천장면적은 그대로 사용 (개구부 차감하지 않음)
            
            반드시 위 JSON 구조를 정확히 따라주세요. Streamlit 호환성을 위해 extracted_dimensions와 room_geometry 섹션이 필요합니다.
            """
            
            logger.info("OpenAI API 호출 시작")
            
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
            
            logger.info("OpenAI API 응답 수신 완료")
            
            result_text = response.choices[0].message.content
            logger.info(f"원본 응답 길이: {len(result_text)} 문자")
            logger.info(f"원본 응답 내용:\n{result_text}")
            
            # JSON 파싱 시도
            import json
            try:
                # JSON 블록 추출
                json_start = result_text.find('{')
                json_end = result_text.rfind('}') + 1
                
                logger.info(f"JSON 시작 위치: {json_start}, 끝 위치: {json_end}")
                
                if json_start >= 0 and json_end > json_start:
                    json_str = result_text[json_start:json_end]
                    logger.info(f"추출된 JSON 문자열:\n{json_str}")
                    
                    result = json.loads(json_str)
                    logger.info("JSON 파싱 성공!")
                    
                    # None 값들을 안전한 기본값으로 교체
                    result = self._sanitize_result(result)
                    logger.info("결과 정리 완료")
                    
                else:
                    logger.error("JSON 블록을 찾을 수 없음")
                    result = self._get_default_result()
                    result["error"] = "JSON 형태로 파싱할 수 없음"
                    result["raw_response"] = result_text
            
            except json.JSONDecodeError as e:
                logger.error(f"JSON 파싱 오류: {str(e)}")
                logger.error(f"파싱 시도한 문자열: {json_str if 'json_str' in locals() else 'N/A'}")
                
                result = self._get_default_result()
                result["error"] = f"JSON 파싱 오류: {str(e)}"
                result["raw_response"] = result_text
                result["attempted_json"] = json_str if 'json_str' in locals() else None
            
            logger.info("=== AI 이미지 분석 완료 ===")
            return result
            
        except Exception as e:
            logger.error(f"이미지 분석 중 치명적 오류: {str(e)}")
            logger.error(f"오류 타입: {type(e).__name__}")
            import traceback
            logger.error(f"스택 트레이스:\n{traceback.format_exc()}")
            
            return {
                "error": str(e),
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc()
            }
    
    def _sanitize_result(self, result):
        """결과에서 None 값들을 안전한 기본값으로 교체"""
        logger.info("결과 정리 시작")
        logger.info(f"입력된 결과 구조: {list(result.keys()) if isinstance(result, dict) else 'dict가 아님'}")
        
        # extracted_dimensions 처리 (Streamlit 호환성)
        if "extracted_dimensions" in result:
            logger.info("extracted_dimensions 처리 중")
            dims = result["extracted_dimensions"]
            dims["ceiling_height_ft"] = safe_float(dims.get("ceiling_height_ft"), 8.0)
            dims["floor_area_sf"] = safe_float(dims.get("floor_area_sf"), 120.0)
            dims["room_area_sf"] = safe_float(dims.get("room_area_sf"), 120.0)
            dims["wall_area_sf"] = safe_float(dims.get("wall_area_sf"), 320.0)
            dims["ceiling_area_sf"] = safe_float(dims.get("ceiling_area_sf"), 120.0)
            dims["perimeter_lf"] = safe_float(dims.get("perimeter_lf"), 44.0)
            dims["ceiling_perimeter_lf"] = safe_float(dims.get("ceiling_perimeter_lf"), 44.0)
            logger.info(f"extracted_dimensions 처리 완료: {dims}")
        else:
            logger.warning("extracted_dimensions가 결과에 없음")
        
        # room_geometry 처리 (Streamlit 호환성)
        if "room_geometry" in result:
            logger.info("room_geometry 처리 중")
            geo = result["room_geometry"]
            geo["total_floor_area_sf"] = safe_float(geo.get("total_floor_area_sf"), 120.0)
            geo["ceiling_height_ft"] = safe_float(geo.get("ceiling_height_ft"), 8.0)
            geo["total_perimeter_lf"] = safe_float(geo.get("total_perimeter_lf"), 44.0)
            logger.info(f"room_geometry 처리 완료: {geo}")
        else:
            logger.warning("room_geometry가 결과에 없음")
        
        # openings_summary 처리 (Streamlit 호환성)
        if "openings_summary" in result:
            logger.info("openings_summary 처리 중")
            openings = result["openings_summary"]
            openings["total_doors"] = int(safe_float(openings.get("total_doors"), 1))
            openings["total_windows"] = int(safe_float(openings.get("total_windows"), 1))
            openings["total_missing_walls"] = int(safe_float(openings.get("total_missing_walls"), 0))
            openings["door_width_total_ft"] = safe_float(openings.get("door_width_total_ft"), 3.0)
            openings["window_area_total_sf"] = safe_float(openings.get("window_area_total_sf"), 12.0)
            openings["missing_wall_width_total_ft"] = safe_float(openings.get("missing_wall_width_total_ft"), 0.0)
            
            # Streamlit 호환을 위한 기존 필드들도 추가
            openings["total_interior_doors"] = openings["total_doors"]
            openings["total_exterior_doors"] = 0
            
            logger.info(f"openings_summary 처리 완료: {openings}")
        else:
            logger.warning("openings_summary가 결과에 없음")
        
        # calculated_materials 처리
        if "calculated_materials" in result:
            logger.info("calculated_materials 처리 중")
            materials = result["calculated_materials"]
            
            # 문자열로 된 계산식이 있을 수 있으므로 숫자로 변환 시도
            baseboard_val = materials.get("baseboard_length_lf")
            if isinstance(baseboard_val, str):
                logger.info(f"baseboard_length_lf가 문자열임: {baseboard_val}")
                materials["baseboard_length_lf"] = 41.0  # 기본값 사용
            else:
                materials["baseboard_length_lf"] = safe_float(baseboard_val, 41.0)
            
            crown_val = materials.get("crown_molding_length_lf")
            if isinstance(crown_val, str):
                logger.info(f"crown_molding_length_lf가 문자열임: {crown_val}")
                materials["crown_molding_length_lf"] = 44.0  # 기본값 사용
            else:
                materials["crown_molding_length_lf"] = safe_float(crown_val, 44.0)
            
            materials["flooring_area_sf"] = safe_float(materials.get("flooring_area_sf"), 120.0)
            materials["wall_paint_area_sf"] = safe_float(materials.get("wall_paint_area_sf"), 320.0)
            materials["ceiling_paint_area_sf"] = safe_float(materials.get("ceiling_paint_area_sf"), 120.0)
            logger.info(f"calculated_materials 처리 완료: {materials}")
        else:
            logger.warning("calculated_materials가 결과에 없음")
        
        logger.info("결과 정리 완료")
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
                "total_missing_walls": 0,
                "total_interior_doors": 1,
                "total_exterior_doors": 0,
                "door_width_total_ft": 3.0,
                "window_area_total_sf": 12.0,
                "missing_wall_width_total_ft": 0.0
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


class RoomDataParser:
    """도면에서 계산된 수치 데이터를 파싱하는 클래스"""
    
    def __init__(self):
        # 면적 및 길이 단위 패턴
        self.area_patterns = {
            'sf_walls': r'(\d+\.?\d*)\s*SF\s*Walls?',
            'sf_ceiling': r'(\d+\.?\d*)\s*SF\s*Ceiling',
            'sf_floor': r'(\d+\.?\d*)\s*SF\s*Floor',
            'sf_walls_ceiling': r'(\d+\.?\d*)\s*SF\s*Walls?\s*&\s*Ceiling',
            'sy_flooring': r'(\d+\.?\d*)\s*SY\s*Flooring',
            'lf_perimeter': r'(\d+\.?\d*)\s*LF\s*(?:Floor\s*)?Perimeter',
            'lf_ceil_perimeter': r'(\d+\.?\d*)\s*LF\s*Ceil\.?\s*Perimeter',
            'diameter': r'(\d+\.?\d*)\s*(?:LF\s*)?(?:Diameter|DIAMETER)'
        }
        
        # 치수 패턴 (feet'inches" 형식)
        self.dimension_pattern = r"(\d+)'\s*(\d+)\s*(\d+)/(\d+)\""
        self.simple_dimension_pattern = r"(\d+)'\s*(\d+)\""
        
        # 개구부 정보 패턴
        self.opening_patterns = {
            'door': r'Door.*?(\d+\'\s*\d+(?:\s*\d+/\d+)?\"\s*[Xx]\s*\d+\'\s*\d+(?:\s*\d+/\d+)?\")',
            'window': r'Window.*?(\d+\'\s*\d+(?:\s*\d+/\d+)?\"\s*[Xx]\s*\d+\'\s*\d+(?:\s*\d+/\d+)?\")',
            'missing_wall': r'Missing\s*Wall.*?(\d+\'\s*\d+(?:\s*\d+/\d+)?\"\s*[Xx]\s*\d+\'\s*\d+(?:\s*\d+/\d+)?\")'
        }

    def parse_room_data(self, text: str) -> Dict:
        """텍스트에서 방 정보를 파싱"""
        try:
            # 방 이름 추출
            room_name = self._extract_room_name(text)
            
            # 면적 및 길이 데이터 추출
            measurements = self._extract_measurements(text)
            
            # 높이 정보 추출
            height = self._extract_height(text)
            
            # 개구부 정보 추출
            openings = self._extract_openings(text)
            
            return {
                'room_name': room_name,
                'height': height,
                'measurements': measurements,
                'openings': openings,
                'calculated_areas': self._calculate_additional_areas(measurements),
                'material_estimates': self._estimate_materials(measurements, openings)
            }
            
        except Exception as e:
            logger.error(f"방 데이터 파싱 중 오류: {e}")
            return {}

    def _extract_room_name(self, text: str) -> str:
        """방 이름 추출"""
        # "Recreation Room", "SUMP_ROOM2" 등의 패턴 찾기
        room_patterns = [
            r'([A-Z][a-z]+\s+Room)',  # "Recreation Room"
            r'([A-Z_]+(?:_[A-Z_]+)*)',  # "SUMP_ROOM2"
            r'Room:\s*([A-Za-z\s_]+)'  # "Room: Living Room"
        ]
        
        for pattern in room_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "Unknown Room"

    def _extract_height(self, text: str) -> Optional[str]:
        """높이 정보 추출"""
        height_pattern = r'Height:\s*(\d+\'\s*\d+\"?)'
        match = re.search(height_pattern, text, re.IGNORECASE)
        return match.group(1) if match else None

    def _extract_measurements(self, text: str) -> Dict[str, float]:
        """면적 및 길이 측정값 추출"""
        measurements = {}
        
        for key, pattern in self.area_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # 여러 값이 있으면 첫 번째 값 사용
                measurements[key] = float(matches[0])
        
        return measurements

    def _extract_openings(self, text: str) -> List[Dict]:
        """개구부 정보 추출"""
        openings = []
        
        # 각 라인을 분석하여 개구부 정보 추출
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Door, Window, Missing Wall 등 찾기
            opening_info = self._parse_opening_line(line)
            if opening_info:
                openings.append(opening_info)
        
        return openings

    def _parse_opening_line(self, line: str) -> Optional[Dict]:
        """개별 라인에서 개구부 정보 파싱"""
        # 개구부 타입 확인
        opening_type = None
        if 'door' in line.lower():
            opening_type = 'Door'
        elif 'window' in line.lower():
            opening_type = 'Window'
        elif 'missing wall' in line.lower():
            opening_type = 'Missing Wall'
        else:
            return None
        
        # 치수 추출 (예: 5' 7 11/16" X 7' 3/16")
        dimension_match = re.search(
            r"(\d+)'\s*(\d+)(?:\s*(\d+)/(\d+))?\"\s*[Xx]\s*(\d+)'\s*(\d+)(?:\s*(\d+)/(\d+))?\"",
            line
        )
        
        if dimension_match:
            groups = dimension_match.groups()
            
            # 첫 번째 치수 (폭)
            width_feet = int(groups[0])
            width_inches = int(groups[1])
            width_frac_num = int(groups[2]) if groups[2] else 0
            width_frac_den = int(groups[3]) if groups[3] else 1
            
            # 두 번째 치수 (높이)
            height_feet = int(groups[4])
            height_inches = int(groups[5])
            height_frac_num = int(groups[6]) if groups[6] else 0
            height_frac_den = int(groups[7]) if groups[7] else 1
            
            # 인치로 변환
            width_total = (width_feet * 12) + width_inches + (width_frac_num / width_frac_den)
            height_total = (height_feet * 12) + height_inches + (height_frac_num / height_frac_den)
            
            # 연결 정보 추출
            connection = self._extract_connection_info(line)
            
            return {
                'type': opening_type,
                'width_inches': width_total,
                'height_inches': height_total,
                'width_feet': width_total / 12,
                'height_feet': height_total / 12,
                'area_sqft': (width_total * height_total) / 144,  # 평방피트
                'connects_to': connection,
                'original_text': line.strip()
            }
        
        return None

    def _extract_connection_info(self, line: str) -> str:
        """개구부가 연결되는 곳 정보 추출"""
        connection_patterns = [
            r'Opens\s+into\s+([A-Z_\s]+)',
            r'Goes\s+to\s+([A-Z_\s]+)',
            r'into\s+([A-Z_\s]+)'
        ]
        
        for pattern in connection_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "Unknown"

    def _calculate_additional_areas(self, measurements: Dict[str, float]) -> Dict[str, float]:
        """추가 면적 계산"""
        calculated = {}
        
        # 총 표면적 계산
        if 'sf_walls' in measurements and 'sf_ceiling' in measurements:
            calculated['total_surface_area'] = measurements['sf_walls'] + measurements['sf_ceiling']
        
        # 페인트 면적 (벽면적에서 개구부 제외)
        if 'sf_walls' in measurements:
            calculated['paintable_wall_area'] = measurements['sf_walls']  # 개구부 면적은 별도 계산 필요
        
        # 바닥재 면적
        if 'sf_floor' in measurements:
            calculated['flooring_area'] = measurements['sf_floor']
        
        return calculated

    def _estimate_materials(self, measurements: Dict[str, float], openings: List[Dict]) -> Dict:
        """자재 소요량 추정"""
        materials = {}
        
        # 페인트 소요량 (1갤런당 약 350sqft 기준)
        if 'sf_walls' in measurements:
            # 개구부 면적 계산
            opening_area = sum(opening.get('area_sqft', 0) for opening in openings)
            paintable_area = measurements['sf_walls'] - opening_area
            materials['paint_gallons'] = max(0, paintable_area / 350)
        
        # 바닥재 소요량 (10% 여유분 포함)
        if 'sf_floor' in measurements:
            materials['flooring_sqft'] = measurements['sf_floor'] * 1.1
        
        # SY를 SF로 변환 (1 SY = 9 SF)
        if 'sy_flooring' in measurements:
            materials['flooring_sqft_from_sy'] = measurements['sy_flooring'] * 9
        
        # Baseboard 계산 - 둘레에서 문과 개방구간 제외
        if 'lf_perimeter' in measurements or 'diameter' in measurements:
            # diameter 우선 사용, 없으면 lf_perimeter 사용
            total_perimeter = measurements.get('diameter', measurements.get('lf_perimeter', 0))
            
            # 개구부 폭 계산 (문과 개방구간만)
            opening_widths = self._calculate_opening_widths(openings)
            
            # 실제 baseboard 필요 길이 = 둘레 - 개구부 폭들
            actual_baseboard_length = max(0, total_perimeter - opening_widths['total_width'])
            
            # 5% 여유분 포함
            materials['baseboard_lf'] = actual_baseboard_length * 1.05
            
            # 상세 정보도 포함
            materials['baseboard_details'] = {
                'total_perimeter': total_perimeter,
                'perimeter_source': 'diameter' if 'diameter' in measurements else 'lf_perimeter',
                'door_widths': opening_widths['door_width'],
                'opening_widths': opening_widths['opening_width'], 
                'total_openings_width': opening_widths['total_width'],
                'actual_baseboard_length': actual_baseboard_length,
                'with_waste_allowance': actual_baseboard_length * 1.05
            }
        
        # Crown molding은 개구부 영향 없음 (천장 둘레)
        if 'lf_ceil_perimeter' in measurements:
            materials['crown_molding_lf'] = measurements['lf_ceil_perimeter'] * 1.05
        
        return materials

    def _calculate_opening_widths(self, openings: List[Dict]) -> Dict[str, float]:
        """개구부들의 폭 계산 (baseboard 계산용)"""
        door_width = 0
        opening_width = 0  # Missing Wall, Window - Goes to Floor 등
        
        for opening in openings:
            width_ft = opening.get('width_feet', 0)
            opening_type = opening.get('type', '').lower()
            original_text = opening.get('original_text', '').lower()
            
            if 'door' in opening_type:
                door_width += width_ft
            elif ('missing wall' in original_text or 
                  'goes to floor' in original_text or
                  ('window' in opening_type and 'goes to floor' in original_text)):
                opening_width += width_ft
        
        total_width = door_width + opening_width
        
        return {
            'door_width': door_width,
            'opening_width': opening_width,
            'total_width': total_width
        }

    def parse_multiple_rooms(self, text: str) -> List[Dict]:
        """여러 방의 정보를 파싱"""
        rooms = []
        
        # 방별로 섹션 분리 (각 방은 보통 "Room" 키워드로 시작)
        room_sections = re.split(r'(?=\w+\s+Room|\w+_ROOM)', text)
        
        for section in room_sections:
            if section.strip():
                room_data = self.parse_room_data(section)
                if room_data:
                    rooms.append(room_data)
        
        return rooms

    def generate_summary_report(self, rooms: List[Dict]) -> str:
        """파싱된 데이터의 요약 보고서 생성"""
        if not rooms:
            return "파싱된 방 데이터가 없습니다."
        
        report = []
        report.append("=== 방 정보 요약 보고서 ===\n")
        
        total_floor_area = 0
        total_wall_area = 0
        total_openings = 0
        
        for i, room in enumerate(rooms, 1):
            report.append(f"{i}. {room.get('room_name', 'Unknown Room')}")
            report.append(f"   높이: {room.get('height', 'N/A')}")
            
            measurements = room.get('measurements', {})
            if measurements:
                report.append("   측정값:")
                for key, value in measurements.items():
                    unit = 'SF' if 'sf' in key else 'LF' if 'lf' in key else 'SY' if 'sy' in key else ''
                    report.append(f"     {key}: {value} {unit}")
                
                # 총합 계산
                if 'sf_floor' in measurements:
                    total_floor_area += measurements['sf_floor']
                if 'sf_walls' in measurements:
                    total_wall_area += measurements['sf_walls']
            
            openings = room.get('openings', [])
            if openings:
                report.append(f"   개구부: {len(openings)}개")
                total_openings += len(openings)
                for opening in openings[:3]:  # 처음 3개만 표시
                    report.append(f"     - {opening['type']}: {opening['width_feet']:.1f}' x {opening['height_feet']:.1f}' → {opening['connects_to']}")
            
            report.append("")
        
        # 전체 요약
        report.append("=== 전체 요약 ===")
        report.append(f"총 방 수: {len(rooms)}개")
        report.append(f"총 바닥 면적: {total_floor_area:.2f} SF")
        report.append(f"총 벽 면적: {total_wall_area:.2f} SF")
        report.append(f"총 개구부: {total_openings}개")
        
        return "\n".join(report)

class RoomDataParser:
    """도면에서 계산된 수치 데이터를 파싱하는 클래스"""
    
    def __init__(self):
        # 면적 및 길이 단위 패턴
        self.area_patterns = {
            'sf_walls': r'(\d+\.?\d*)\s*SF\s*Walls?',
            'sf_ceiling': r'(\d+\.?\d*)\s*SF\s*Ceiling',
            'sf_floor': r'(\d+\.?\d*)\s*SF\s*Floor',
            'sf_walls_ceiling': r'(\d+\.?\d*)\s*SF\s*Walls?\s*&\s*Ceiling',
            'sy_flooring': r'(\d+\.?\d*)\s*SY\s*Flooring',
            'lf_perimeter': r'(\d+\.?\d*)\s*LF\s*(?:Floor\s*)?Perimeter',
            'lf_ceil_perimeter': r'(\d+\.?\d*)\s*LF\s*Ceil\.?\s*Perimeter',
            'diameter': r'(\d+\.?\d*)\s*(?:LF\s*)?(?:Diameter|DIAMETER)'
        }
        
        # 치수 패턴 (feet'inches" 형식)
        self.dimension_pattern = r"(\d+)'\s*(\d+)\s*(\d+)/(\d+)\""
        self.simple_dimension_pattern = r"(\d+)'\s*(\d+)\""
        
        # 개구부 정보 패턴
        self.opening_patterns = {
            'door': r'Door.*?(\d+\'\s*\d+(?:\s*\d+/\d+)?\"\s*[Xx]\s*\d+\'\s*\d+(?:\s*\d+/\d+)?\")',
            'window': r'Window.*?(\d+\'\s*\d+(?:\s*\d+/\d+)?\"\s*[Xx]\s*\d+\'\s*\d+(?:\s*\d+/\d+)?\")',
            'missing_wall': r'Missing\s*Wall.*?(\d+\'\s*\d+(?:\s*\d+/\d+)?\"\s*[Xx]\s*\d+\'\s*\d+(?:\s*\d+/\d+)?\")'
        }

    def parse_room_data(self, text: str) -> Dict:
        """텍스트에서 방 정보를 파싱"""
        try:
            # 방 이름 추출
            room_name = self._extract_room_name(text)
            
            # 면적 및 길이 데이터 추출
            measurements = self._extract_measurements(text)
            
            # 높이 정보 추출
            height = self._extract_height(text)
            
            # 개구부 정보 추출
            openings = self._extract_openings(text)
            
            return {
                'room_name': room_name,
                'height': height,
                'measurements': measurements,
                'openings': openings,
                'calculated_areas': self._calculate_additional_areas(measurements),
                'material_estimates': self._estimate_materials(measurements, openings)
            }
            
        except Exception as e:
            logger.error(f"방 데이터 파싱 중 오류: {e}")
            return {}

    def _extract_room_name(self, text: str) -> str:
        """방 이름 추출"""
        # "Recreation Room", "SUMP_ROOM2" 등의 패턴 찾기
        room_patterns = [
            r'([A-Z][a-z]+\s+Room)',  # "Recreation Room"
            r'([A-Z_]+(?:_[A-Z_]+)*)',  # "SUMP_ROOM2"
            r'Room:\s*([A-Za-z\s_]+)'  # "Room: Living Room"
        ]
        
        for pattern in room_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "Unknown Room"

    def _extract_height(self, text: str) -> Optional[str]:
        """높이 정보 추출"""
        height_pattern = r'Height:\s*(\d+\'\s*\d+\"?)'
        match = re.search(height_pattern, text, re.IGNORECASE)
        return match.group(1) if match else None

    def _extract_measurements(self, text: str) -> Dict[str, float]:
        """면적 및 길이 측정값 추출"""
        measurements = {}
        
        for key, pattern in self.area_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # 여러 값이 있으면 첫 번째 값 사용
                measurements[key] = float(matches[0])
        
        return measurements

    def _extract_openings(self, text: str) -> List[Dict]:
        """개구부 정보 추출"""
        openings = []
        
        # 각 라인을 분석하여 개구부 정보 추출
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Door, Window, Missing Wall 등 찾기
            opening_info = self._parse_opening_line(line)
            if opening_info:
                openings.append(opening_info)
        
        return openings

    def _parse_opening_line(self, line: str) -> Optional[Dict]:
        """개별 라인에서 개구부 정보 파싱"""
        # 개구부 타입 확인
        opening_type = None
        if 'door' in line.lower():
            opening_type = 'Door'
        elif 'window' in line.lower():
            opening_type = 'Window'
        elif 'missing wall' in line.lower():
            opening_type = 'Missing Wall'
        else:
            return None
        
        # 치수 추출 (예: 5' 7 11/16" X 7' 3/16")
        dimension_match = re.search(
            r"(\d+)'\s*(\d+)(?:\s*(\d+)/(\d+))?\"\s*[Xx]\s*(\d+)'\s*(\d+)(?:\s*(\d+)/(\d+))?\"",
            line
        )
        
        if dimension_match:
            groups = dimension_match.groups()
            
            # 첫 번째 치수 (폭)
            width_feet = int(groups[0])
            width_inches = int(groups[1])
            width_frac_num = int(groups[2]) if groups[2] else 0
            width_frac_den = int(groups[3]) if groups[3] else 1
            
            # 두 번째 치수 (높이)
            height_feet = int(groups[4])
            height_inches = int(groups[5])
            height_frac_num = int(groups[6]) if groups[6] else 0
            height_frac_den = int(groups[7]) if groups[7] else 1
            
            # 인치로 변환
            width_total = (width_feet * 12) + width_inches + (width_frac_num / width_frac_den)
            height_total = (height_feet * 12) + height_inches + (height_frac_num / height_frac_den)
            
            # 연결 정보 추출
            connection = self._extract_connection_info(line)
            
            return {
                'type': opening_type,
                'width_inches': width_total,
                'height_inches': height_total,
                'width_feet': width_total / 12,
                'height_feet': height_total / 12,
                'area_sqft': (width_total * height_total) / 144,  # 평방피트
                'connects_to': connection,
                'original_text': line.strip()
            }
        
        return None

    def _extract_connection_info(self, line: str) -> str:
        """개구부가 연결되는 곳 정보 추출"""
        connection_patterns = [
            r'Opens\s+into\s+([A-Z_\s]+)',
            r'Goes\s+to\s+([A-Z_\s]+)',
            r'into\s+([A-Z_\s]+)'
        ]
        
        for pattern in connection_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "Unknown"

    def _calculate_additional_areas(self, measurements: Dict[str, float]) -> Dict[str, float]:
        """추가 면적 계산"""
        calculated = {}
        
        # 총 표면적 계산
        if 'sf_walls' in measurements and 'sf_ceiling' in measurements:
            calculated['total_surface_area'] = measurements['sf_walls'] + measurements['sf_ceiling']
        
        # 페인트 면적 (벽면적에서 개구부 제외)
        if 'sf_walls' in measurements:
            calculated['paintable_wall_area'] = measurements['sf_walls']  # 개구부 면적은 별도 계산 필요
        
        # 바닥재 면적
        if 'sf_floor' in measurements:
            calculated['flooring_area'] = measurements['sf_floor']
        
        return calculated

    def _estimate_materials(self, measurements: Dict[str, float], openings: List[Dict]) -> Dict:
        """자재 소요량 추정"""
        materials = {}
        
        # 페인트 소요량 (1갤런당 약 350sqft 기준)
        if 'sf_walls' in measurements:
            # 개구부 면적 계산
            opening_area = sum(opening.get('area_sqft', 0) for opening in openings)
            paintable_area = measurements['sf_walls'] - opening_area
            materials['paint_gallons'] = max(0, paintable_area / 350)
        
        # 바닥재 소요량 (10% 여유분 포함)
        if 'sf_floor' in measurements:
            materials['flooring_sqft'] = measurements['sf_floor'] * 1.1
        
        # SY를 SF로 변환 (1 SY = 9 SF)
        if 'sy_flooring' in measurements:
            materials['flooring_sqft_from_sy'] = measurements['sy_flooring'] * 9
        
        # Baseboard 계산 - 둘레에서 문과 개방구간 제외
        if 'lf_perimeter' in measurements or 'diameter' in measurements:
            # diameter 우선 사용, 없으면 lf_perimeter 사용
            total_perimeter = measurements.get('diameter', measurements.get('lf_perimeter', 0))
            
            # 개구부 폭 계산 (문과 개방구간만)
            opening_widths = self._calculate_opening_widths(openings)
            
            # 실제 baseboard 필요 길이 = 둘레 - 개구부 폭들
            actual_baseboard_length = max(0, total_perimeter - opening_widths['total_width'])
            
            # 5% 여유분 포함
            materials['baseboard_lf'] = actual_baseboard_length * 1.05
            
            # 상세 정보도 포함
            materials['baseboard_details'] = {
                'total_perimeter': total_perimeter,
                'perimeter_source': 'diameter' if 'diameter' in measurements else 'lf_perimeter',
                'door_widths': opening_widths['door_width'],
                'opening_widths': opening_widths['opening_width'], 
                'total_openings_width': opening_widths['total_width'],
                'actual_baseboard_length': actual_baseboard_length,
                'with_waste_allowance': actual_baseboard_length * 1.05
            }
        
        # Crown molding은 개구부 영향 없음 (천장 둘레)
        if 'lf_ceil_perimeter' in measurements:
            materials['crown_molding_lf'] = measurements['lf_ceil_perimeter'] * 1.05
        
        return materials

    def _calculate_opening_widths(self, openings: List[Dict]) -> Dict[str, float]:
        """개구부들의 폭 계산 (baseboard 계산용)"""
        door_width = 0
        opening_width = 0  # Missing Wall, Window - Goes to Floor 등
        
        for opening in openings:
            width_ft = opening.get('width_feet', 0)
            opening_type = opening.get('type', '').lower()
            original_text = opening.get('original_text', '').lower()
            
            if 'door' in opening_type:
                door_width += width_ft
            elif ('missing wall' in original_text or 
                  'goes to floor' in original_text or
                  ('window' in opening_type and 'goes to floor' in original_text)):
                opening_width += width_ft
        
        total_width = door_width + opening_width
        
        return {
            'door_width': door_width,
            'opening_width': opening_width,
            'total_width': total_width
        }

    def parse_multiple_rooms(self, text: str) -> List[Dict]:
        """여러 방의 정보를 파싱"""
        rooms = []
        
        # 방별로 섹션 분리 (각 방은 보통 "Room" 키워드로 시작)
        room_sections = re.split(r'(?=\w+\s+Room|\w+_ROOM)', text)
        
        for section in room_sections:
            if section.strip():
                room_data = self.parse_room_data(section)
                if room_data:
                    rooms.append(room_data)
        
        return rooms

    def generate_summary_report(self, rooms: List[Dict]) -> str:
        """파싱된 데이터의 요약 보고서 생성"""
        if not rooms:
            return "파싱된 방 데이터가 없습니다."
        
        report = []
        report.append("=== 방 정보 요약 보고서 ===\n")
        
        total_floor_area = 0
        total_wall_area = 0
        total_openings = 0
        
        for i, room in enumerate(rooms, 1):
            report.append(f"{i}. {room.get('room_name', 'Unknown Room')}")
            report.append(f"   높이: {room.get('height', 'N/A')}")
            
            measurements = room.get('measurements', {})
            if measurements:
                report.append("   측정값:")
                for key, value in measurements.items():
                    unit = 'SF' if 'sf' in key else 'LF' if 'lf' in key else 'SY' if 'sy' in key else ''
                    report.append(f"     {key}: {value} {unit}")
                
                # 총합 계산
                if 'sf_floor' in measurements:
                    total_floor_area += measurements['sf_floor']
                if 'sf_walls' in measurements:
                    total_wall_area += measurements['sf_walls']
            
            openings = room.get('openings', [])
            if openings:
                report.append(f"   개구부: {len(openings)}개")
                total_openings += len(openings)
                for opening in openings[:3]:  # 처음 3개만 표시
                    report.append(f"     - {opening['type']}: {opening['width_feet']:.1f}' x {opening['height_feet']:.1f}' → {opening['connects_to']}")
            
            report.append("")
        
        # 전체 요약
        report.append("=== 전체 요약 ===")
        report.append(f"총 방 수: {len(rooms)}개")
        report.append(f"총 바닥 면적: {total_floor_area:.2f} SF")
        report.append(f"총 벽 면적: {total_wall_area:.2f} SF")
        report.append(f"총 개구부: {total_openings}개")
        
        return "\n".join(report)


# 사용 예제
def main():
    """사용 예제"""
    parser = RoomDataParser()
    
    # 샘플 텍스트 (이미지에서 추출된 텍스트)
    sample_text = """
    Recreation Room                                Height: 8' 7"
    1331.92 SF Walls                              1134.88 SF Ceiling
    2466.80 SF Walls & Ceiling                    1134.88 SF Floor
    126.10 SY Flooring                            147.55 LF Floor Perimeter
    185.58 LF Ceil. Perimeter
    
    Door        5' 7 11/16" X 7' 3/16"           Opens into Exterior
    Door        2' 2" X 6' 8"                    Opens into SUMP_ROOM2
    Window      2' 7 9/16" X 1' 1/2"             Opens into Exterior
    Door        5' 11 3/16" X 7' 2 3/8"          Opens into RECREATION_1
    Door        3' 15/16" X 6' 10 11/16"         Opens into COMPUTER_ARE
    Window      1' 4 1/4" X 1' 3 5/8"            Opens into Exterior
    Door        2' 6 5/8" X 6' 11 1/4"           Opens into SUMP_ROOM_2
    Missing Wall - Goes to Floor    4' 7 3/8" X 6' 9 5/8"    Opens into CLOSET_TWO
    Window - Goes to Floor          2' 7 13/16" X 6' 11 9/16" Opens into STORAGE_AREA
    Door        2' 6 5/8" X 6' 11 7/16"          Opens into UNDER_STAIR2
    Door        2' 5 1/8" X 6' 11 1/8"           Opens into UNDER_STAIR2
    Door        3' 9" X 6' 8 3/16"               Opens into BACK_DOUBLE_
    Door        2' 8" X 6' 8"                    Opens into WORK_ROOM
    """
    
    # 데이터 파싱
    room_data = parser.parse_room_data(sample_text)
    
    # 결과 출력
    print("=== 파싱 결과 ===")
    print(f"방 이름: {room_data['room_name']}")
    print(f"높이: {room_data['height']}")
    print("\n측정값:")
    for key, value in room_data['measurements'].items():
        print(f"  {key}: {value}")
    
    print(f"\n개구부 ({len(room_data['openings'])}개):")
    for opening in room_data['openings']:
        print(f"  {opening['type']}: {opening['width_feet']:.2f}' x {opening['height_feet']:.2f}' → {opening['connects_to']}")
    
    print("\n자재 추정:")
    for key, value in room_data['material_estimates'].items():
        if key == 'baseboard_details':
            print(f"  Baseboard 상세:")
            for detail_key, detail_value in value.items():
                print(f"    {detail_key}: {detail_value:.2f}" if isinstance(detail_value, (int, float)) else f"    {detail_key}: {detail_value}")
        else:
            print(f"  {key}: {value:.2f}")
    
    # 요약 보고서
    print("\n" + parser.generate_summary_report([room_data]))


if __name__ == "__main__":
    main()