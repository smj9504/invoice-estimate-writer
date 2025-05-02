import streamlit as st
import datetime
import re
from modules.company_module import get_all_companies
from modules.estimate_item_module import get_all_items
from modules.estimate_module import get_estimate_by_id
from weasyprint import HTML, CSS


st.set_page_config(page_title="Estimate Builder", page_icon="📟", layout="wide")

# ✅ 세션 상태 강제 초기화
if "initialized" not in st.session_state:
    st.session_state["new_section_triggered"] = False
    st.session_state["new_section_title_cache"] = ""
    st.session_state["item_add_triggered"] = None
    st.session_state["item_add_cache"] = []
    st.session_state["item_delete_triggered"] = None
    st.session_state["manual_add_triggered"] = None
    st.session_state["from_page"] = ""

    # sections는 비어있을 때만 초기화
    if "sections" not in st.session_state:
        st.session_state["sections"] = []

    st.session_state["initialized"] = True

# URL 파라미터에서 ID 추출
query_params = st.query_params
raw_id = query_params.get("id")
estimate_id = raw_id[0] if isinstance(raw_id, list) else raw_id
uuid_pattern = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")

if estimate_id and uuid_pattern.match(estimate_id):
    if not st.session_state.sections:
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
            st.session_state.op_percent = data.get("op_percent", "")
            st.session_state.selected_company = data.get("company", {})
            st.session_state.from_page = "build_estimate"
        else:
            st.error("❌ 해당 ID의 견적서를 찾을 수 없습니다.")
            st.stop()
elif estimate_id:
    st.error("❌ 유효하지 않은 ID 형식입니다.")
    st.stop()
else:
    if not estimate_id and not st.session_state.sections:
        st.session_state.sections = []
        st.session_state.estimate_number = ""
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
        st.session_state.selected_company = {}
        st.session_state.from_page = "build_estimate"

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
top_note = st.text_area("Note 입력", key="top_note")

# 섹션 추가
st.subheader("📦 견적서 섹션 추가")
cols = st.columns([1, 2, 1])
with cols[0]:
    new_section_title = st.text_input("섹션 이름", key="new_section")
with cols[1]:
    show_subtotal = st.checkbox("Subtotal 표시 여부", value=True, key="show_subtotal_checkbox")
with cols[2]:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    if st.button("➕ 추가") and new_section_title:
        st.session_state.sections.append({
            "title": new_section_title,
            "items": [],
            "showSubtotal": show_subtotal,
            "subtotal": 0.0
        })

# 항목 전체 불러오기
ALL_ITEMS = get_all_items()

# 삭제 및 수동 추가 트리거 처리
if trigger := st.session_state.item_delete_triggered:
    i, j = trigger
    if 0 <= i < len(st.session_state.sections) and 0 <= j < len(st.session_state.sections[i]["items"]):
        st.session_state.sections[i]["items"].pop(j)
    st.session_state.item_delete_triggered = None

if trigger := st.session_state.manual_add_triggered:
    i = trigger
    if 0 <= i < len(st.session_state.sections):
        st.session_state.sections[i]["items"].append({
            "code": "",
            "name": "",
            "unit": "",
            "price": 0.0,
            "qty": 1.0,
            "dec": ""
        })
    st.session_state.manual_add_triggered = None

