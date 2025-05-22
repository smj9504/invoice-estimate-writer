import streamlit as st
import datetime
import re
from modules.company_module import get_all_companies  
from modules.estimate_item_module import get_all_items
from modules.estimate_module import get_estimate_by_id
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

# 항목 추가 트리거
if "add_items_trigger" in st.session_state:
    section_idx, items_to_add = st.session_state.add_items_trigger
    if 0 <= section_idx < len(st.session_state.sections):
        for item in items_to_add:
            # 중복 체크
            if not any(existing_item["code"] == item["code"] for existing_item in st.session_state.sections[section_idx]["items"]):
                st.session_state.sections[section_idx]["items"].append({
                    "code": item["code"],
                    "name": item["name"], 
                    "unit": item["unit"],
                    "price": item["unit_price"],
                    "qty": 1.0,
                    "dec": ""
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
            "dec": ""
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

            st.session_state.sections = data.get("serviceSections", [])
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
    - 항목 추가 후 ⬆️⬇️ 버튼으로 순서를 변경할 수 있습니다
    - 각 항목의 설명은 확장 메뉴에서 입력할 수 있습니다
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

# 섹션 표시
for i, section in enumerate(st.session_state.sections):
    st.markdown("---")
    cols = st.columns([6, 1])
    with cols[0]:
        st.subheader(f"📦 {section['title']}")
    with cols[1]:
        if st.button("🗑️ 섹션 삭제", key=f"delete-section-{i}"):
            st.session_state.delete_section_trigger = i
            st.rerun()

    all_categories = sorted(set(item["category"] for item in ALL_ITEMS if item.get("category")))
    
    # 카테고리 선택 초기화
    if "selected_category" not in section:
        section["selected_category"] = all_categories[0] if all_categories else ""
    
    # 카테고리 선택
    col1, col2 = st.columns([1, 1])
    with col1:
        selected_category = st.selectbox(
            "1️⃣ 카테고리 선택",
            all_categories,
            index=all_categories.index(section["selected_category"]) if section["selected_category"] in all_categories else 0,
            key=f"cat-{i}"
        )
        
        # 카테고리가 변경되면 서브카테고리 선택 초기화
        if section["selected_category"] != selected_category:
            section["selected_category"] = selected_category
            if "selected_subcategory" in section:
                del section["selected_subcategory"]

    # 선택된 카테고리의 서브카테고리들 추출
    category_items = [item for item in ALL_ITEMS if item.get("category") == selected_category]
    all_subcategories = sorted(set(item["subcategory"] for item in category_items if item.get("subcategory")))
    
    # 서브카테고리가 있는 경우에만 서브카테고리 선택 표시
    if all_subcategories:
        with col2:
            # 서브카테고리 선택 초기화
            if "selected_subcategory" not in section:
                section["selected_subcategory"] = all_subcategories[0] if all_subcategories else ""
            
            # 서브카테고리 선택
            selected_subcategory = st.selectbox(
                "2️⃣ 서브카테고리 선택",
                all_subcategories,
                index=all_subcategories.index(section["selected_subcategory"]) if section["selected_subcategory"] in all_subcategories else 0,
                key=f"subcat-{i}"
            )
            section["selected_subcategory"] = selected_subcategory
        
        # 선택된 서브카테고리의 항목들
        section_items = [item for item in ALL_ITEMS 
                        if item.get("category") == selected_category 
                        and item.get("subcategory") == selected_subcategory]
        
        # 현재 선택 상태 표시
        st.info(f"📂 **{selected_category}** > **{selected_subcategory}** ({len(section_items)}개 항목)")
    else:
        with col2:
            st.markdown("*서브카테고리가 없습니다*")
        
        # 서브카테고리가 없는 경우 카테고리의 모든 항목
        section_items = [item for item in ALL_ITEMS if item.get("category") == selected_category]
        
        # 현재 선택 상태 표시
        st.info(f"📂 **{selected_category}** ({len(section_items)}개 항목)")
    item_names = [f"{item['code']} - {item['name']}" for item in section_items]
    item_lookup = {f"{item['code']} - {item['name']}": item for item in section_items}

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

    # 항목 헤더 (항목이 있을 때만 표시)
    if section["items"]:
        st.markdown("##### 📋 항목 목록")
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

        # 설명 입력
        with st.expander("📝 설명 입력 (선택)", expanded=bool(item.get("dec"))):
            item["dec"] = st.text_area("설명", value=item.get("dec", ""), key=f"desc-{i}-{j}")
            if item["dec"]:
                st.markdown(item["dec"].replace("\n", "<br>"), unsafe_allow_html=True)

    # 섹션 소계 계산
    section["subtotal"] = round(sum(it["qty"] * it["price"] for it in section["items"]), 2)
    st.markdown(f"<p style='text-align:right; font-weight:bold;'>Subtotal: ${section['subtotal']:,.2f}</p>", unsafe_allow_html=True)

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