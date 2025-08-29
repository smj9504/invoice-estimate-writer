# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MJ Estimate Generator is a comprehensive invoice and estimate management system with both legacy Streamlit and modern React/FastAPI implementations. The system supports creating professional insurance estimates, invoices, plumber reports, and work orders with PDF generation capabilities. Data persistence is handled through Supabase integration.

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment (Windows)
python -m venv venv
venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies (if working with React frontend)
cd frontend && npm install
cd ..

# Install backend dependencies (specific versions for FastAPI backend)
cd backend && pip install -r requirements.txt
cd ..
```

### Running Applications

#### Quick Start (All Servers)
```bash
# Windows - starts both FastAPI backend and React frontend
start_servers.bat

# Manual equivalent
# Terminal 1: Backend (port 8000)
venv\Scripts\activate && cd backend && uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend (port 3000) 
cd frontend && npm start
```

#### Legacy Streamlit Application
```bash
# Start Streamlit server (legacy interface)
venv\Scripts\activate
streamlit run app.py

# Convert .env to Streamlit secrets format
python utils/convert_env_to_secrets.py
```

#### Docker Deployment
```bash
# Development environment
docker-compose -f docker-compose.dev.yml up

# Production environment  
docker-compose -f docker-compose.prod.yml up
```

### Testing & Quality
```bash
# Python tests (both Streamlit and FastAPI modules)
pytest

# Test specific components
python test_floor_plan.py
python test_pdf_generation.py

# Frontend tests (React application)
cd frontend && npm test

# Build frontend for production
cd frontend && npm run build
```

### Development Workflows
```bash
# Backend development with hot reload
cd backend && uvicorn app.main:app --reload

# Frontend development with hot reload
cd frontend && npm start

# Update Python dependencies
pip freeze > requirements.txt

