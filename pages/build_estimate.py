import streamlit as st
import datetime
import re
from modules.company_module import get_all_companies  
from modules.estimate_item_module import get_all_items
from modules.estimate_module import get_estimate_by_id, get_descriptions_by_item_id
from weasyprint import HTML, CSS

st.set_page_config(page_title="Estimate Builder", page_icon="📟", layout="wide")

# 세션 상태 초기화
if "sections" not in st.session_state:
    st.session_state.sections = []
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.from_page = ""

# 트리거 처리 (페이지 최상단에서 모든 액션 처리)
# 섹션 추가 트리거
if "add_section_trigger" in st.session_state:
    title, show_subtotal = st.session_state.add_section_trigger
    st.session_state.sections.append({
        "title": title,
        "items": [],
        "showSubtotal": show_subtotal,
        "subtotal": 0.0
    })
    del st.session_state.add_section_trigger

# 섹션 삭제 트리거
if "delete_section_trigger" in st.session_state:
    section_idx = st.session_state.delete_section_trigger
    if 0 <= section_idx < len(st.session_state.sections):
        st.session_state.sections.pop(section_idx)
    del st.session_state.delete_section_trigger

# 섹션 이름 업데이트 트리거
if "update_section_title_trigger" in st.session_state:
    section_idx, new_title = st.session_state.update_section_title_trigger
    if 0 <= section_idx < len(st.session_state.sections):
        st.session_state.sections[section_idx]["title"] = new_title
    del st.session_state.update_section_title_trigger

# 항목 추가 트리거
if "add_items_trigger" in st.session_state:
    section_idx, items_to_add = st.session_state.add_items_trigger
    if 0 <= section_idx < len(st.session_state.sections):
        for item in items_to_add:
            # 중복 체크
            if not any(existing_item["code"] == item["code"] for existing_item in st.session_state.sections[section_idx]["items"]):
                # 항목의 description들 불러오기
                try:
                    descriptions = get_descriptions_by_item_id(item["id"])
                    available_descriptions = []
                    if descriptions:
                        for desc in descriptions:
                            available_descriptions.append({
                                "id": desc["id"],
                                "text": f"{desc['description']}",
                                "tag": desc.get("tag", ""),
                                "description": desc["description"],
                                "sort_order": desc.get("sort_order", 1)
                            })
                        # 정렬
                        available_descriptions.sort(key=lambda x: x["sort_order"])
                except Exception as e:
                    available_descriptions = []
                
                st.session_state.sections[section_idx]["items"].append({
                    "code": item["code"],
                    "name": item["name"], 
                    "unit": item["unit"],
                    "price": item["unit_price"],
                    "qty": 1.0,
                    "dec": "",
                    "item_id": item["id"],  # 항목 ID 저장
                    "available_descriptions": available_descriptions,  # 사용 가능한 설명들
                    "selected_descriptions": [],  # 선택된 설명들
                    "manual_description": ""  # 수동 입력 설명
                })
    del st.session_state.add_items_trigger

# 수동 항목 추가 트리거
if "manual_add_trigger" in st.session_state:
    section_idx = st.session_state.manual_add_trigger
    if 0 <= section_idx < len(st.session_state.sections):
        st.session_state.sections[section_idx]["items"].append({
            "code": "",
            "name": "",
            "unit": "",
            "price": 0.0,
            "qty": 1.0,
            "dec": "",
            "item_id": None,
            "available_descriptions": [],
            "selected_descriptions": [],
            "manual_description": ""
        })
    del st.session_state.manual_add_trigger

# 항목 삭제 트리거
if "delete_item_trigger" in st.session_state:
    section_idx, item_idx = st.session_state.delete_item_trigger
    if (0 <= section_idx < len(st.session_state.sections) and 
        0 <= item_idx < len(st.session_state.sections[section_idx]["items"])):
        st.session_state.sections[section_idx]["items"].pop(item_idx)
    del st.session_state.delete_item_trigger

