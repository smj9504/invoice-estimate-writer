import streamlit as st
import uuid
import re
from modules.estimate_module import (
    get_all_items, get_item_by_id, insert_item, update_item, delete_item,
    get_descriptions_by_item_id, insert_multiple_descriptions, replace_item_descriptions,
    update_description, delete_description, get_item_by_code
)

def generate_item_code(category, item_name):
    """
    카테고리와 아이템명으로 코드를 자동 생성
    예: Cabinetry + appliance garage → CABAG
    """
    if not category or not item_name:
        return f"AUTO-{uuid.uuid4().hex[:6]}"

    # 카테고리의 첫 3글자 (대문자)
    category_prefix = re.sub(r'[^A-Za-z]', '', category)[:3].upper()

    # 아이템명에서 중요한 단어들 추출 (전치사, 관사 제외)
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'o', 'with', 'by'}

    # 아이템명을 단어들로 분할하고 정리 (하이픈, 콤마 등도 구분자로 사용)
    words = re.findall(r'\b[A-Za-z]+\b', item_name.lower())
    important_words = [word for word in words if word not in stop_words and len(word) > 1]

    if not important_words:
        # 중요한 단어가 없으면 모든 단어 사용
        important_words = [word for word in words if len(word) > 1]

    # 각 중요한 단어의 첫 글자들을 조합
    if len(important_words) == 1:
        # 단어가 1개면 그 단어의 첫 4글자까지
        item_suffix = important_words[0][:4].upper()
    elif len(important_words) == 2:
        # 단어가 2개면 각각 2글자씩 또는 첫 글자들
        first_word = important_words[0]
        second_word = important_words[1]

        if len(first_word) >= 2 and len(second_word) >= 2:
            item_suffix = first_word[:2].upper() + second_word[:2].upper()
        else:
            item_suffix = first_word[0].upper() + second_word[0].upper()
    else:
        # 단어가 3개 이상이면 첫 번째 단어는 2-3글자, 나머지는 첫 글자
        first_word = important_words[0]
        other_words = important_words[1:3]  # 최대 2개까지만

        if len(first_word) >= 3:
            item_suffix = first_word[:2].upper() + ''.join([word[0].upper() for word in other_words])
        else:
            item_suffix = first_word.upper() + ''.join([word[0].upper() for word in other_words])

    # 최종 코드 생성 (최대 8글자로 제한)
    generated_code = (category_prefix + item_suffix)[:8]

    # 코드가 너무 짧으면 보완
    if len(generated_code) < 4:
        generated_code += uuid.uuid4().hex[:2].upper()

    return generated_code

# 🔁 상태 초기화
if "edit_item_id" not in st.session_state:
    st.session_state.edit_item_id = None
if "selected_category" not in st.session_state:
    st.session_state.selected_category = "전체"
if "selected_subcategory" not in st.session_state:
    st.session_state.selected_subcategory = "전체"
if "descriptions" not in st.session_state:
    st.session_state.descriptions = []

# 📄 항목 목록 불러오기
try:
    all_items = get_all_items()
    if all_items is None:
        all_items = []
except Exception as e:
    st.error(f"항목을 불러오는 중 오류가 발생했습니다: {e}")
    all_items = []

# 🔍 수정 항목 불러오기
edit_item = None
if st.session_state.edit_item_id:
    try:
        edit_item = get_item_by_id(st.session_state.edit_item_id)
        if edit_item and not st.session_state.descriptions:
            # 기존 설명들 불러오기
            descriptions = get_descriptions_by_item_id(edit_item["id"])
            st.session_state.descriptions = [
                {
                    "id": desc.get("id"),
                    "description": desc.get("description", ""),
                    "tag": desc.get("tag", ""),
                    "sort_order": desc.get("sort_order", 1)
                }
                for desc in descriptions
            ]
    except Exception as e:
        st.error(f"항목을 불러오는 중 오류가 발생했습니다: {e}")
        st.session_state.edit_item_id = None

# 📝 항목 등록/수정 폼
st.subheader("➕ 항목 등록 / 수정")