# Update frontend dependencies  
cd frontend && npm update
```

## Architecture Overview

This project contains two parallel implementations:

### 1. FastAPI Backend + React Frontend (Modern Stack)

**Backend Architecture (`backend/app/`)**:
- **Domain-Driven Design**: Organized by business domains (company, invoice, estimate, work_order, etc.)
- **Layered Architecture**: API → Service → Repository → Database
- **Core Infrastructure**: 
  - `core/database.py`: Supabase connection management
  - `core/config.py`: Environment-based configuration  
  - `common/base_repository.py`: Shared database operations
- **Domain Modules**: Each domain contains `api.py`, `models.py`, `schemas.py`, `service.py`, `repository.py`
- **Authentication**: JWT-based auth system in `domains/auth/`

**Key Backend Domains**:
- `company/`: Company management with logo upload
- `invoice/`, `estimate/`: Document creation and management  
- `work_order/`: Work order lifecycle management
- `plumber_report/`: Specialized reporting system
- `staff/`: User and permission management
- `document_types/`: Document template configuration

**Frontend Architecture (`frontend/src/`)**:
- **React 18 + TypeScript**: Component-based architecture
- **State Management**: Zustand for global state, React Query for server state
- **UI Framework**: Ant Design 5.x with Korean localization
- **Routing**: React Router v7 with protected routes
- **Key Components**:
  - `pages/`: Main application pages (Dashboard, DocumentList, etc.)
  - `components/`: Reusable UI components organized by domain
  - `services/`: API integration layer
  - `contexts/`: Authentication and global state

### 2. Legacy Streamlit Application

**Core Components**:
- **Main Application (`app.py`)**: Entry point with navigation
- **PDF Generation System (`pdf_generator.py`)**:
  - Template-based generation using Jinja2 and WeasyPrint
  - Supports estimates, invoices, insurance estimates with floor plans
  - GTK+ runtime dependency for Windows environments
- **Floor Plan Generator (`floor_plan_generator.py`)**:
  - SVG-based room floor plans with automatic scaling
  - Integration with insurance estimate PDFs
- **Module System (`modules/`)**:
  - CRUD operations for companies, estimates, invoices
  - Shared data models and business logic
- **Page Components (`pages/`)**: Streamlit-specific UI pages

### Shared Infrastructure

**Database Layer (`utils/db.py`)**:
- Supabase integration with connection management
- Retry logic and session-based caching
- Used by both Streamlit and FastAPI applications

**Template System (`templates/`)**:
- HTML/CSS templates for PDF generation
- Shared between both application stacks
- Support for insurance estimates with integrated floor plans

## Key Technical Considerations

### FastAPI Backend Development
- **Domain Structure**: Each domain follows the pattern `api.py` → `service.py` → `repository.py` → database
- **Database Factory**: `core/database_factory.py` provides abstraction over Supabase connections
- **Error Handling**: Custom exceptions in `core/interfaces.py` for consistent error responses
- **Authentication**: JWT tokens with role-based permissions via `domains/auth/`
- **API Documentation**: Available at `/docs` (Swagger UI) and `/redoc` when server runs

### React Frontend Development  
- **Component Organization**: Components grouped by domain (`company/`, `work-order/`, etc.)
- **API Integration**: Centralized in `services/` directory using axios + React Query
- **State Management**: Zustand for client state, React Query for server state caching
- **Routing**: Protected routes require authentication, automatic redirects
- **Build System**: CRACO for customized Create React App configuration
- **Proxy Configuration**: Development proxy to backend on `localhost:8000`

### PDF Generation & WeasyPrint
- **GTK+ Dependency**: Required for WeasyPrint on Windows at `C:\Program Files\GTK3-Runtime Win64\bin`
- **Template System**: Jinja2 templates in `templates/` directory with CSS styling
- **Floor Plan Integration**: SVG generation via `floor_plan_generator.py` for insurance estimates
- **Document Types**: Support for estimates, invoices, insurance estimates with floor plans

### Database & Supabase Integration
- **Connection Management**: Shared `utils/db.py` with retry logic and session caching
- **Environment Configuration**: Different database configs for development vs. production
- **Schema**: Tables for companies, invoices, estimates, work_orders, plumber_reports, staff
- **Data Safety**: Safe numeric conversion functions, NaN handling, decimal precision

### Development Dependencies & Common Issues
- **Backend Missing Dependencies**: Common missing packages are `itsdangerous`, `bcrypt`, `email-validator`
- **Frontend Compilation**: Uses CRACO instead of standard react-scripts
- **WeasyPrint Warnings**: GTK+ warnings are expected and don't affect functionality
- **CORS**: Configured for development (localhost:3000) and production

## Project Structure Integration

### Adding New Features
1. **Backend**: Create new domain in `backend/app/domains/` with full API → Service → Repository pattern
2. **Frontend**: Add corresponding pages in `frontend/src/pages/` and components in `frontend/src/components/`
3. **Database**: Update Supabase schema and modify shared modules in `modules/`

### Working with PDF Templates
1. Create HTML template in `templates/` directory
2. Add corresponding CSS file for styling  
3. Update `TEMPLATE_MAP` in `pdf_generator.py`
4. Test with both Streamlit and React frontends

### Database Schema Changes
1. Update Supabase database schema
2. Modify domain models in backend (`backend/app/domains/*/models.py`)
3. Update Pydantic schemas in backend (`backend/app/domains/*/schemas.py`) 
4. Modify legacy modules in `modules/` for Streamlit compatibility
5. Update frontend TypeScript types in `frontend/src/types/`

## Important Files & Directories

**Modern Stack**:
- `backend/app/main.py`: FastAPI application entry point
- `backend/app/domains/*/`: Domain-driven design structure  
- `frontend/src/App.tsx`: React application root with routing
- `frontend/src/pages/`: Main application pages
- `start_servers.bat`: Quick start script for both servers

**Legacy & Shared**:
- `app.py`: Streamlit application entry point
- `modules/`: Shared business logic modules  
- `templates/`: Jinja2 templates for PDF generation
- `utils/db.py`: Supabase connection management
- `pdf_generator.py`: PDF generation system

**Data & Configuration**:
- `data/`: Generated PDFs, JSON files, Excel conversions
- `docker-compose.dev.yml` / `docker-compose.prod.yml`: Container deployment
- Multiple `requirements.txt` files: Root (Streamlit), `backend/` (FastAPI), `frontend/package.json` (React)