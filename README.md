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

  ## 로컬 실행

  ### 간편 실행 (Windows)
  ```bash
  start_servers.bat
  ```

  ### 개별 실행
  ```bash
  # Backend
  cd backend && uvicorn app.main:app --reload --port 8000

  # Frontend  
  cd frontend && npm start
  ```

  ## Docker 실행

  Docker를 사용하여 컨테이너 환경에서 실행할 수 있습니다.

  ### 개발 환경 (docker-compose.dev.yml)
  ```bash
  # 개발 환경으로 실행
  docker-compose -f docker-compose.dev.yml up

  # 백그라운드 실행
  docker-compose -f docker-compose.dev.yml up -d
  ```

  개발 환경 특징:
  - Backend: 포트 8000
  - Frontend: 포트 3000  
  - 로컬 파일 변경사항 즉시 반영 (Hot Reload)
  - 개발용 환경 변수 사용

  ### 프로덕션 환경 (docker-compose.prod.yml)
  ```bash
  # 프로덕션 환경으로 실행
  docker-compose -f docker-compose.prod.yml up

  # 백그라운드 실행
  docker-compose -f docker-compose.prod.yml up -d
  ```

  프로덕션 환경 특징:
  - Backend: 포트 8000
  - Frontend: 포트 80
  - 프로덕션 최적화 설정
  - 프로덕션 환경 변수 사용

  ### Docker 관련 명령어
  ```bash
  # 컨테이너 중지
  docker-compose -f docker-compose.dev.yml down

  # 컨테이너 및 볼륨 제거
  docker-compose -f docker-compose.dev.yml down -v

  # 컨테이너 로그 확인
  docker-compose -f docker-compose.dev.yml logs -f

  # 특정 서비스만 실행
  docker-compose -f docker-compose.dev.yml up backend
  ```

  ### Docker 사용 장점
  - OS에 관계없이 동일한 개발/운영 환경
  - 의존성 관리 간편화
  - 팀원 간 일관된 환경 보장
  - 배포 프로세스 단순화

  📝 다음 단계 권장사항

  1. 회사 관리 페이지 구현
  2. 문서 작성 폼 (견적서, 인보이스) 구현
  3. PDF 미리보기 기능 추가
  4. 인증/권한 시스템 구현
  5. Floor Plan Generator 통합 (보험 견적서용)