# 코드 생성 규칙 설명
with st.expander("💡 자동 코드 생성 규칙"):
    st.markdown("""
    **코드를 비워두면 다음 규칙으로 자동 생성됩니다:**
    - 카테고리 첫 3글자 + 아이템명의 주요 단어 조합
    - 예시:
        - Cabinetry + appliance garage → **CABAG** (CAB + A + G)
        - Cabinetry + wood panel → **CABWOPA** (CAB + WO + PA)
        - Backsplash + stainless steel → **BACSTST** (BAC + ST + ST)
        - Service + counter → **SERCOUN** (SER + COUN)
    - 중복되는 경우 숫자가 자동으로 추가됩니다 (예: CABAG1, CABAG2...)
    - 최대 8글자로 제한됩니다
    """)

    # 실시간 예시 생성기
    st.markdown("**실시간 코드 생성 테스트:**")
    test_cols = st.columns(2)
    with test_cols[0]:
        test_category = st.text_input("테스트 카테고리", value="Cabinetry", key="test_cat")
    with test_cols[1]:
        test_item = st.text_input("테스트 아이템명", value="appliance garage", key="test_item")

    if test_category and test_item:
        test_code = generate_item_code(test_category, test_item)
        st.code(f"생성될 코드: {test_code}")

# ==========================================
# 📝 설명 관리 섹션 (폼 밖에서 관리)
# ==========================================
st.markdown("### 📝 설명 관리")

# 설명 관리 버튼들
desc_button_cols = st.columns([1, 1, 1, 1])
with desc_button_cols[0]:
    if st.button("➕ 설명 추가"):
        st.session_state.descriptions.append({
            "id": None,
            "description": "",
            "tag": "",
            "sort_order": len(st.session_state.descriptions) + 1
        })
        st.rerun()

with desc_button_cols[1]:
    if st.button("🔄 순서 재정렬"):
        # 순서 재정렬
        for i, desc in enumerate(st.session_state.descriptions):
            desc["sort_order"] = i + 1
        st.rerun()

with desc_button_cols[2]:
    if st.button("🗑️ 모든 설명 삭제"):
        st.session_state.descriptions = []
        st.rerun()

with desc_button_cols[3]:
    # 빈 설명 제거
    if st.button("🧹 빈 설명 정리"):
        st.session_state.descriptions = [
            desc for desc in st.session_state.descriptions
            if desc["description"].strip()
        ]
        st.rerun()

# 설명 입력 필드들
for i, desc in enumerate(st.session_state.descriptions):
    with st.container():
        st.markdown(f"**설명 {i+1}**")
        desc_inner_cols = st.columns([4, 2, 1, 1])

        with desc_inner_cols[0]:
            new_description = st.text_area(
                "설명 내용",
                value=desc["description"],
                key=f"desc_content_{i}",
                height=80,
                label_visibility="collapsed"
            )
            st.session_state.descriptions[i]["description"] = new_description

        with desc_inner_cols[1]:
            new_tag = st.text_input(
                "태그",
                value=desc["tag"],
                key=f"desc_tag_{i}",
                placeholder="예: 주의사항, 포함사항",
                label_visibility="collapsed"
            )
            st.session_state.descriptions[i]["tag"] = new_tag

        with desc_inner_cols[2]:
            new_sort_order = st.number_input(
                "순서",
                min_value=1,
                value=desc["sort_order"],
                key=f"desc_order_{i}",
                label_visibility="collapsed"
            )
            st.session_state.descriptions[i]["sort_order"] = new_sort_order

        with desc_inner_cols[3]:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            if st.button("🗑️", key=f"remove_desc_{i}", help=f"설명 {i+1} 삭제"):
                st.session_state.descriptions.pop(i)
                st.rerun()

        st.markdown("---")

# 설명 미리보기
if st.session_state.descriptions:
    st.markdown("**📋 설명 미리보기:**")
    sorted_descriptions = sorted(st.session_state.descriptions, key=lambda x: x["sort_order"])
    for desc in sorted_descriptions:
        if desc["description"].strip():
            tag_display = f"[{desc['tag']}] " if desc["tag"].strip() else ""
            st.info(f"{tag_display}{desc['description']}")

st.markdown("---")

# 카테고리 및 서브카테고리 추출 (폼에서 사용하기 위해 미리 계산)
all_categories = sorted(set(item.get('category', '') for item in all_items if item.get('category')))
all_subcategories = sorted(set(item.get('subcategory', '') for item in all_items if item.get('subcategory')))