# 항목 순서 변경 트리거 (위로 이동)
if "move_item_up_trigger" in st.session_state:
    section_idx, item_idx = st.session_state.move_item_up_trigger
    if (0 <= section_idx < len(st.session_state.sections) and 
        1 <= item_idx < len(st.session_state.sections[section_idx]["items"])):
        # 현재 항목과 위의 항목 위치 바꾸기
        items = st.session_state.sections[section_idx]["items"]
        items[item_idx], items[item_idx-1] = items[item_idx-1], items[item_idx]
    del st.session_state.move_item_up_trigger

# 항목 순서 변경 트리거 (아래로 이동)
if "move_item_down_trigger" in st.session_state:
    section_idx, item_idx = st.session_state.move_item_down_trigger
    if (0 <= section_idx < len(st.session_state.sections) and 
        0 <= item_idx < len(st.session_state.sections[section_idx]["items"]) - 1):
        # 현재 항목과 아래의 항목 위치 바꾸기
        items = st.session_state.sections[section_idx]["items"]
        items[item_idx], items[item_idx+1] = items[item_idx+1], items[item_idx]
    del st.session_state.move_item_down_trigger

# URL 파라미터에서 ID 추출
query_params = st.query_params
raw_id = query_params.get("id")
estimate_id = raw_id[0] if isinstance(raw_id, list) else raw_id
uuid_pattern = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")

# 기존 견적서 로드
if estimate_id and uuid_pattern.match(estimate_id):
    if "estimate_loaded" not in st.session_state:
        estimate = get_estimate_by_id(estimate_id)
        if estimate:
            st.title("📄 견적서 수정")
            data = estimate.get("json_data", {})

            # 섹션 데이터 로드 및 description 필드 초기화
            loaded_sections = data.get("serviceSections", [])
            for section in loaded_sections:
                for item in section.get("items", []):
                    # 기존 항목에 description 관련 필드가 없으면 초기화
                    if "item_id" not in item:
                        item["item_id"] = None
                    if "available_descriptions" not in item:
                        item["available_descriptions"] = []
                    if "selected_descriptions" not in item:
                        item["selected_descriptions"] = []
                    if "manual_description" not in item:
                        item["manual_description"] = ""
                    
                    # 기존 설명이 있으면 수동 설명으로 이동
                    if item.get("dec") and not item.get("manual_description"):
                        item["manual_description"] = item["dec"]
            
            st.session_state.sections = loaded_sections
            st.session_state.estimate_number = data.get("estimate_number", "")
            st.session_state.estimate_date = data.get("estimate_date", datetime.date.today())

            client = data.get("client", {})
            st.session_state.client_name = client.get("name", "")
            st.session_state.client_phone = client.get("phone", "")
            st.session_state.client_email = client.get("email", "")
            st.session_state.client_street = client.get("address", "")
            st.session_state.client_city = client.get("city", "")
            st.session_state.client_state = client.get("state", "")
            st.session_state.client_zip = client.get("zip", "")

            st.session_state.top_note = data.get("top_note", "")
            st.session_state.bottom_note = data.get("bottom_note", "")
            st.session_state.disclaimer = data.get("disclaimer", "")
            st.session_state.op_percent = data.get("op_percent", 0.0)
            st.session_state.selected_company = data.get("company", {})
            st.session_state.from_page = "build_estimate"
            st.session_state.estimate_loaded = True
        else:
            st.error("❌ 해당 ID의 견적서를 찾을 수 없습니다.")
            st.stop()
elif estimate_id:
    st.error("❌ 유효하지 않은 ID 형식입니다.")
    st.stop()
