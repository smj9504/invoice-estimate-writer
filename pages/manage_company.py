import streamlit as st
import base64
from PIL import Image
import io
from modules.company_module import (
    get_all_companies, get_company_by_id,
    insert_company, update_company, delete_company
)

st.set_page_config(page_title="회사 관리", page_icon="🏢", layout="wide")
st.title("🏢 회사 정보 관리")

# 🔄 상태 초기화
if "edit_company_id" not in st.session_state:
    st.session_state.edit_company_id = None
if "cropped_logo" not in st.session_state:
    st.session_state.cropped_logo = None
if "show_crop" not in st.session_state:
    st.session_state.show_crop = False

# 📥 회사 목록 불러오기
companies = get_all_companies()

# 📋 회사 목록 표시
st.subheader("📃 등록된 회사 목록")

for company in companies:
    cols = st.columns([1, 3, 2, 2, 1, 1])

    # 로고 표시
    if company.get('logo'):
        try:
            # base64 문자열에서 이미지 생성
            if company['logo'].startswith('data:image'):
                # data URL 형식인 경우
                base64_str = company['logo'].split(',')[1]
            else:
                base64_str = company['logo']

            img_data = base64.b64decode(base64_str)
            img = Image.open(io.BytesIO(img_data))
            cols[0].image(img, width=40)
        except Exception:
            cols[0].write("🏢")
    else:
        cols[0].write("🏢")

    cols[1].markdown(f"**{company['name']}**")
    cols[2].markdown(f"{company['city']}, {company['state']}")
    cols[3].markdown(company.get("phone", ""))

    if cols[4].button("✏️ 수정", key=f"edit-{company['id']}"):
        st.session_state.edit_company_id = company["id"]
        # 로고가 있으면 세션에 저장
        if company.get('logo'):
            st.session_state.cropped_logo = company['logo']

    if cols[5].button("🗑️ 삭제", key=f"delete-{company['id']}"):
        delete_company(company["id"])
        st.success(f"✅ {company['name']} 삭제 완료")
        st.rerun()

# 🔧 수정 모드인 경우 정보 불러오기
edit_data = None
if st.session_state.edit_company_id:
    edit_data = get_company_by_id(st.session_state.edit_company_id)
    # 수정 모드에서 로고 데이터 세션에 저장
    if edit_data and edit_data.get('logo') and not st.session_state.cropped_logo:
        st.session_state.cropped_logo = edit_data['logo']

# 📝 회사 등록/수정 폼
st.markdown("---")
st.subheader("➕ 회사 정보 등록 / 수정")

# 로고 업로드 및 크롭 섹션 (폼 외부)
st.markdown("### 🖼️ 회사 로고")
col1, col2 = st.columns([2, 1])