with st.form("item_form"):
    code = st.text_input("코드", value=edit_item["code"] if edit_item else "")

    # 카테고리 입력 (기존 선택 또는 새로 입력)
    form_col1, form_col2 = st.columns(2)
    with form_col1:
        st.markdown("**카테고리**")
        category_options = ["새로 입력..."] + sorted(all_categories) if all_categories else ["새로 입력..."]

        # 수정 모드일 때 기존 카테고리가 목록에 있으면 선택, 없으면 "새로 입력" 선택
        if edit_item and edit_item["category"] in all_categories:
            category_default_idx = category_options.index(edit_item["category"])
        else:
            category_default_idx = 0  # "새로 입력..." 선택

        category_choice = st.selectbox(
            "기존 카테고리 선택",
            category_options,
            index=category_default_idx,
            key="category_choice"
        )

        if category_choice == "새로 입력...":
            category = st.text_input(
                "새 카테고리 입력",
                value=edit_item["category"] if edit_item and edit_item["category"] not in all_categories else "",
                placeholder="예: Cabinetry, Electrical, Plumbing"
            )
        else:
            category = category_choice
            st.success(f"✅ 선택된 카테고리: {category}")

    with form_col2:
        st.markdown("**서브카테고리**")
        # 선택된 카테고리에 따른 서브카테고리 옵션
        if category and category != "새로 입력...":
            category_subcategories = sorted(set(
                item.get('subcategory', '')
                for item in all_items
                if item.get('category') == category and item.get('subcategory')
            ))
        else:
            category_subcategories = sorted(all_subcategories) if all_subcategories else []

        subcategory_options = ["없음", "새로 입력..."] + category_subcategories if category_subcategories else ["없음",
            "새로 입력..."]

        # 수정 모드일 때 기존 서브카테고리 처리
        if edit_item and edit_item.get("subcategory"):
            if edit_item["subcategory"] in category_subcategories:
                subcategory_default_idx = subcategory_options.index(edit_item["subcategory"])
            else:
                subcategory_default_idx = 1  # "새로 입력..." 선택
        else:
            subcategory_default_idx = 0  # "없음" 선택

        subcategory_choice = st.selectbox(
            "기존 서브카테고리 선택",
            subcategory_options,
            index=subcategory_default_idx,
            key="subcategory_choice"
        )

        if subcategory_choice == "새로 입력...":
            subcategory = st.text_input(
                "새 서브카테고리 입력",
                value=edit_item["subcategory"] if edit_item and edit_item.get("subcategory") not in category_subcategories else "",

                placeholder="예: Kitchen Cabinets, Bathroom Cabinets"
            )
        elif subcategory_choice == "없음":
            subcategory = ""
        else:
            subcategory = subcategory_choice
            st.success(f"✅ 선택된 서브카테고리: {subcategory}")

    name = st.text_input("아이템 이름", value=edit_item["name"] if edit_item else "")

    form_col3, form_col4 = st.columns(2)
    with form_col3:
        st.markdown("**단위**")
        # 일반적인 단위 옵션
        common_units = ["EA", "SQ", "LF", "SF", "HR"]
        unit_options = ["직접 입력..."] + common_units

        # 수정 모드일 때 기존 단위가 일반 단위 목록에 있으면 선택, 없으면 "직접 입력" 선택
        if edit_item and edit_item.get("unit") in common_units:
            unit_default_idx = unit_options.index(edit_item["unit"])
        else:
            unit_default_idx = 0  # "직접 입력..." 선택

        unit_choice = st.selectbox(
            "일반 단위 선택",
            unit_options,
            index=unit_default_idx,
            key="unit_choice"
        )

        if unit_choice == "직접 입력...":
            unit = st.text_input(
                "단위 직접 입력",
                value=edit_item["unit"] if edit_item and edit_item.get("unit") not in common_units else "",
                placeholder="예: KG, M, SET, etc."
            )
        else:
            unit = unit_choice
            st.success(f"✅ 선택된 단위: {unit}")

        # 단위별 설명 표시
        unit_descriptions = {
            "EA": "개 (Each)",
            "SQ": "제곱 (Square)",
            "LF": "선형 피트 (Linear Feet)",
            "SF": "제곱 피트 (Square Feet)",
            "HR": "시간 (Hour)"
        }

        if unit in unit_descriptions:
            st.caption(f"💡 {unit_descriptions[unit]}")

    with form_col4:
        price = st.number_input("단가", value=edit_item["unit_price"] if edit_item else 0.0, step=1.0)

    # 카테고리/서브카테고리 미리보기
    if category and category != "새로 입력...":
        category_preview = f"📁 **{category}"
        if subcategory:
            category_preview += f" > {subcategory}"
        category_preview += "**"
        st.markdown(category_preview)

    # 코드 미리보기 (코드가 비어있고 카테고리와 아이템명이 있을 때)
    if not code.strip() and category.strip() and name.strip() and category != "새로 입력...":
        preview_code = generate_item_code(category, name)
        st.info(f"💡 자동 생성될 코드: **{preview_code}**")

    # 폼 제출 버튼
    submitted = st.form_submit_button("💾 저장", type="primary")

    if submitted:
        # 입력 검증
        if not category or category == "새로 입력...":
            st.error("❌ 카테고리를 입력해주세요.")
        elif not name.strip():
            st.error("❌ 아이템 이름을 입력해주세요.")
        else:
            try:
                if not code.strip():
                    # 카테고리와 아이템명으로 코드 자동 생성
                    code = generate_item_code(category, name)

                existing = get_item_by_code(code.strip())
                if existing and (not edit_item or existing["id"] != edit_item["id"]):
                    # 코드가 중복되면 숫자를 추가해서 유니크하게 만들기
                    base_code = code.strip()
                    counter = 1
                    while existing and (not edit_item or existing["id"] != edit_item["id"]):
                        code = f"{base_code}{counter}"
                        existing = get_item_by_code(code)
                        counter += 1
                        if counter > 99:  # 무한 루프 방지
                            code = f"{base_code}-{uuid.uuid4().hex[:4].upper()}"
                            break
                    st.info(f"💡 코드가 중복되어 **{code}**로 저장됩니다.")

                # 데이터 저장
                data = {
                    "code": code.strip(),
                    "category": category.strip(),
                    "subcategory": subcategory.strip() if subcategory else "",
                    "name": name.strip(),
                    "unit": unit.strip(),
                    "unit_price": price
                }

                if edit_item:
                    update_item(edit_item["id"], data)
                    item_id = edit_item["id"]
                    st.success("✅ 항목 수정 완료")

                    # 새 카테고리나 서브카테고리가 추가된 경우 알림
                    if category not in all_categories:
                        st.success(f"🆕 새 카테고리 '{category}' 추가됨")
                    if subcategory and subcategory not in all_subcategories:
                        st.success(f"🆕 새 서브카테고리 '{subcategory}' 추가됨")
                else:
                    result = insert_item(data)
                    if result and result.data:
                        item_id = result.data[0]["id"]
                        st.success("✅ 새 항목 등록 완료")

                        # 새 카테고리나 서브카테고리가 추가된 경우 알림
                        if category not in all_categories:
                            st.success(f"🆕 새 카테고리 '{category}' 추가됨")
                        if subcategory and subcategory not in all_subcategories:
                            st.success(f"🆕 새 서브카테고리 '{subcategory}' 추가됨")
                    else:
                        st.error("항목 저장에 실패했습니다.")
                        item_id = None

                # 설명 저장
                if item_id and st.session_state.descriptions:
                    # 빈 설명 제거
                    valid_descriptions = [
                        desc for desc in st.session_state.descriptions
                        if desc["description"].strip()
                    ]

                    if valid_descriptions:
                        try:
                            replace_item_descriptions(item_id, valid_descriptions)
                            st.success(f"✅ {len(valid_descriptions)}개의 설명 저장 완료")
                        except Exception as e:
                            st.error(f"설명 저장 중 오류: {e}")

                # 상태 초기화
                st.session_state.edit_item_id = None
                st.session_state.descriptions = []
                st.rerun()

            except Exception as e:
                st.error(f"저장 중 오류가 발생했습니다: {e}")

