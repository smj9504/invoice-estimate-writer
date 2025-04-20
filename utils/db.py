import os
from supabase import create_client
from dotenv import load_dotenv
import streamlit as st

# # .env 파일 로드
# load_dotenv()

# # Supabase 연결 정보
# SUPABASE_URL = os.getenv("SUPABASE_URL")
# SUPABASE_KEY = os.getenv("SUPABASE_KEY")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

def init_connection():
    """
    Supabase 클라이언트를 초기화하고 연결합니다.
    애플리케이션 시작 시 한 번만 호출하는 것이 좋습니다.
    """
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase 연결 성공")
        return supabase
    except Exception as e:
        print(f"[DB ERROR] Supabase 연결 실패: {e}")
        return None

def get_connection():
    """
    기존 연결이 있으면 반환하고, 없으면 새 연결을 생성합니다.
    이 함수는 세션 상태를 사용하여 연결을 저장하므로 Streamlit 환경에서만 작동합니다.
    """
    # 이미 연결이 있는 경우
    if "supabase" in st.session_state and st.session_state.supabase is not None:
        return st.session_state.supabase
    
    # 새 연결 생성
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        st.session_state.supabase = supabase
        print("✅ Supabase 연결 성공")
        return supabase
    except Exception as e:
        print(f"[DB ERROR] Supabase 연결 실패: {e}")
        st.error(f"데이터베이스 연결에 실패했습니다: {e}")
        return None

def get_supabase_client():
    """
    현재 활성화된 Supabase 클라이언트를 반환합니다.
    get_connection()의 별칭으로, 이름이 더 명확합니다.
    """
    return get_connection()