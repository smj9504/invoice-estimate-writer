# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MJ Estimate Generator is a Streamlit-based web application for creating professional insurance estimates, invoices, and floor plans. The system integrates with Supabase for data persistence and uses WeasyPrint for PDF generation.

## Development Commands

### Environment Setup
```bash
# Activate virtual environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Convert .env to Streamlit secrets format
python utils/convert_env_to_secrets.py
```

### Running the Application
```bash
# Start Streamlit server
streamlit run app.py
# or
python -m streamlit run app.py
```

### Testing
```bash
# Run tests
pytest

# Test floor plan generation
python test_floor_plan.py

# Test PDF generation
python test_pdf_generation.py
```

### Dependency Management
```bash
# Update requirements file
pip freeze > requirements.txt
```

## Architecture Overview

### Core Components

1. **Main Application (`app.py`)**: Entry point with navigation to estimate and invoice builders

2. **PDF Generation System (`pdf_generator.py`)**:
   - Template-based PDF generation using Jinja2 and WeasyPrint
   - Supports multiple document types: estimates, invoices, insurance estimates
   - Handles floor plan integration for insurance estimates
   - GTK+ runtime dependency for Windows environments

3. **Floor Plan Generator (`floor_plan_generator.py`)**:
   - Creates SVG floor plans for rooms with measurements
   - Automatic scaling and centering
   - Integration with insurance estimate PDFs

4. **Database Layer (`utils/db.py`)**:
   - Supabase integration with connection management
   - Retry logic for network resilience
   - Session-based connection caching for Streamlit

5. **Module System (`modules/`)**:
   - `company_module.py`: Company data CRUD operations
   - `estimate_module.py`: Estimate management
   - `invoice_module.py`: Invoice management
   - `estimate_item_module.py`: Line item management for estimates
   - `invoice_item_module.py`: Line item management for invoices

### Page Components (`pages/`)

Key pages include:
- `insurance_estimate_editor.py`: Complex insurance estimate creation with floor plans
- `build_estimate.py`: General estimate builder
- `build_invoice.py`: Invoice builder
- `xlsx_to_pdf.py`: Excel to PDF conversion
- `generate_from_json.py`: JSON-based document generation

### Template System (`templates/`)

HTML/CSS templates for different document types:
- `insurance_estimate_with_plans.html`: Insurance estimates with integrated floor plans
- `general_estimate.html`: Standard estimates
- `general_invoice.html`: Standard invoices
- Associated CSS files for styling

## Key Technical Considerations

### WeasyPrint & GTK+ Configuration
The application requires GTK+ runtime for WeasyPrint on Windows. The `pdf_generator.py` automatically adds GTK+ to PATH if installed at the standard location (`C:\Program Files\GTK3-Runtime Win64\bin`).

### Data Safety
- All numeric conversions use safe conversion functions (`safe_float_conversion`, `safe_decimal_conversion`)
- NaN values are handled throughout the codebase
- Decimal precision for financial calculations

### Supabase Integration
- Connection caching using Streamlit's `@st.cache_resource`
- Automatic retry logic for database operations
- Secrets stored in `.streamlit/secrets.toml` (use `convert_env_to_secrets.py` to convert from `.env`)

### Floor Plan Generation
- SVG-based room floor plans with automatic scaling
- Dimension labels and area calculations
- Integration with PDF generation for insurance estimates

### JSON Data Structure
The system expects specific JSON structures for estimates:
- Room data with dimensions, area, and measurements
- Line items with quantities, rates, and calculations
- Company and client information
- Support for depreciation and insurance-specific fields

## Important Files & Directories

- `data/insurance_estimate/`: Storage for generated PDFs, HTML, and JSON files
- `data/xlsx_json/`: JSON files converted from Excel
- `statics/`: Static HTML intake forms
- `measurement/`: Sample JSON data for floor plans and room measurements

## Common Operations

### Adding New Document Types
1. Create HTML template in `templates/`
2. Add CSS file for styling
3. Update `TEMPLATE_MAP` in `pdf_generator.py`
4. Create corresponding page in `pages/`

### Modifying Database Schema
1. Update Supabase tables
2. Modify relevant module in `modules/`
3. Update data conversion functions if needed

### Debugging PDF Generation
1. Check GTK+ installation and PATH
2. Enable HTML output for debugging (`save_html=True` in generation functions)
3. Review generated HTML in `data/insurance_estimate/html/`