# 취소 버튼 (수정 모드일 때만 표시)
if edit_item:
    cancel_cols = st.columns([1, 1])
    with cancel_cols[0]:
        if st.button("❌ 수정 취소"):
            st.session_state.edit_item_id = None
            st.session_state.descriptions = []
            st.rerun()
    with cancel_cols[1]:
        if st.button("🆕 새 항목으로 전환"):
            st.session_state.edit_item_id = None
            st.session_state.descriptions = []
            st.rerun()
else:
    # 새 항목 등록 시 설명 초기화 버튼
    if st.session_state.descriptions:
        if st.button("🔄 새 항목으로 초기화"):
            st.session_state.descriptions = []
            st.rerun()

st.markdown("---")

# 🔍 필터링 UI
st.subheader("🔍 항목 필터링")

# 카테고리 및 서브카테고리 추출
all_categories = sorted(set(item.get('category', '') for item in all_items if item.get('category')))
all_subcategories = sorted(set(item.get('subcategory', '') for item in all_items if item.get('subcategory')))

col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    # 카테고리 선택
    category_options = ["전체"] + all_categories
    selected_category = st.selectbox(
        "🏷️ 카테고리 선택",
        category_options,
        index=category_options.index(st.session_state.selected_category) if st.session_state.selected_category in category_options else 0,

        key="category_filter"
    )
    st.session_state.selected_category = selected_category

