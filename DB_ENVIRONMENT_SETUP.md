# Database Environment Setup Guide

## Overview
이 프로젝트는 Development와 Production 환경을 분리하여 안전한 개발과 배포를 지원합니다.

## 환경 구성

### 1. Supabase 프로젝트 설정

#### Development 프로젝트
1. [Supabase Dashboard](https://app.supabase.com)에서 새 프로젝트 생성
2. 프로젝트 이름: `mj-estimate-dev`
3. 데이터베이스 비밀번호 설정
4. Settings > API에서 URL과 anon key 복사

#### Production 프로젝트
1. 별도의 새 프로젝트 생성
2. 프로젝트 이름: `mj-estimate-prod`
3. 강력한 데이터베이스 비밀번호 설정
4. Settings > API에서 URL과 anon key 복사

### 2. 환경 파일 설정

#### Backend
1. `.env.development` 파일에 dev Supabase 정보 입력
2. `.env.production` 파일에 prod Supabase 정보 입력

#### Frontend
1. `frontend/.env.development` 파일에 dev 설정 입력
2. `frontend/.env.production` 파일에 prod 설정 입력

## 실행 방법

### Development 환경

#### Backend
```bash
cd backend
python run_dev.py
# 또는
ENVIRONMENT=development python -m uvicorn app.main:app --reload
```

#### Frontend
```bash
cd frontend
npm install dotenv-cli --save-dev  # 처음 한 번만
npm run start:dev
```

### Production 환경

#### Backend
```bash
cd backend
python run_prod.py
# 또는
ENVIRONMENT=production python -m uvicorn app.main:app --workers 4
```

#### Frontend
```bash
cd frontend
npm run build:prod
npm run start:prod  # 테스트용
```

## Docker 사용 (선택사항)

### Development
```bash
docker-compose -f docker-compose.dev.yml up
```

### Production
```bash
docker-compose -f docker-compose.prod.yml up
```

## 데이터 마이그레이션

### Dev에서 Prod로 데이터 복사
```bash
cd scripts
python migrate_db.py --from dev --to prod --confirm
```

### 특정 테이블만 마이그레이션
```bash
python migrate_db.py --from dev --to prod --tables companies invoices --confirm
```

## 테이블 생성

각 환경의 Supabase SQL Editor에서 `supabase_plumber_reports_table.sql` 실행:

1. Dev 환경 Supabase Dashboard > SQL Editor
2. SQL 파일 내용 복사 & 실행
3. Prod 환경에서도 동일하게 실행

## 주의사항

1. **절대 Production 환경 정보를 Git에 커밋하지 마세요**
   - `.gitignore`에 `.env*` 파일들이 포함되어 있는지 확인

2. **환경 확인**
   - Frontend 우측 하단에 환경 표시기가 나타남 (dev only)
   - API 응답 헤더에서 `X-Environment` 확인 가능

3. **데이터 보호**
   - Production 데이터를 Dev로 복사할 때는 개인정보 마스킹 고려
   - 정기적인 백업 설정

## 환경별 URL

### Development
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Production
- Frontend: https://your-domain.com
- Backend: https://api.your-domain.com
- API Docs: (보안상 비활성화 권장)

## 트러블슈팅

### 환경 변수가 로드되지 않을 때
1. `.env.development` 또는 `.env.production` 파일 존재 확인
2. `ENVIRONMENT` 환경 변수 확인: `echo $ENVIRONMENT` (Linux/Mac) 또는 `echo %ENVIRONMENT%` (Windows)

### Supabase 연결 실패
1. URL과 Key가 올바른지 확인
2. Supabase 프로젝트가 활성화되어 있는지 확인
3. 네트워크 연결 확인

### 데이터 마이그레이션 실패
1. 소스와 타겟 DB 모두 접근 가능한지 확인
2. 테이블 스키마가 동일한지 확인
3. Foreign key 제약 조건 확인