else:
    # 새 견적서 기본값 설정
    if "new_estimate_initialized" not in st.session_state:
        st.session_state.estimate_number = "EST-001"
        st.session_state.estimate_date = datetime.date.today()
        st.session_state.client_name = ""
        st.session_state.client_phone = ""
        st.session_state.client_email = ""
        st.session_state.client_street = ""
        st.session_state.client_city = ""
        st.session_state.client_state = ""
        st.session_state.client_zip = ""
        st.session_state.top_note = ""
        st.session_state.bottom_note = ""
        st.session_state.disclaimer = ""
        st.session_state.op_percent = 0.0
        st.session_state.selected_company = {}
        st.session_state.from_page = "build_estimate"
        st.session_state.new_estimate_initialized = True

# 회사 목록
companies = get_all_companies()
if not companies:
    st.warning("⛔ 등록된 회사가 없습니다. 먼저 회사 정보를 등록하세요.")
    st.stop()

company_names = [c["name"] for c in companies]
default_company = st.session_state.get("selected_company", {}).get("name")
company_name = st.selectbox(
    "🏢 사용할 회사 선택",
    company_names,
    index=company_names.index(default_company) if default_company in company_names else 0
)
selected_company = next((c for c in companies if c["name"] == company_name), None)

# 견적서 정보 입력
estimate_number = st.text_input("견적서 번호", value=st.session_state.get("estimate_number", "EST-001"))
estimate_date = st.date_input("작성일", value=st.session_state.get("estimate_date", datetime.date.today()))

st.subheader("👤 고객 정보 입력")
client_name = st.text_input("고객명", value=st.session_state.get("client_name", ""))
client_phone = st.text_input("전화번호", value=st.session_state.get("client_phone", ""))
client_email = st.text_input("이메일", value=st.session_state.get("client_email", ""))
client_street = st.text_input("Street Address", value=st.session_state.get("client_street", ""))
cols = st.columns([1, 1, 1])
with cols[0]:
    client_city = st.text_input("City", value=st.session_state.get("client_city", ""))
with cols[1]:
    client_state = st.text_input("State", value=st.session_state.get("client_state", ""))
with cols[2]:
    client_zip = st.text_input("ZIP Code", value=st.session_state.get("client_zip", ""))

# 상단 노트
st.subheader("📝 견적서 노트")
top_note = st.text_area("Note 입력", value=st.session_state.get("top_note", ""), key="top_note")

# 섹션 추가
st.subheader("📦 견적서 섹션 추가")
with st.expander("💡 사용법 안내"):
    st.markdown("""
    **섹션 및 항목 관리:**
    - 각 섹션은 카테고리별로 항목을 그룹화합니다
    - 섹션 이름은 언제든지 편집할 수 있습니다
    - 항목 추가 후 ⬆️⬇️ 버튼으로 순서를 변경할 수 있습니다
    - 각 항목의 설명은 확장 메뉴에서 저장된 설명을 선택하거나 직접 입력할 수 있습니다
    - 카테고리/서브카테고리를 "모든 카테고리"/"모든 서브카테고리"로 설정하면 전체 목록을 볼 수 있습니다
    - O&P(Overhead & Profit)는 모든 섹션의 합계에 적용됩니다
    """)

cols = st.columns([1, 2, 1])
with cols[0]:
    new_section_title = st.text_input("섹션 이름", key="new_section")
with cols[1]:
    show_subtotal = st.checkbox("Subtotal 표시 여부", value=True, key="show_subtotal_checkbox")
with cols[2]:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    if st.button("➕ 추가", key="add_section_btn") and new_section_title:
        st.session_state.add_section_trigger = (new_section_title, show_subtotal)
        st.rerun()

# 항목 전체 불러오기
ALL_ITEMS = get_all_items()

