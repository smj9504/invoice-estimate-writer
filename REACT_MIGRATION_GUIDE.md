# React Migration Guide - MJ Estimate Generator

## 🎯 프로젝트 개요

Streamlit 기반 MJ Estimate Generator를 React + FastAPI로 마이그레이션하는 가이드입니다.

## 📁 디렉토리 구조

```
estimate_generator/
├── frontend/                 # React 애플리케이션
│   ├── src/
│   │   ├── api/             # API 클라이언트
│   │   ├── components/      # 재사용 가능한 컴포넌트
│   │   │   ├── common/      # 공통 컴포넌트 (Layout, Header, etc.)
│   │   │   ├── dashboard/   # 대시보드 컴포넌트
│   │   │   ├── company/     # 회사 관리 컴포넌트
│   │   │   ├── documents/   # 문서 관련 컴포넌트
│   │   │   └── forms/       # 폼 컴포넌트
│   │   ├── pages/          # 페이지 컴포넌트
│   │   ├── services/        # 비즈니스 로직
│   │   ├── store/           # 상태 관리 (Zustand)
│   │   ├── hooks/           # 커스텀 훅
│   │   ├── types/           # TypeScript 타입 정의
│   │   ├── utils/           # 유틸리티 함수
│   │   └── styles/          # 글로벌 스타일
│   └── package.json
│
├── backend/                 # FastAPI 백엔드
│   ├── app/
│   │   ├── api/            # API 엔드포인트
│   │   ├── core/           # 핵심 설정 및 유틸리티
│   │   ├── schemas/        # Pydantic 모델
│   │   ├── services/       # 비즈니스 로직
│   │   └── main.py        # FastAPI 앱 진입점
│   ├── run.py             # 서버 실행 스크립트
│   └── requirements.txt    # Python 의존성
│
├── app.py                   # 기존 Streamlit (유지)
└── [기존 파일들...]
```

## 🚀 시작하기

### 1. 백엔드 실행

```bash
# 의존성 설치
cd backend
pip install -r requirements.txt

# FastAPI 서버 실행
python run.py
```

백엔드는 http://localhost:8000 에서 실행됩니다.
API 문서: http://localhost:8000/docs

### 2. 프론트엔드 실행

```bash
# React 개발 서버 실행
cd frontend
npm install
npm start
```

프론트엔드는 http://localhost:3000 에서 실행됩니다.

## 📋 구현된 기능

### ✅ 완료된 기능

1. **프로젝트 구조 설정**
   - TypeScript 기반 React 프로젝트
   - Ant Design UI 라이브러리
   - Zustand 상태 관리
   - React Query 서버 상태 관리

2. **핵심 컴포넌트**
   - Layout 컴포넌트 (사이드바, 헤더)
   - Dashboard 페이지
   - DocumentList 페이지 (필터링 지원)

3. **API 연동**
   - Axios 기반 API 클라이언트
   - 인터셉터를 통한 인증 처리
   - 에러 핸들링

4. **FastAPI 백엔드**
   - 기존 Python 모듈 래핑
   - RESTful API 엔드포인트
   - CORS 설정

### 🚧 구현 필요 기능

1. **회사 관리 페이지**
   - 회사 목록 표시
   - 회사 추가/수정/삭제
   - 로고 업로드

2. **문서 작성 페이지**
   - 견적서 작성 폼
   - 인보이스 작성 폼
   - 보험 견적서 작성 (floor plan 포함)
   - 배관공 보고서 작성

3. **문서 편집/상세 페이지**
   - 문서 상세 보기
   - 문서 편집
   - PDF 미리보기

4. **추가 기능**
   - 이메일 발송
   - Excel 내보내기
   - 문서 복제

## 🔄 마이그레이션 단계

### Phase 1: 기본 설정 (완료) ✅
- [x] React 프로젝트 생성
- [x] 디렉토리 구조 설정
- [x] 필수 패키지 설치
- [x] FastAPI 백엔드 구조

### Phase 2: 핵심 기능 (진행중) 🚧
- [x] Layout 및 라우팅
- [x] Dashboard 구현
- [x] Document List 구현
- [ ] Company Management
- [ ] Document Creation Forms

### Phase 3: 문서 작성 기능 (예정)
- [ ] Estimate Builder 컴포넌트
- [ ] Invoice Builder 컴포넌트
- [ ] Insurance Estimate with Floor Plans
- [ ] Plumber Report Builder

### Phase 4: PDF 생성 (예정)
- [ ] PDF 생성 API 연동
- [ ] PDF 미리보기 컴포넌트
- [ ] 다운로드 기능

### Phase 5: 고급 기능 (예정)
- [ ] 실시간 저장
- [ ] 드래그 앤 드롭
- [ ] 자동 완성
- [ ] 템플릿 시스템

## 🛠️ 기술 스택

### Frontend
- **React 18** + **TypeScript**: 타입 안정성
- **Ant Design**: UI 컴포넌트 라이브러리
- **Zustand**: 경량 상태 관리
- **React Query**: 서버 상태 관리
- **React Router v6**: 라우팅
- **Axios**: HTTP 클라이언트

### Backend
- **FastAPI**: 고성능 API 프레임워크
- **Supabase**: 데이터베이스 (기존 유지)
- **WeasyPrint**: PDF 생성 (기존 유지)
- **Pydantic**: 데이터 검증

## 🔑 주요 개선사항

1. **사용자 경험**
   - 빠른 페이지 로딩 (클라이언트 사이드 렌더링)
   - 반응형 디자인
   - 직관적인 UI/UX

2. **개발자 경험**
   - TypeScript로 타입 안정성
   - 컴포넌트 재사용성
   - 명확한 프로젝트 구조

3. **성능**
   - 캐싱 전략 (React Query)
   - 최적화된 번들 크기
   - Lazy loading

4. **확장성**
   - 모듈화된 구조
   - 명확한 관심사 분리
   - 테스트 가능한 코드

## 📝 다음 단계

1. **회사 관리 페이지 구현**
   ```typescript
   // pages/CompanyManagement.tsx
   - 회사 CRUD 기능
   - 로고 업로드
   - 회사 선택 기능
   ```

2. **문서 작성 폼 구현**
   ```typescript
   // components/forms/EstimateForm.tsx
   // components/forms/InvoiceForm.tsx
   - 동적 아이템 추가/삭제
   - 자동 계산
   - 유효성 검증
   ```

3. **PDF 생성 서비스 연동**
   ```typescript
   // services/pdfService.ts
   - PDF 생성 API 호출
   - Blob 처리
   - 다운로드 기능
   ```

## 🚨 주의사항

1. **기존 Streamlit 유지**
   - 마이그레이션 기간 동안 병행 운영
   - 데이터베이스 스키마 변경 최소화
   - 기존 PDF 생성 로직 재사용

2. **데이터 일관성**
   - Supabase 데이터베이스 공유
   - 트랜잭션 처리 주의
   - 동시성 문제 고려

3. **보안**
   - 인증/인가 구현 필요
   - API 보안 강화
   - 환경 변수 관리

## 🔗 유용한 링크

- [React Documentation](https://react.dev)
- [Ant Design Components](https://ant.design/components/overview)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Zustand Documentation](https://github.com/pmndrs/zustand)
- [React Query Documentation](https://tanstack.com/query/latest)

## 📞 지원

문제가 발생하거나 질문이 있으시면 이슈를 생성해주세요.