with col2:
    # 선택된 카테고리에 따른 서브카테고리 필터링
    if selected_category == "전체":
        subcategory_options = ["전체"] + all_subcategories
    else:
        filtered_subcategories = sorted(set(
            item.get('subcategory', '')
            for item in all_items
            if item.get('category') == selected_category and item.get('subcategory')
        ))
        subcategory_options = ["전체"] + filtered_subcategories

    # 이전 선택이 현재 옵션에 없으면 "전체"로 리셋
    if st.session_state.selected_subcategory not in subcategory_options:
        st.session_state.selected_subcategory = "전체"

    selected_subcategory = st.selectbox(
        "🏷️ 서브카테고리 선택",
        subcategory_options,
        index=subcategory_options.index(st.session_state.selected_subcategory) if st.session_state.selected_subcategory in subcategory_options else 0,

        key="subcategory_filter"
    )
    st.session_state.selected_subcategory = selected_subcategory

with col3:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    if st.button("🔄 필터 초기화"):
        st.session_state.selected_category = "전체"
        st.session_state.selected_subcategory = "전체"
        st.rerun()

# 필터링된 항목 목록
filtered_items = all_items

if selected_category != "전체":
    filtered_items = [item for item in filtered_items if item.get('category') == selected_category]

if selected_subcategory != "전체":
    filtered_items = [item for item in filtered_items if item.get('subcategory') == selected_subcategory]

# 필터링 결과 표시
filter_info = []
if selected_category != "전체":
    filter_info.append(f"카테고리: **{selected_category}**")
if selected_subcategory != "전체":
    filter_info.append(f"서브카테고리: **{selected_subcategory}**")

if filter_info:
    st.info(f"🔍 필터 적용됨 - {' | '.join(filter_info)} ({len(filtered_items)}개 항목)")
else:
    st.info(f"📋 전체 항목 표시 ({len(filtered_items)}개 항목)")

st.markdown("---")

# 📋 필터링된 항목 목록 표시
st.subheader("📋 견적 항목 목록")

if not filtered_items:
    st.warning("선택된 조건에 해당하는 항목이 없습니다.")
else:
    # 테이블 헤더
    header_cols = st.columns([4, 1, 1, 1, 1, 1])
    header_cols[0].markdown("**항목명 (카테고리)**")
    header_cols[1].markdown("**단위**")
    header_cols[2].markdown("**단가**")
    header_cols[3].markdown("**생성일**")
    header_cols[4].markdown("**수정**")
    header_cols[5].markdown("**삭제**")

    st.markdown("---")

    for item in filtered_items:
        with st.container():
            cols = st.columns([4, 1, 1, 1, 1, 1])

            # 항목명과 카테고리/서브카테고리 표시
            category_text = item.get('category', '')
            subcategory_text = item.get('subcategory', '')

            if subcategory_text:
                category_display = f"{category_text} > {subcategory_text}"
            else:
                category_display = category_text

            cols[0].markdown(f"**{item['name']}**")
            cols[0].caption(f"📁 {category_display}")

            cols[1].markdown(f"{item.get('unit', '')}")
            cols[2].markdown(f"${item.get('unit_price', 0):.2f}")
            cols[3].markdown(item.get("created_at", "-"))

            if cols[4].button("✏️", key=f"edit-{item['id']}", help="수정"):
                st.session_state.edit_item_id = item["id"]
                # 수정 모드일 때 기존 설명들 불러오기
                try:
                    descriptions = get_descriptions_by_item_id(item["id"])
                    st.session_state.descriptions = [
                        {
                            "id": desc.get("id"),
                            "description": desc.get("description", ""),
                            "tag": desc.get("tag", ""),
                            "sort_order": desc.get("sort_order", 1)
                        }
                        for desc in descriptions
                    ]
                except Exception as e:
                    st.session_state.descriptions = []
                st.rerun()

            if cols[5].button("🗑️", key=f"delete-{item['id']}", help="삭제"):
                try:
                    delete_item(item["id"])
                    st.success(f"🗑️ '{item['name']}' 삭제 완료")
                    st.rerun()
                except Exception as e:
                    st.error(f"삭제 중 오류가 발생했습니다: {e}")