def update_item_description(section_idx, item_idx):
    """항목의 설명을 업데이트하는 함수"""
    item = st.session_state.sections[section_idx]["items"][item_idx]
    
    # 선택된 설명들과 수동 입력 설명을 합치기
    all_descriptions = []
    
    # 선택된 설명들 추가
    for desc_id in item.get("selected_descriptions", []):
        for desc in item.get("available_descriptions", []):
            if desc["id"] == desc_id:
                all_descriptions.append(desc["text"])
                break
    
    # 수동 입력 설명 추가
    if item.get("manual_description", "").strip():
        all_descriptions.append(item["manual_description"].strip())
    
    # 최종 설명 텍스트 생성
    item["dec"] = "\n".join(all_descriptions)

# 섹션 표시
for i, section in enumerate(st.session_state.sections):
    st.markdown("---")
    cols = st.columns([4, 2, 1])
    with cols[0]:
        # 섹션 이름 편집 가능하게 변경
        new_section_title = st.text_input(
            "섹션 이름", 
            value=section['title'], 
            key=f"section-title-{i}",
            label_visibility="collapsed"
        )
        # 섹션 이름이 변경되면 업데이트
        if new_section_title != section['title']:
            st.session_state.update_section_title_trigger = (i, new_section_title)
            st.rerun()
        
        st.markdown(f"### 📦 {section['title']}")
    with cols[1]:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        st.markdown(f"**{len(section['items'])}개 항목**")
    with cols[2]:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("🗑️ 섹션 삭제", key=f"delete-section-{i}"):
            st.session_state.delete_section_trigger = i
            st.rerun()

    # 현재 섹션의 항목 목록 먼저 표시
    if section["items"]:
        st.markdown("##### 📋 현재 항목 목록")
        header_cols = st.columns([3, 1, 1, 1, 0.5, 0.5, 0.5])
        header_cols[0].markdown("**항목명**")
        header_cols[1].markdown("**수량**")
        header_cols[2].markdown("**단위**")
        header_cols[3].markdown("**단가**")
        header_cols[4].markdown("**⬆️**")
        header_cols[5].markdown("**⬇️**")
        header_cols[6].markdown("**🗑️**")

        # 항목 표시 및 편집
        for j, item in enumerate(section["items"]):
            # 항목 순서 표시를 위한 구분선
            if j > 0:
                st.markdown("<hr style='margin: 5px 0; border: 1px solid #e0e0e0;'>", unsafe_allow_html=True)
            
            cols = st.columns([3, 1, 1, 1, 0.5, 0.5, 0.5])
            with cols[0]:
                # 순서 번호와 함께 항목명 표시
                item["name"] = st.text_input(f"항목명 #{j+1}", value=item.get("name", ""), key=f"name-{i}-{j}")
            with cols[1]:
                item["qty"] = st.number_input("수량", value=item.get("qty", 1.0), step=1.0, key=f"qty-{i}-{j}")
            with cols[2]:
                item["unit"] = st.text_input("단위", value=item.get("unit", ""), key=f"unit-{i}-{j}")
            with cols[3]:
                item["price"] = st.number_input("단가", value=item.get("price", 0.0), step=0.01, key=f"price-{i}-{j}")
            with cols[4]:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                # 위로 이동 버튼 (첫 번째 항목이 아닐 때만 활성화)
                if j > 0:
                    if st.button("⬆️", key=f"up-{i}-{j}", help="위로 이동"):
                        st.session_state.move_item_up_trigger = (i, j)
                        st.rerun()
                else:
                    st.button("⬆️", key=f"up-{i}-{j}", disabled=True, help="첫 번째 항목입니다")
            with cols[5]:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                # 아래로 이동 버튼 (마지막 항목이 아닐 때만 활성화)
                if j < len(section["items"]) - 1:
                    if st.button("⬇️", key=f"down-{i}-{j}", help="아래로 이동"):
                        st.session_state.move_item_down_trigger = (i, j)
                        st.rerun()
                else:
                    st.button("⬇️", key=f"down-{i}-{j}", disabled=True, help="마지막 항목입니다")
            with cols[6]:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"delete-{i}-{j}", help="항목 삭제"):
                    st.session_state.delete_item_trigger = (i, j)
                    st.rerun()

            # 설명 관리 섹션
            with st.expander("📝 설명 관리", expanded=bool(item.get("dec") or item.get("available_descriptions"))):
                # 저장된 설명들이 있는 경우
                if item.get("available_descriptions"):
                    st.markdown("**💾 저장된 설명 선택:**")
                    
                    # 사용 가능한 설명들 표시
                    description_options = []
                    description_map = {}
                    
                    for desc in item["available_descriptions"]:
                        option_text = desc["text"]
                        description_options.append(option_text)
                        description_map[option_text] = desc["id"]
                    
                    # 현재 선택된 설명들 확인
                    if "selected_descriptions" not in item:
                        item["selected_descriptions"] = []
                    
                    # 다중 선택 위젯
                    selected_desc_texts = st.multiselect(
                        "사용할 설명 선택 (여러 개 선택 가능)",
                        description_options,
                        default=[desc["text"] for desc in item["available_descriptions"] 
                                if desc["id"] in item.get("selected_descriptions", [])],
                        key=f"desc-select-{i}-{j}"
                    )
                    
                    # 선택된 설명 ID 업데이트
                    item["selected_descriptions"] = [description_map[text] for text in selected_desc_texts]
                    
                    # 선택된 설명들 미리보기
                    if selected_desc_texts:
                        st.markdown("**📋 선택된 설명 미리보기:**")
                        for desc_text in selected_desc_texts:
                            st.info(desc_text)
                    
                    st.markdown("---")
                
                # 수동 입력 섹션
                st.markdown("**✍️ 추가 설명 입력:**")
                
                # 기존 수동 설명이 없으면 초기화
                if "manual_description" not in item:
                    item["manual_description"] = ""
                
                new_manual_desc = st.text_area(
                    "직접 입력한 설명",
                    value=item.get("manual_description", ""),
                    key=f"manual-desc-{i}-{j}",
                    help="저장된 설명 외에 추가로 입력할 설명"
                )
                item["manual_description"] = new_manual_desc
                
                # 설명 업데이트 버튼
                if st.button(f"📝 설명 적용", key=f"apply-desc-{i}-{j}"):
                    update_item_description(i, j)
                    st.success("설명이 적용되었습니다!")
                    st.rerun()
                
                # 최종 설명 미리보기
                st.markdown("---")
                st.markdown("**📄 최종 설명 미리보기:**")
                
                # 임시로 설명 조합해서 보여주기
                temp_descriptions = []
                
                # 선택된 저장된 설명들
                for desc_id in item.get("selected_descriptions", []):
                    for desc in item.get("available_descriptions", []):
                        if desc["id"] == desc_id:
                            temp_descriptions.append(desc["text"])
                            break
                
                # 수동 입력 설명
                if item.get("manual_description", "").strip():
                    temp_descriptions.append(item["manual_description"].strip())
                
                if temp_descriptions:
                    final_desc = "\n".join(temp_descriptions)
                    st.text_area(
                        "최종 견적서에 표시될 설명",
                        value=final_desc,
                        height=100,
                        disabled=True,
                        key=f"final-desc-{i}-{j}"
                    )
                    
                    # 현재 적용된 설명과 다르면 알림
                    if final_desc != item.get("dec", ""):
                        st.warning("⚠️ 설명이 변경되었습니다. '📝 설명 적용' 버튼을 클릭하여 적용하세요.")
                else:
                    st.info("선택된 설명이 없습니다.")

        # 섹션 소계 계산 및 표시
        section["subtotal"] = round(sum(it["qty"] * it["price"] for it in section["items"]), 2)
        st.markdown(f"<p style='text-align:right; font-weight:bold; margin-top:10px;'>Subtotal: ${section['subtotal']:,.2f}</p>", unsafe_allow_html=True)
        
        st.markdown("---")
    else:
        # 빈 섹션일 때 메시지 표시
        st.info("📋 이 섹션에는 아직 항목이 없습니다. 아래에서 항목을 추가해보세요.")
        # 빈 섹션의 소계는 0
        section["subtotal"] = 0.0

    # 새 항목 추가 섹션 (섹션 이름을 명확하게 표시)
    st.markdown(f"##### ➕ '{section['title']}' 섹션에 새 항목 추가")
    
    # 전체 카테고리 및 서브카테고리 추출
    all_categories = sorted(set(item.get("category", "") for item in ALL_ITEMS if item.get("category")))
    all_categories.insert(0, "모든 카테고리")  # 전체 선택 옵션 추가
    
    # 카테고리 선택 초기화
    if f"selected_category_{i}" not in st.session_state:
        st.session_state[f"selected_category_{i}"] = "모든 카테고리"
    
    # 카테고리 선택
    col1, col2 = st.columns([1, 1])
    with col1:
        selected_category = st.selectbox(
            "1️⃣ 카테고리 선택",
            all_categories,
            index=all_categories.index(st.session_state[f"selected_category_{i}"]) if st.session_state[f"selected_category_{i}"] in all_categories else 0,
            key=f"cat-{i}"
        )
        
        # 카테고리가 변경되면 서브카테고리 선택 초기화
        if st.session_state[f"selected_category_{i}"] != selected_category:
            st.session_state[f"selected_category_{i}"] = selected_category
            if f"selected_subcategory_{i}" in st.session_state:
                del st.session_state[f"selected_subcategory_{i}"]

    # 선택된 카테고리에 따라 서브카테고리 추출
    if selected_category == "모든 카테고리":
        # 모든 카테고리를 선택한 경우 모든 서브카테고리 표시
        all_subcategories = sorted(set(item.get("subcategory", "") for item in ALL_ITEMS if item.get("subcategory")))
    else:
        # 특정 카테고리의 서브카테고리들 추출
        category_items = [item for item in ALL_ITEMS if item.get("category") == selected_category]
        all_subcategories = sorted(set(item.get("subcategory", "") for item in category_items if item.get("subcategory")))
    
    # 서브카테고리가 있는 경우에만 서브카테고리 선택 표시
    if all_subcategories:
        all_subcategories.insert(0, "모든 서브카테고리")  # 전체 선택 옵션 추가
        
        with col2:
            # 서브카테고리 선택 초기화
            if f"selected_subcategory_{i}" not in st.session_state:
                st.session_state[f"selected_subcategory_{i}"] = "모든 서브카테고리"
            
            # 서브카테고리 선택
            selected_subcategory = st.selectbox(
                "2️⃣ 서브카테고리 선택",
                all_subcategories,
                index=all_subcategories.index(st.session_state[f"selected_subcategory_{i}"]) if st.session_state[f"selected_subcategory_{i}"] in all_subcategories else 0,
                key=f"subcat-{i}"
            )
            st.session_state[f"selected_subcategory_{i}"] = selected_subcategory
        
        # 항목 필터링
        if selected_category == "모든 카테고리" and selected_subcategory == "모든 서브카테고리":
            # 모든 항목 표시
            section_items = ALL_ITEMS
            filter_text = "**전체 항목**"
        elif selected_category == "모든 카테고리":
            # 특정 서브카테고리의 모든 항목
            section_items = [item for item in ALL_ITEMS if item.get("subcategory") == selected_subcategory]
            filter_text = f"**모든 카테고리** > **{selected_subcategory}**"
        elif selected_subcategory == "모든 서브카테고리":
            # 특정 카테고리의 모든 항목 (서브카테고리 무관)
            section_items = [item for item in ALL_ITEMS if item.get("category") == selected_category]
            filter_text = f"**{selected_category}** > **모든 서브카테고리**"
        else:
            # 특정 카테고리와 서브카테고리
            section_items = [item for item in ALL_ITEMS 
                            if item.get("category") == selected_category 
                            and item.get("subcategory") == selected_subcategory]
            filter_text = f"**{selected_category}** > **{selected_subcategory}**"
        
        # 현재 선택 상태 표시
        st.info(f"📂 {filter_text} ({len(section_items)}개 항목)")
    else:
        with col2:
            st.markdown("*서브카테고리가 없습니다*")
        
        # 서브카테고리가 없는 경우 처리
        if selected_category == "모든 카테고리":
            # 모든 항목 표시
            section_items = ALL_ITEMS
            filter_text = "**전체 항목**"
        else:
            # 특정 카테고리의 모든 항목
            section_items = [item for item in ALL_ITEMS if item.get("category") == selected_category]
            filter_text = f"**{selected_category}**"
        
        # 현재 선택 상태 표시
        st.info(f"📂 {filter_text} ({len(section_items)}개 항목)")
    
    # 항목 선택 인터페이스
    if section_items:
        item_names = [f"{item.get('code', '')} - {item.get('name', '')}" for item in section_items]
        item_lookup = {f"{item.get('code', '')} - {item.get('name', '')}": item for item in section_items}

        # 항목 선택 및 추가
        cols = st.columns([5, 1, 1])
        with cols[0]:
            selected_items = st.multiselect("항목 선택", item_names, key=f"multi-{i}")
        with cols[1]:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("➕ 항목 추가", key=f"btn-add-{i}") and selected_items:
                items_to_add = [item_lookup[name] for name in selected_items if name in item_lookup]
                if items_to_add:
                    st.session_state.add_items_trigger = (i, items_to_add)
                    st.rerun()
        with cols[2]:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("➕ 수동 추가", key=f"manual-btn-{i}"):
                st.session_state.manual_add_trigger = i
                st.rerun()
    else:
        st.warning("선택한 조건에 해당하는 항목이 없습니다.")