# 섹션 반복
for i, section in enumerate(st.session_state.sections):
    st.markdown("---")
    cols = st.columns([6, 1])
    with cols[0]:
        st.subheader(f"📦 {section['title']}")
    with cols[1]:
        if st.button("🗑️ 섹션 삭제", key=f"delete-section-{i}"):
            st.session_state.sections.pop(i)
            st.rerun()

    all_categories = sorted(set(item["category"] for item in ALL_ITEMS if item.get("category")))

    # 👉 section 자체에 category 저장 (없으면 기본값으로 초기화)
    if "selected_category" not in section or section["selected_category"] not in all_categories:
        section["selected_category"] = all_categories[0] if all_categories else ""

    # 선택 박스 (값은 section 내부의 값을 사용)
    selected_category = st.selectbox(
        "카테고리 선택",
        all_categories,
        index=all_categories.index(section["selected_category"]),
        key=f"cat-{i}"
    )
    section["selected_category"] = selected_category

    section_items = [item for item in ALL_ITEMS if item.get("category") == section["selected_category"]]

    item_names = [f"{item['code']} - {item['name']}" for item in section_items]
    item_lookup = {f"{item['code']} - {item['name']}": item for item in section_items}

    cols = st.columns([5, 1, 1])
    with cols[0]:
        selected_items = st.multiselect("항목 선택", item_names, key=f"multi-{i}")
    with cols[1]:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("➕ 항목 추가", key=f"btn-add-{i}"):
            for full_name in selected_items:
                item = item_lookup.get(full_name)
                if item and not any(it["code"] == item["code"] for it in section["items"]):
                    section["items"].append({
                        "code": item["code"],
                        "name": item["name"],
                        "unit": item["unit"],
                        "price": item["unit_price"],
                        "qty": 1.0,
                        "dec": ""
                    })
    with cols[2]:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("➕ 수동 추가", key=f"manual-btn-{i}"):
            st.session_state.manual_add_triggered = i
            st.rerun()


    for j, item in enumerate(section["items"]):
        cols = st.columns([4, 1, 1, 1, 1])
        with cols[0]:
            item["name"] = st.text_input("항목명", value=item.get("name", ""), key=f"name-{i}-{j}")
        with cols[1]:
            item["qty"] = st.number_input("수량", value=item.get("qty", 1.0), step=1.0, key=f"qty-{i}-{j}")
        with cols[2]:
            item["unit"] = st.text_input("단위", value=item.get("unit", ""), key=f"unit-{i}-{j}")
        with cols[3]:
            item["price"] = st.number_input("단가", value=item.get("price", 0.0), step=0.01, key=f"price-{i}-{j}")
        with cols[4]:
            if st.button("🗑️ 삭제", key=f"delete-{i}-{j}"):
                st.session_state.item_delete_triggered = (i, j)
                st.rerun()

        desc_key = f"desc-{i}-{j}"
        with st.expander("📝 설명 입력 (선택)", expanded=bool(item.get("dec"))):
            item["dec"] = st.text_area("설명", value=item.get("dec", ""), key=desc_key)
            if item["dec"]:
                st.markdown(item["dec"].replace("\n", "<br>"), unsafe_allow_html=True)

    section["subtotal"] = round(sum(it["qty"] * it["price"] for it in section["items"]), 2)
    st.markdown(f"<p style='text-align:right; font-weight:bold;'>Subtotal: ${section['subtotal']:,.2f}</p>", unsafe_allow_html=True)

# ✅ O&P 퍼센트 입력
st.subheader("💰 Overhead & Profit (O&P) 설정")
op_percent = st.number_input("O&P 비율 (%)", min_value=0.0, max_value=100.0, step=1.0, key="op_percent")

# ✅ subtotal 합산
subtotal_sum = round(sum(section["subtotal"] for section in st.session_state.sections), 2)

# ✅ O&P 금액 계산
op_amount = round(subtotal_sum * (op_percent / 100), 2)

# ✅ 총합
total = round(subtotal_sum + op_amount, 2)

# ✅ 표시
st.markdown(f"""
<p style='text-align:right; font-weight:bold;'>Subtotal: ${subtotal_sum:,.2f}</p>
<p style='text-align:right; font-weight:bold;'>O&amp;P ({op_percent:.0f}%): ${op_amount:,.2f}</p>
<p style='text-align:right; font-size:25px; font-weight:600;'>Total: ${total:,.2f}</p>
""", unsafe_allow_html=True)

# 하단 노트
st.subheader("Note 및 Disclaimer")
bottom_note = st.text_area("Note", key="bottom_note")
disclaimer = st.text_area("Disclaimer", key="disclaimer")

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
    st.session_state.top_note_preview = st.session_state.get("top_note", "")
    st.session_state.bottom_note_preview = st.session_state.get("bottom_note", "")
    st.session_state.disclaimer_preview = st.session_state.get("disclaimer", "")
    st.session_state.op_percent_preview = op_percent
    st.session_state.op_amount_preview = op_amount
    st.session_state.total_preview = total

    st.switch_page("pages/preview_estimate.py")