with col1:
    uploaded_logo = st.file_uploader(
        "로고 이미지 업로드 (JPG, PNG)",
        type=['png', 'jpg', 'jpeg'],
        key="logo_uploader"
    )

    if uploaded_logo is not None:
        # 업로드된 이미지 열기
        image = Image.open(uploaded_logo)

        # RGBA를 RGB로 변환 (PNG의 경우)
        if image.mode == 'RGBA':
            # 흰색 배경 생성
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3] if len(image.split()) > 3 else None)
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')

        # 이미지 크기 제한 (최대 800px)
        max_size = 800
        if image.width > max_size or image.height > max_size:
            ratio = min(max_size/image.width, max_size/image.height)
            new_size = (int(image.width * ratio), int(image.height * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)

        st.image(image, caption="업로드된 이미지", use_container_width=True)

        # 크롭 영역 선택
        st.markdown("#### ✂️ 로고 영역 선택")

        # 크롭 모드 선택
        crop_mode = st.radio(
            "크롭 모드",
            options=["auto", "manual"],
            format_func=lambda x: "🎯 자동 (전체 이미지 사용)" if x == "auto" else "✂️ 수동 크롭",
            horizontal=True
        )

        if crop_mode == "auto":
            # 전체 이미지를 사용하여 자동으로 비율 유지하며 리사이즈
            if st.button("✅ 전체 이미지 사용"):
                # 최대 크기 150px를 유지하며 비율 조정
                max_dimension = 150
                if image.width > image.height:
                    # 가로가 긴 경우
                    new_width = max_dimension
                    new_height = int((image.height / image.width) * max_dimension)
                else:
                    # 세로가 긴 경우
                    new_height = max_dimension
                    new_width = int((image.width / image.height) * max_dimension)

                cropped = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

                # base64로 인코딩
                buffered = io.BytesIO()
                cropped.save(buffered, format="PNG", quality=95)
                img_base64 = base64.b64encode(buffered.getvalue()).decode()

                # 세션 상태에 저장
                st.session_state.cropped_logo = f"data:image/png;base64,{img_base64}"
                st.success("✅ 로고 설정 완료!")
                st.rerun()

        else:  # manual mode
            # 크롭 타입 선택
            crop_type = st.radio(
                "크롭 형태",
                options=["square", "rectangle"],
                format_func=lambda x: "⬜ 정사각형" if x == "square" else "▭ 직사각형",
                horizontal=True
            )

            if crop_type == "square":
                # 정사각형 크롭
                max_crop_size = min(image.width, image.height)
                if max_crop_size < 50:
                    st.error("이미지가 너무 작습니다. 최소 50x50 픽셀 이상이어야 합니다.")
                else:
                    crop_size = st.slider(
                        "크롭 크기 (픽셀)",
                        min_value=50,
                        max_value=max_crop_size,
                        value=min(200, max_crop_size),
                        step=10
                    )

                    col_x, col_y = st.columns(2)
                    with col_x:
                        crop_x = st.number_input(
                            "X 위치",
                            min_value=0,
                            max_value=max(0, image.width - crop_size),
                            value=max(0, (image.width - crop_size) // 2),
                            step=10
                        )
                    with col_y:
                        crop_y = st.number_input(
                            "Y 위치",
                            min_value=0,
                            max_value=max(0, image.height - crop_size),
                            value=max(0, (image.height - crop_size) // 2),
                            step=10
                        )

                    if st.button("✂️ 크롭 적용"):
                        # 이미지 크롭
                        cropped = image.crop((crop_x, crop_y, crop_x + crop_size, crop_y + crop_size))
                        # 150x150으로 리사이즈
                        cropped = cropped.resize((150, 150), Image.Resampling.LANCZOS)

                        # base64로 인코딩
                        buffered = io.BytesIO()
                        cropped.save(buffered, format="PNG", quality=95)
                        img_base64 = base64.b64encode(buffered.getvalue()).decode()

                        # 세션 상태에 저장
                        st.session_state.cropped_logo = f"data:image/png;base64,{img_base64}"
                        st.success("✅ 로고 크롭 완료!")
                        st.rerun()

            else:  # rectangle
                # 직사각형 크롭
                col_w, col_h = st.columns(2)
                with col_w:
                    crop_width = st.slider(
                        "너비 (픽셀)",
                        min_value=50,
                        max_value=image.width,
                        value=min(200, image.width),
                        step=10
                    )
                with col_h:
                    crop_height = st.slider(
                        "높이 (픽셀)",
                        min_value=50,
                        max_value=image.height,
                        value=min(150, image.height),
                        step=10
                    )

                col_x, col_y = st.columns(2)
                with col_x:
                    crop_x = st.number_input(
                        "X 위치",
                        min_value=0,
                        max_value=max(0, image.width - crop_width),
                        value=max(0, (image.width - crop_width) // 2),
                        step=10
                    )
                with col_y:
                    crop_y = st.number_input(
                        "Y 위치",
                        min_value=0,
                        max_value=max(0, image.height - crop_height),
                        value=max(0, (image.height - crop_height) // 2),
                        step=10
                    )

                if st.button("✂️ 크롭 적용"):
                    # 이미지 크롭
                    cropped = image.crop((crop_x, crop_y, crop_x + crop_width, crop_y + crop_height))

                    # 비율 유지하며 최대 150px로 리사이즈
                    max_dimension = 150
                    if cropped.width > cropped.height:
                        new_width = max_dimension
                        new_height = int((cropped.height / cropped.width) * max_dimension)
                    else:
                        new_height = max_dimension
                        new_width = int((cropped.width / cropped.height) * max_dimension)

                    cropped = cropped.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # base64로 인코딩
            buffered = io.BytesIO()
            cropped.save(buffered, format="PNG", quality=95)
            img_base64 = base64.b64encode(buffered.getvalue()).decode()

            # 세션 상태에 저장
            st.session_state.cropped_logo = f"data:image/png;base64,{img_base64}"
            st.success("✅ 로고 크롭 완료!")
            st.rerun()

with col2:
    if st.session_state.cropped_logo:
        st.markdown("#### 현재 로고")
        try:
            if st.session_state.cropped_logo.startswith('data:image'):
                base64_str = st.session_state.cropped_logo.split(',')[1]
            else:
                base64_str = st.session_state.cropped_logo

            img_data = base64.b64decode(base64_str)
            img = Image.open(io.BytesIO(img_data))
            st.image(img, caption=f"현재 로고 ({img.width}x{img.height})", width=150)

            if st.button("❌ 로고 제거"):
                st.session_state.cropped_logo = None
                st.rerun()
        except Exception:
            st.error("로고 표시 오류")

st.markdown("---")

# 회사 정보 폼
with st.form("company_form"):
    st.markdown("### 📋 회사 정보")

    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input("회사명 *", value=edit_data["name"] if edit_data else "")
        address = st.text_input("주소 *", value=edit_data["address"] if edit_data else "")
        city = st.text_input("도시 *", value=edit_data["city"] if edit_data else "")
        state = st.text_input("주 *", value=edit_data["state"] if edit_data else "")

    with col2:
        zip_code = st.text_input("우편번호", value=edit_data["zip"] if edit_data else "")
        phone = st.text_input("전화번호", value=edit_data["phone"] if edit_data else "")
        email = st.text_input("이메일", value=edit_data["email"] if edit_data else "")

    submitted = st.form_submit_button("💾 저장", use_container_width=True)

    if submitted:
        if not name or not address or not city or not state:
            st.error("❌ 필수 항목을 모두 입력해주세요.")
        else:
            data = {
                "name": name,
                "address": address,
                "city": city,
                "state": state,
                "zip": zip_code,
                "phone": phone,
                "email": email,
                "logo": st.session_state.cropped_logo if st.session_state.cropped_logo else ""
            }

            if edit_data:
                update_company(edit_data["id"], data)
                st.success("✅ 회사 정보 수정 완료")
                st.session_state.edit_company_id = None
                st.session_state.cropped_logo = None
            else:
                insert_company(data)
                st.success("✅ 새 회사 등록 완료")
                st.session_state.cropped_logo = None

            st.rerun()