# O&P 퍼센트 입력
st.subheader("💰 Overhead & Profit (O&P) 설정")
op_percent = st.number_input("O&P 비율 (%)", min_value=0.0, max_value=100.0, step=1.0, value=st.session_state.get("op_percent", 0.0), key="op_percent")

# 총계 계산
subtotal_sum = round(sum(section["subtotal"] for section in st.session_state.sections), 2)
op_amount = round(subtotal_sum * (op_percent / 100), 2)
total = round(subtotal_sum + op_amount, 2)

# 총계 표시
st.markdown(f"""
<p style='text-align:right; font-weight:bold;'>Subtotal: ${subtotal_sum:,.2f}</p>
<p style='text-align:right; font-weight:bold;'>O&amp;P ({op_percent:.0f}%): ${op_amount:,.2f}</p>
<p style='text-align:right; font-size:25px; font-weight:600;'>Total: ${total:,.2f}</p>
""", unsafe_allow_html=True)

# 하단 노트
st.subheader("Note 및 Disclaimer")
bottom_note = st.text_area("Note", value=st.session_state.get("bottom_note", ""), key="bottom_note")
disclaimer = st.text_area("Disclaimer", value=st.session_state.get("disclaimer", ""), key="disclaimer")

# 미리보기 이동
if st.button("👁️ 미리보기로 이동"):
    st.session_state.selected_company = selected_company
    st.session_state.estimate_number = estimate_number
    st.session_state.estimate_date = estimate_date
    st.session_state.client_name = client_name
    st.session_state.client_phone = client_phone
    st.session_state.client_email = client_email
    st.session_state.client_street = client_street
    st.session_state.client_city = client_city
    st.session_state.client_state = client_state
    st.session_state.client_zip = client_zip
    st.session_state.top_note_preview = top_note
    st.session_state.bottom_note_preview = bottom_note
    st.session_state.disclaimer_preview = disclaimer
    st.session_state.op_percent_preview = op_percent
    st.session_state.op_amount_preview = op_amount
    st.session_state.total_preview = total

    st.switch_page("pages/preview_estimate.py")