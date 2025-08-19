import re
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
            logger.info("=== 개선된 AI 이미지 분석 시작 ===")
            logger.info(f"Room name: {room_name}, Room type hint: {room_type_hint}")

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

            # 텍스트 분석 결과 로깅
            if "all_text_lines" in text_analysis:
                logger.info(f"Found {len(text_analysis['all_text_lines'])} text lines")
            if "openings_found" in text_analysis:
                logger.info(f"Found {len(text_analysis['openings_found'])} openings in text")
                for opening in text_analysis["openings_found"]:
                    logger.info(f"  - {opening.get('type', 'Unknown')}: {opening.get('text', '')}")

            # 2단계: 구조화된 데이터 추출
            structured_analysis = self._extract_structured_data(
                base64_image, text_analysis, room_name, room_type_hint
            )

            # 구조화된 분석 결과 로깅
            if "detailed_openings" in structured_analysis:
                logger.info(f"Structured analysis produced {len(structured_analysis['detailed_openings'])} detailed openings")

            # 3단계: 교차 검증 및 보정
            final_result = self._cross_validate_and_correct(text_analysis, structured_analysis)

            # 최종 결과 로깅
            if "openings_summary" in final_result:
                summary = final_result["openings_summary"]
                logger.info(f"Final counts - Doors: {summary.get('total_doors', 0)}, "
                           f"Windows: {summary.get('total_windows', 0)}, Open Areas: {summary.get('total_open_areas', 0)}")

            return final_result

        except Exception as e:
            logger.error(f"이미지 분석 중 치명적 오류: {str(e)}")
            return self._get_error_result(str(e))

    def _extract_text_with_verification(self, base64_image: str) -> Dict:
        """1단계: 텍스트 추출 및 검증"""
        prompt = """
        Please extract all text from this image accurately and provide detailed verification.

        **CRITICAL: Respond ONLY in valid JSON format.**

        Respond in exactly this JSON format:

        {
            "all_text_lines": [
                "All text lines found in the image",
                "Each line exactly as it appears"
            ],
            "room_info": {
                "room_name": "detected room name",
                "ceiling_height": "detected ceiling height",
                "total_lines_found": number
            },
            "measurements_found": {
                "floor_area_s": number_or_null,
                "wall_area_s": number_or_null,
                "ceiling_area_s": number_or_null,
                "perimeter_l": number_or_null,
                "ceiling_perimeter_l": number_or_null,
                "floor_perimeter_l": number_or_null
            },
            "openings_found": [
                {
                    "type": "Door/Window/Missing Wall/etc",
                    "text": "original text as found",
                    "size_info": "size information (e.g., 3'0\" x 6'8\")",
                    "connection": "connection info (Goes to, Opens into, etc)"
                }
            ],
            "verification": {
                "total_doors_counted": number,
                "total_windows_counted": number,
                "total_open_areas_counted": number,
                "confidence_level": "high/medium/low"
            }
        }

        **Reading Instructions:**
        1. Read ALL text without missing any lines - scan the entire image systematically
        2. Look for EVERY occurrence of "Door", "Window", "Missing Wall", etc.
        3. Don't skip any openings - count each one individually
        4. Look for both floor perimeter and ceiling perimeter values
        5. Carefully distinguish between interior doors, exterior doors, and windows
        6. Pay special attention to small text that might contain opening information
        7. If multiple windows are mentioned, count each one separately
        8. Count ONLY lines that start with "Door" as doors
        9. Count ONLY lines that start with "Window" as windows (including "Window - Goes to Floor")
        10. Count ONLY "Missing Wall - Goes to Floor" as open areas (NOT "Window - Goes to Floor")
        11. Avoid counting any item twice - each line should be counted only once
        12. "Window - Goes to Floor" is still a WINDOW, not an open area
        13. Output ONLY valid JSON, no other text
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

        # 텍스트 분석 결과를 더 상세하게 포함
        text_info = ""
        if "all_text_lines" in text_analysis:
            text_info = "Text read from image:\n" + "\n".join(text_analysis["all_text_lines"])

        openings_info = ""
        if "openings_found" in text_analysis:
            openings_info = f"\nDetected openings ({len(text_analysis['openings_found'])} total):\n"
            for i, opening in enumerate(text_analysis["openings_found"], 1):
                openings_info += f"{i}. {opening.get('type', 'Unknown')}: {opening.get('text', '')}\n"

        prompt = """
        Analyze this construction image and extract accurate data in JSON format.

        **Reference from text reading results:**
        {text_info}
        {openings_info}

        Room Name: {room_name if room_name else "Not specified"}
        Room Type Hint: {room_type_hint if room_type_hint else "None"}

        **CRITICAL REQUIREMENTS:**
        1. Include ALL openings found in text analysis in detailed_openings
        2. Ensure detailed_openings count matches openings_summary counts
        3. Include both floor_perimeter_lf and ceiling_perimeter_lf
        4. If you see 3 windows in text, output exactly 3 windows in detailed_openings

        **CRITICAL: Respond ONLY in valid JSON format.**

        Respond in exactly this JSON format:

        {{
            "room_identification": {{
                "detected_room_name": "room name from image",
                "room_shape": "rectangular",
                "confidence_level": "high/medium/low",
                "image_type": "insurance_estimate"
            }},
            "extracted_dimensions": {{
                "ceiling_height_ft": 8.0,
                "floor_area_s": 200.0,
                "room_area_s": 200.0,
                "wall_area_s": 400.0,
                "ceiling_area_s": 200.0,
                "perimeter_l": 60.0,
                "ceiling_perimeter_l": 60.0,
                "floor_perimeter_l": 60.0
            }},
            "room_geometry": {{
                "total_floor_area_s": 200.0,
                "ceiling_height_ft": 8.0,
                "total_perimeter_l": 60.0,
                "floor_perimeter_l": 60.0
            }},
            "openings_summary": {{
                "total_doors": actual_door_count,
                "total_windows": actual_window_count,
                "total_open_areas": actual_open_area_count,
                "total_interior_doors": interior_door_count,
                "total_exterior_doors": exterior_door_count,
                "door_width_total_ft": total_door_width,
                "window_area_total_s": total_window_area,
                "open_area_width_total_ft": total_open_area_width
            }},
            "detailed_openings": [
                {{
                    "type": "Door/Window/Missing Wall",
                    "width_ft": 3.0,
                    "height_ft": 6.67,
                    "area_s": 20.0,
                    "location": "North Wall",
                    "connects_to": "connected location",
                    "is_exterior": false
                }}
            ],
            "calculated_materials": {{
                "baseboard_length_l": calculated_baseboard_length,
                "crown_molding_length_l": calculated_crown_molding_length,
                "flooring_area_s": flooring_area,
                "wall_paint_area_s": wall_paint_area,
                "ceiling_paint_area_s": ceiling_paint_area
            }},
            "confidence_level": "high/medium/low",
            "analysis_notes": "analysis notes",
            "dimension_source": "insurance_data"
        }}

        **Analysis Guidelines:**
        1. The detailed_openings array MUST contain ALL openings mentioned in the text analysis
        2. Count matches: detailed_openings count = openings_summary counts
        3. Include both floor_perimeter_lf and ceiling_perimeter_lf in extracted_dimensions
        4. Use floor_perimeter_lf for baseboard calculations, not ceiling_perimeter_lf
        5. If text analysis found {len(text_analysis.get('openings_found', []))} openings, include all of them
        6. Count ONLY lines starting with "Door" as doors
        7. Count ALL lines starting with "Window" as windows (including "Window - Goes to Floor")
        8. Classify ONLY "Missing Wall - Goes to Floor" as open areas
        9. "Window - Goes to Floor" is a WINDOW with floor connection, NOT an open area
        10. Ensure no duplicate counting - each opening should appear exactly once
        11. All numbers must be in decimal format
        12. Output ONLY valid JSON, no other text

        **Baseboard Calculation Formula:**
        Baseboard length = floor_perimeter_lf - Total door width - Total open area width

        Output ONLY valid JSON!
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

        # 중복 제거 먼저 수행
        self._remove_duplicate_openings(result)

        # detailed_openings 검증 및 보정
        self._validate_detailed_openings(text_analysis, result)

        # floor_perimeter 확보
        self._ensure_floor_perimeter(result)

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

            logger.info(f"Text analysis: doors={text_doors}, windows={text_windows}, open_areas={text_opens}")
            logger.info(f"Structured analysis: doors={struct_doors}, windows={struct_windows},
                open_areas={struct_opens}")

            # 차이가 큰 경우 텍스트 분석 결과를 우선시
            if abs(text_doors - struct_doors) > 1:
                logger.warning(f"Large door count difference: using text analysis result ({text_doors})")
                openings_summary["total_doors"] = text_doors

            if abs(text_windows - struct_windows) > 1:
                logger.warning(f"Large window count difference: using text analysis result ({text_windows})")
                openings_summary["total_windows"] = text_windows

            if abs(text_opens - struct_opens) > 1:
                logger.warning(f"Large open area count difference: using text analysis result ({text_opens})")
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

    def _remove_duplicate_openings(self, result: Dict):
        """중복된 개구부 제거"""
        if "detailed_openings" not in result:
            return

        detailed_openings = result["detailed_openings"]
        unique_openings = []
        seen = set()

        for opening in detailed_openings:
            # 고유 식별자 생성 (타입, 연결처, 대략적인 크기)
            width = round(opening.get("width_ft", 0), 1)
            height = round(opening.get("height_ft", 0), 1)

            # 연결처 정규화 - 언더스코어와 숫자 패턴 통일
            connects_to = opening.get("connects_to", "").upper()
            # SUMP_ROOM2와 SUMP_ROOM_2를 같은 것으로 처리
            connects_to = connects_to.replace("SUMP_ROOM2", "SUMP_ROOM_2")
            connects_to = connects_to.replace("UNDER_STAIR2", "UNDER_STAIR_2")
            connects_to = connects_to.replace("_", "").replace(" ", "")

            opening_type = opening.get("type", "")

            # 정확한 크기로 식별자 생성 (0.2ft 이내 차이는 같은 것으로 간주)
            identifier = f"{opening_type}_{width}x{height}_{connects_to}"

            # 유사한 개구부 확인
            is_duplicate = False
            for seen_id in seen:
                parts = seen_id.split("_")
                if len(parts) >= 3:
                    seen_type = parts[0]
                    seen_size = parts[1]
                    seen_connects = "_".join(parts[2:])

                    if seen_type == opening_type and seen_connects == connects_to:
                        # 크기 비교
                        if "x" in seen_size:
                            seen_width, seen_height = map(float, seen_size.split("x"))
                            if abs(seen_width - width) < 0.2 and abs(seen_height - height) < 0.2:
                                is_duplicate = True
                                break

            if not is_duplicate:
                seen.add(identifier)
                unique_openings.append(opening)
            else:
                logger.warning(f"Duplicate opening removed: {opening_type} to {opening.get('connects_to', 'Unknown')}")

        if len(unique_openings) != len(detailed_openings):
            logger.info(f"Removed {len(detailed_openings) - len(unique_openings)} duplicate openings")
            result["detailed_openings"] = unique_openings

            # 개수 재계산
            door_count = sum(1 for o in unique_openings if o.get("type") == "Door")
            window_count = sum(1 for o in unique_openings if o.get("type") == "Window")
            open_area_count = sum(1 for o in unique_openings if o.get("type") in ["Missing Wall", "Open Area"])

            openings_summary = result.get("openings_summary", {})
            openings_summary["total_doors"] = door_count
            openings_summary["total_windows"] = window_count
            openings_summary["total_open_areas"] = open_area_count

            # Interior/Exterior 재계산
            interior_doors = sum(1 for o in unique_openings if o.get("type") == "Door" and not o.get("is_exterior",
                False))
            exterior_doors = sum(1 for o in unique_openings if o.get("type") == "Door" and o.get("is_exterior", False))

            openings_summary["total_interior_doors"] = interior_doors
            openings_summary["total_exterior_doors"] = exterior_doors

            logger.info(f"After deduplication - Doors: {door_count}, Windows: {window_count},
                Open Areas: {open_area_count}")

    def _validate_detailed_openings(self, text_analysis: Dict, result: Dict):
        """detailed_openings 검증 및 보정"""
        if "openings_found" not in text_analysis:
            return

        text_openings = text_analysis["openings_found"]
        detailed_openings = result.get("detailed_openings", [])

        logger.info(f"Text analysis found {len(text_openings)} openings")
        logger.info(f"Structured analysis included {len(detailed_openings)} detailed openings")

        # 개수가 맞지 않으면 경고하고 보정
        if len(text_openings) != len(detailed_openings):
            logger.warning(f"Opening count mismatch: text={len(text_openings)}, detailed={len(detailed_openings)}")

            # 부족한 경우 기본 정보로 채우기
            if len(detailed_openings) < len(text_openings):
                logger.info("Adding missing openings to detailed_openings")
                for i in range(len(detailed_openings), len(text_openings)):
                    text_opening = text_openings[i]
                    opening_type = text_opening.get("type", "Unknown")

                    # "Window - Goes to Floor"는 Window로 분류
                    if "Window" in opening_type:
                        # 연결처를 확인해서 내부/외부 판단
                        connection = text_opening.get("connection", "")
                        is_exterior = "Exterior" in connection or connection == ""
                        # STORAGE_AREA 같은 내부 공간으로 연결되면 내부 창문
                        if any(room_name in connection.upper() for room_name in ["ROOM", "AREA", "CLOSET", "HALL"]):
                            is_exterior = False

                        default_opening = {
                            "type": "Window",
                            "width_ft": 2.5,
                            "height_ft": 6.0 if "Goes to Floor" in opening_type else 4.0,
                            "area_s": 15.0 if "Goes to Floor" in opening_type else 10.0,
                            "location": "Exterior" if is_exterior else "Interior",
                            "connects_to": connection if connection else "Exterior",
                            "is_exterior": is_exterior
                        }
                    elif "Door" in opening_type:
                        default_opening = {
                            "type": "Door",
                            "width_ft": 3.0,
                            "height_ft": 6.67,
                            "area_s": 20.0,
                            "location": "Interior",
                            "connects_to": text_opening.get("connection", "Unknown"),
                            "is_exterior": "Exterior" in text_opening.get("connection", "")
                        }
                    elif "Missing Wall" in opening_type:
                        default_opening = {
                            "type": "Missing Wall",
                            "width_ft": 4.0,
                            "height_ft": 6.67,
                            "area_s": 26.68,
                            "location": "Interior",
                            "connects_to": text_opening.get("connection", "Unknown"),
                            "is_exterior": False
                        }
                    else:
                        default_opening = {
                            "type": opening_type,
                            "width_ft": 3.0,
                            "height_ft": 6.67,
                            "area_s": 20.0,
                            "location": "Unknown",
                            "connects_to": text_opening.get("connection", "Unknown"),
                            "is_exterior": False
                        }

                    detailed_openings.append(default_opening)

                result["detailed_openings"] = detailed_openings
                logger.info(f"Updated detailed_openings count to {len(detailed_openings)}")

    def _ensure_floor_perimeter(self, result: Dict):
        """floor_perimeter_lf 확보"""
        extracted_dims = result.get("extracted_dimensions", {})

        if "floor_perimeter_l" not in extracted_dims or extracted_dims["floor_perimeter_l"] <= 0:
            # perimeter_lf나 ceiling_perimeter_lf 사용
            floor_perimeter = extracted_dims.get("perimeter_l", 0)
            if floor_perimeter <= 0:
                floor_perimeter = extracted_dims.get("ceiling_perimeter_l", 0)

            extracted_dims["floor_perimeter_l"] = floor_perimeter
            logger.info(f"Added floor_perimeter_lf: {floor_perimeter}")

            # room_geometry에도 추가
            if "room_geometry" in result:
                result["room_geometry"]["floor_perimeter_l"] = floor_perimeter

    def _recalculate_baseboard(self, result: Dict):
        """베이스보드 길이 재계산 - floor_perimeter 사용"""
        try:
            extracted_dims = result.get("extracted_dimensions", {})
            openings_summary = result.get("openings_summary", {})

            # floor_perimeter 우선 사용, 없으면 perimeter_lf 사용
            floor_perimeter = extracted_dims.get("floor_perimeter_l", 0)
            if floor_perimeter <= 0:
                floor_perimeter = extracted_dims.get("perimeter_l", 0)
            if floor_perimeter <= 0:
                floor_perimeter = extracted_dims.get("ceiling_perimeter_l", 0)

            # 문 총 폭
            door_width_total = openings_summary.get("door_width_total_ft", 0)

            # 개방구간 총 폭
            open_area_width_total = openings_summary.get("open_area_width_total_ft", 0)

            # 베이스보드 길이 계산
            baseboard_length = max(0, floor_perimeter - door_width_total - open_area_width_total)

            # calculated_materials 업데이트
            if "calculated_materials" not in result:
                result["calculated_materials"] = {}

            result["calculated_materials"]["baseboard_length_l"] = baseboard_length

            logger.info(f"Baseboard recalculation (using floor_perimeter): {floor_perimeter} - {door_width_total} - {open_area_width_total} = {baseboard_length}")

        except Exception as e:
            logger.error(f"Error during baseboard recalculation: {e}")

    def _clean_json_string(self, json_str: str) -> str:
        """Clean JSON string to make it parseable"""
        import re

        # Remove comments
        json_str = re.sub(r'//.*?\n', '\n', json_str)
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)

        # Convert single quotes to double quotes
        json_str = re.sub(r"'([^']*)':", r'"\1":', json_str)
        json_str = re.sub(r":\s*'([^']*)'", r': "\1"', json_str)

        # Fix unquoted property names
        json_str = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_str)

        # Remove trailing commas
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)

        return json_str

    def _sanitize_result(self, result):
        """Replace None values and validate ranges, but preserve zero values from failed analysis"""

        # extracted_dimensions 처리
        if "extracted_dimensions" in result:
            dims = result["extracted_dimensions"]
            # None만 0으로 변경, 0 값은 그대로 유지 (분석 실패 표시)
            dims["ceiling_height_ft"] = safe_float(dims.get("ceiling_height_ft"), 0.0)
            dims["floor_area_s"] = safe_float(dims.get("floor_area_s"), 0.0)
            dims["room_area_s"] = safe_float(dims.get("room_area_s"), 0.0)
            dims["wall_area_s"] = safe_float(dims.get("wall_area_s"), 0.0)
            dims["ceiling_area_s"] = safe_float(dims.get("ceiling_area_s"), 0.0)
            dims["perimeter_l"] = safe_float(dims.get("perimeter_l"), 0.0)
            dims["ceiling_perimeter_l"] = safe_float(dims.get("ceiling_perimeter_l"), 0.0)
            dims["floor_perimeter_l"] = safe_float(dims.get("floor_perimeter_l"), 0.0)

        # room_geometry 처리
        if "room_geometry" in result:
            geo = result["room_geometry"]
            geo["total_floor_area_s"] = safe_float(geo.get("total_floor_area_s"), 0.0)
            geo["ceiling_height_ft"] = safe_float(geo.get("ceiling_height_ft"), 0.0)
            geo["total_perimeter_l"] = safe_float(geo.get("total_perimeter_l"), 0.0)
            geo["floor_perimeter_l"] = safe_float(geo.get("floor_perimeter_l"), 0.0)

        # openings_summary 처리
        if "openings_summary" in result:
            openings = result["openings_summary"]
            openings["total_doors"] = int(safe_float(openings.get("total_doors"), 0))
            openings["total_windows"] = int(safe_float(openings.get("total_windows"), 0))
            openings["total_open_areas"] = int(safe_float(openings.get("total_open_areas"), 0))
            openings["door_width_total_ft"] = safe_float(openings.get("door_width_total_ft"), 0.0)
            openings["window_area_total_s"] = safe_float(openings.get("window_area_total_s"), 0.0)
            openings["open_area_width_total_ft"] = safe_float(openings.get("open_area_width_total_ft"), 0.0)
            openings["total_interior_doors"] = int(safe_float(openings.get("total_interior_doors"), 0))
            openings["total_exterior_doors"] = int(safe_float(openings.get("total_exterior_doors"), 0))

        # calculated_materials 처리
        if "calculated_materials" in result:
            materials = result["calculated_materials"]
            materials["baseboard_length_l"] = safe_float(materials.get("baseboard_length_l"), 0.0)
            materials["crown_molding_length_l"] = safe_float(materials.get("crown_molding_length_l"), 0.0)
            materials["flooring_area_s"] = safe_float(materials.get("flooring_area_s"), 0.0)
            materials["wall_paint_area_s"] = safe_float(materials.get("wall_paint_area_s"), 0.0)
            materials["ceiling_paint_area_s"] = safe_float(materials.get("ceiling_paint_area_s"), 0.0)

        # 분석 실패 플래그 확인 및 경고 추가
        if result.get("confidence_level") == "failed":
            result["analysis_notes"] = "Analysis failed - All values are 0. Manual data entry required."
            result["requires_manual_input"] = True

        return result

    def _get_default_result(self):
        """Return default result structure with null/zero values to indicate analysis failure"""
        return {
            "room_identification": {
                "detected_room_name": "ANALYSIS_FAILED",
                "room_shape": "unknown",
                "confidence_level": "failed",
                "image_type": "unknown"
            },
            "extracted_dimensions": {
                "ceiling_height_ft": 0.0,
                "floor_area_s": 0.0,
                "room_area_s": 0.0,
                "wall_area_s": 0.0,
                "ceiling_area_s": 0.0,
                "perimeter_l": 0.0,
                "ceiling_perimeter_l": 0.0,
                "floor_perimeter_l": 0.0
            },
            "room_geometry": {
                "total_floor_area_s": 0.0,
                "ceiling_height_ft": 0.0,
                "total_perimeter_l": 0.0,
                "floor_perimeter_l": 0.0
            },
            "openings_summary": {
                "total_doors": 0,
                "total_windows": 0,
                "total_open_areas": 0,
                "total_interior_doors": 0,
                "total_exterior_doors": 0,
                "door_width_total_ft": 0.0,
                "window_area_total_s": 0.0,
                "open_area_width_total_ft": 0.0
            },
            "detailed_openings": [],
            "calculated_materials": {
                "baseboard_length_l": 0.0,
                "crown_molding_length_l": 0.0,
                "flooring_area_s": 0.0,
                "wall_paint_area_s": 0.0,
                "ceiling_paint_area_s": 0.0
            },
            "confidence_level": "failed",
            "analysis_notes": "Image analysis failed - manual input required",
            "dimension_source": "analysis_failed",
            "requires_manual_input": True
        }

    def _get_error_result(self, error_message: str):
        """Return error result"""
        result = self._get_default_result()
        result["error"] = error_message
        result["analysis_notes"] = f"Analysis failed: {error_message}"
        return result
