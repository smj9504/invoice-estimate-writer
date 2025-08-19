## 가상환경 진입
```
venv\Scripts\activate   
```

## 서버 실행 
```
streamlit run app.py
python -m streamlit run app.py
```

## .env → secrets.toml 변환 
```
python utils/convert_env_to_secrets.py
```

### requirements.txt 
```
pip freeze > requirements.txt
```

1. Frontend (React + TypeScript)
    - 확장 가능한 디렉토리 구조 생성
    - Ant Design UI 라이브러리 통합
    - Zustand 상태 관리 설정
    - React Query로 서버 상태 관리
    - Dashboard와 Document List 페이지 구현
    - 필터링 및 검색 기능 구현
  2. Backend (FastAPI)
    - 기존 Python 모듈을 REST API로 래핑
    - 회사 관리 CRUD API
    - 문서 관리 API (견적서, 인보이스)
    - PDF 생성 API
    - CORS 설정 완료
  3. 주요 기능
    - 📊 대시보드: 통계, 빠른 작업, 최근 문서
    - 📄 문서 목록: 필터링, 검색, 페이지네이션
    - 🏢 회사 관리 API 준비
    - 📑 문서 CRUD 작업 (수정, 삭제, 복제)

  🎯 핵심 개선사항

  - UI/UX: Streamlit 대비 훨씬 빠르고 반응적인 인터페이스
  - 확장성: 컴포넌트 기반 구조로 기능 추가 용이
  - 유지보수성: TypeScript로 타입 안정성 확보
  - 기존 기능 유지: Streamlit 앱과 병행 운영 가능

  🚀 실행 방법

  # 간편 실행 (Windows)
  start_servers.bat

  # 또는 개별 실행
  # Backend
  python backend_api.py

  # Frontend
  cd frontend && npm start

  📝 다음 단계 권장사항

  1. 회사 관리 페이지 구현
  2. 문서 작성 폼 (견적서, 인보이스) 구현
  3. PDF 미리보기 기능 추가
  4. 인증/권한 시스템 구현
  5. Floor Plan Generator 통합 (보험 견적서용)