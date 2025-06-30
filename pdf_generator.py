from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
from pathlib import Path
import math
from datetime import datetime
import pandas as pd
import json

TEMPLATE_DIR = Path(__file__).parent / "templates"

TEMPLATE_MAP = {
    "estimate": {
        "template": "general_estimate.html",
        "css": "estimate_style.css"
    },
    "invoice": {
        "template": "general_invoice.html",
        "css": "style.css"
    },
    "insurance_estimate": {
        "template": "insurance_estimate_format.html",
        "css": "insurance_estimate_style.css"
    },
}

def generate_estimate_number(client_address=""):
    """견적서 번호 자동 생성: EST_YYYYMM_{property address 앞 네자리}"""
    now = datetime.now()
    year_month = now.strftime("%Y%m")

    # 주소에서 앞 4자리 추출 (영숫자만)
    address_prefix = ""
    if client_address:
        # 영숫자만 추출하고 대문자로 변환
        alphanumeric = ''.join(c.upper() for c in client_address if c.isalnum())
        address_prefix = alphanumeric[:4].ljust(4, '0')  # 4자리 미만이면 0으로 채움
    else:
        address_prefix = "0000"

    return f"EST_{year_month}_{address_prefix}"

def get_default_estimate_date():
    """오늘 날짜 반환"""
    return datetime.now().strftime("%B %d, %Y")  # "June 18, 2025" 형식으로 변경

def replace_nan_with_zero(d):
    if isinstance(d, dict):
        return {k: replace_nan_with_zero(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [replace_nan_with_zero(v) for v in d]
    elif isinstance(d, float) and (str(d) == "nan" or pd.isna(d)):
        return 0.0
    return d

def clean_nan(obj):
    """NaN 값들을 정리하는 함수"""
    if isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan(v) for v in obj]
    elif isinstance(obj, float) and math.isnan(obj):
        return 0.0
    elif obj is None:
        return ""
    elif pd.isna(obj):
        return 0.0 if isinstance(obj, (int, float)) else ""
    return obj

def safe_float_conversion(value, default=0.0):
    """안전한 float 변환"""
    if value is None or value == '' or value == 'None':
        return default
    try:
        if isinstance(value, str) and value.lower() == 'nan':
            return default
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_note_processing(note_value):
    """안전한 note 값 처리"""
    if note_value is None:
        return ""

    if pd.isna(note_value):
        return ""

    if isinstance(note_value, (int, float)):
        if math.isnan(note_value):
            return ""
        return str(note_value)

    try:
        note_str = str(note_value).strip()
        if note_str.lower() in ['nan', 'none', 'null', '']:
            return ""
        return note_str
    except:
        return ""

def validate_estimate_data(context):
    """견적서 데이터 유효성 검사 및 기본값 설정"""
    print(f"DEBUG: validate_estimate_data called")
    print(f"DEBUG: Input context keys: {list(context.keys())}")

    if 'company' not in context:
        context['company'] = {}
    if 'client' not in context:
        context['client'] = {}
    if 'trades' not in context:
        context['trades'] = []

    print(f"DEBUG: Number of trades: {len(context.get('trades', []))}")

    if not context.get('estimate_number'):
        client_address = context.get('client', {}).get('address', '')
        context['estimate_number'] = generate_estimate_number(client_address)

    if not context.get('estimate_date'):
        context['estimate_date'] = get_default_estimate_date()

    context.setdefault('subtotal', 0.0)
    context.setdefault('discount', 0.0)
    context.setdefault('tax_rate', 0.0)
    context.setdefault('sales_tax', 0.0)
    context.setdefault('total', 0.0)

    context['top_note'] = safe_note_processing(context.get('top_note', ''))
    context['bottom_note'] = safe_note_processing(context.get('bottom_note', ''))
    context['disclaimer'] = safe_note_processing(context.get('disclaimer', ''))

    company_defaults = {
        'name': 'Company Name', 'address': 'Company Address', 'city': 'City', 'state': 'State',
        'zip': 'ZIP', 'phone': 'Phone', 'email': 'Email', 'logo': ''
    }
    for key, default in company_defaults.items():
        context['company'].setdefault(key, default)

    client_defaults = {
        'name': 'Client Name', 'address': 'Client Address', 'city': 'City', 'state': 'State',
        'zip': 'ZIP', 'phone': 'Phone', 'email': 'Email'
    }
    for key, default in client_defaults.items():
        context['client'].setdefault(key, default)

    for i, trade in enumerate(context['trades']):
        trade['name'] = safe_note_processing(trade.get('name', f'Trade {i+1}'))
        trade['note'] = safe_note_processing(trade.get('note', ''))

        trade.setdefault('locations', [])

        for j, location in enumerate(trade['locations']):
            location['name'] = safe_note_processing(location.get('name', f'Location {j+1}'))
            location['note'] = safe_note_processing(location.get('note', ''))

            location.setdefault('showSubtotal', True)
            location.setdefault('subtotal', 0.0)
            location.setdefault('categories', [])

            for k, category in enumerate(location['categories']):
                category['name'] = safe_note_processing(category.get('name', f'Category {k+1}'))
                category.setdefault('items', [])

                print(f"DEBUG_ITEM_ISSUE: Category '{category.get('name')}' items BEFORE iteration:")
                print(f"DEBUG_ITEM_ISSUE: Type of category['items']: {type(category['items'])}")
                if isinstance(category['items'], list):
                    print(f"DEBUG_ITEM_ISSUE: Length of category['items']: {len(category['items'])}")
                    for idx, item_data in enumerate(category['items']):
                        print(f"DEBUG_ITEM_ISSUE: Item {idx} data: {item_data}")
                        print(f"DEBUG_ITEM_ISSUE: Type of item {idx} data: {type(item_data)}")
                else:
                    print(f"DEBUG_ITEM_ISSUE: category['items'] is NOT a list!")
                    print(f"DEBUG_ITEM_ISSUE: Value of category['items']: {category['items']}")

                # --- THIS IS THE CRUCIAL PART TO ENSURE IS PRESENT AND ACTIVE ---
                # Force category['items'] to be a plain list, just in case
                if not isinstance(category['items'], list):
                    # This branch should ideally not be taken based on your debug output
                    print(f"WARNING: category['items'] is not a list. Attempting conversion.")
                    category['items'] = list(category['items'])
                else:
                    # This branch should be taken. Create a new list from the existing one.
                    category['items'] = list(category['items']) # Explicitly re-create as a generic list object.
                # --- END OF CRUCIAL PART ---

                print(f"DEBUG: Category {k} has {len(category.get('items', []))} items")

                for l, item in enumerate(category['items']):
                    item['name'] = safe_note_processing(item.get('name', f'Item {l+1}'))
                    item.setdefault('unit', 'ea')

                    item['qty'] = safe_float_conversion(item.get('qty', 0))
                    item['price'] = safe_float_conversion(item.get('price', 0))

                    item['description'] = safe_note_processing(item.get('description', ''))

    return context

def debug_template_content(html_content, context):
    print(f"DEBUG: ========== TEMPLATE RENDERING DEBUG ==========")
    print(f"DEBUG: HTML content length: {len(html_content)}")

    if 'trades' in html_content.lower():
        print("DEBUG: ✓ 'trades' found in HTML content")
    else:
        print("DEBUG: ✗ 'trades' NOT found in HTML content")

    note_elements = ['trade-note', 'location-note', 'amount-due-note']
    for element in note_elements:
        if element in html_content:
            print(f"DEBUG: ✓ '{element}' found in HTML content")
        else:
            print(f"DEBUG: ✗ '{element}' NOT found in HTML content")

    trades = context.get('trades', [])
    if trades:
        first_item_name = None
        for trade in trades:
            for location in trade.get('locations', []):
                for category in location.get('categories', []):
                    for item in category.get('items', []):
                        if item.get('name'):
                            first_item_name = item['name']
                            break
                    if first_item_name:
                        break
                if first_item_name:
                    break
            if first_item_name:
                break

        if first_item_name:
            if first_item_name in html_content:
                print(f"DEBUG: ✓ First item '{first_item_name}' found in HTML")
            else:
                print(f"DEBUG: ✗ First item '{first_item_name}' NOT found in HTML")

    preview_length = 1000
    print(f"DEBUG: HTML preview (first {preview_length} chars):")
    print(html_content[:preview_length])
    if len(html_content) > preview_length:
        print("...")

    print(f"DEBUG: ============================================")

def validate_invoice_data(context):
    """인보이스 데이터 유효성 검사 및 기본값 설정"""
    print(f"DEBUG: validate_invoice_data called")
    print(f"DEBUG: Input context keys: {list(context.keys())}")

    # 기본 구조 설정
    if 'company' not in context:
        context['company'] = {}
    if 'client' not in context:
        context['client'] = {}
    if 'serviceSections' not in context:
        context['serviceSections'] = []
    if 'payments' not in context:
        context['payments'] = []

    # 인보이스 번호 및 날짜 기본값
    if not context.get('invoice_number'):
        context['invoice_number'] = 'INV-001'
    if not context.get('date_of_issue'):
        context['date_of_issue'] = datetime.now().strftime("%B %d, %Y")
    if not context.get('date_due'):
        context['date_due'] = datetime.now().strftime("%B %d, %Y")

    # 보험 정보 처리
    if 'insurance' not in context:
        context['insurance'] = {}
    
    # 금액 관련 기본값 설정
    context.setdefault('line_item_total', 0.0)
    context.setdefault('material_sales_tax', 0.0)
    context.setdefault('subtotal_total', 0.0)
    context.setdefault('total', 0.0)
    context.setdefault('discount', 0.0)

    # 노트 처리 (줄바꿈 변환)
    context['top_note'] = safe_note_processing(context.get('top_note', ''))
    context['bottom_note'] = safe_note_processing(context.get('bottom_note', ''))
    context['disclaimer'] = safe_note_processing(context.get('disclaimer', ''))
    context['amount_due_text'] = safe_note_processing(context.get('amount_due_text', ''))

    # 회사 정보 기본값
    company_defaults = {
        'name': 'Company Name', 'address': 'Company Address', 'city': 'City', 'state': 'State',
        'zip': 'ZIP', 'phone': 'Phone', 'email': 'Email', 'logo': ''
    }
    for key, default in company_defaults.items():
        context['company'].setdefault(key, default)

    # 고객 정보 기본값
    client_defaults = {
        'name': 'Client Name', 'address': 'Client Address', 'city': 'City', 'state': 'State',
        'zip': 'ZIP', 'phone': 'Phone', 'email': 'Email'
    }
    for key, default in client_defaults.items():
        context['client'].setdefault(key, default)

    # 보험 정보 기본값
    insurance_defaults = {
        'company': '', 'policy_number': '', 'claim_number': ''
    }
    for key, default in insurance_defaults.items():
        context['insurance'].setdefault(key, default)

    # 서비스 섹션 처리
    for i, section in enumerate(context['serviceSections']):
        section['title'] = safe_note_processing(section.get('title', f'Section {i+1}'))
        section.setdefault('amount', 0.0)
        section.setdefault('subtotal', 0.0)
        section.setdefault('showSubtotal', True)
        section.setdefault('items', [])

        for j, item in enumerate(section['items']):
            item['name'] = safe_note_processing(item.get('name', f'Item {j+1}'))
            item.setdefault('unit', 'ea')
            item.setdefault('qty', 0.0)
            item.setdefault('price', 0.0)
            item.setdefault('amount', 0.0)
            item.setdefault('hide_price', False)
            
            # Description 처리 (리스트 형태와 문자열 형태 모두 지원)
            if 'description' in item:
                if isinstance(item['description'], list):
                    # 리스트 형태는 그대로 유지
                    item['description'] = [safe_note_processing(desc) for desc in item['description']]
                else:
                    # 문자열 형태는 줄바꿈으로 분할하여 리스트로 변환
                    desc_text = safe_note_processing(item['description'])
                    item['description'] = [line.strip() for line in desc_text.split('\n') if line.strip()]
            else:
                item['description'] = []
            
            # 기존 dec 필드 처리 (호환성)
            item['dec'] = safe_note_processing(item.get('dec', ''))

    # 결제 정보 처리
    for payment in context['payments']:
        payment.setdefault('name', '')
        payment.setdefault('date', '')
        payment.setdefault('amount', 0.0)

    print(f"DEBUG: Invoice validation completed")
    return context

def calculate_invoice_totals(context):
    """인보이스 총계 계산"""
    print(f"DEBUG: calculate_invoice_totals called")
    
    # 섹션별 소계 계산
    sections_subtotal = 0.0
    for section in context.get('serviceSections', []):
        section_total = 0.0
        
        # 섹션에 직접 금액이 설정되어 있으면 사용
        if section.get('amount', 0) > 0:
            section_total = safe_float_conversion(section['amount'])
        else:
            # 아이템별 금액 계산
            for item in section.get('items', []):
                if item.get('amount', 0) > 0:
                    # 아이템에 직접 금액이 설정되어 있으면 사용
                    section_total += safe_float_conversion(item['amount'])
                else:
                    # qty × price 계산
                    qty = safe_float_conversion(item.get('qty', 0))
                    price = safe_float_conversion(item.get('price', 0))
                    section_total += qty * price
        
        section['subtotal'] = section_total
        sections_subtotal += section_total

    # 추가 비용 계산
    line_item_total = safe_float_conversion(context.get('line_item_total', 0))
    material_sales_tax = safe_float_conversion(context.get('material_sales_tax', 0))
    
    # 전체 총계 (섹션 + Line Item Total + Material Sales Tax)
    grand_total = sections_subtotal + line_item_total + material_sales_tax
    context['subtotal_total'] = grand_total

    # 결제 받은 총액 계산
    paid_total = 0.0
    for payment in context.get('payments', []):
        paid_total += safe_float_conversion(payment.get('amount', 0))

    # 최종 미지불 금액
    amount_due = grand_total - paid_total
    context['total'] = amount_due

    print(f"DEBUG: Invoice totals - Sections: {sections_subtotal}, Line Item: {line_item_total}, Tax: {material_sales_tax}")
    print(f"DEBUG: Grand Total: {grand_total}, Paid: {paid_total}, Amount Due: {amount_due}")

    return context

def generate_depreciation_invoice_pdf(context: dict, output_path: str):
    """
    건설업 특화 인보이스 PDF 생성 함수
    - 보험 정보 지원
    - Line Item Total 및 Material Sales Tax 지원
    - 작업 내역 세부 표시
    - Payment 이름 지원
    """
    print(f"DEBUG: ========== DEPRECIATION INVOICE PDF GENERATION START ==========")
    print(f"DEBUG: Output path: {output_path}")
    print(f"DEBUG: Template directory: {TEMPLATE_DIR}")

    # TEMPLATE_MAP에 새로운 템플릿 추가 (기존 코드에서 이 부분을 추가해야 함)
    depreciation_template_config = {
        "template": "depreciation_invoice.html",  # 새로 만든 HTML 템플릿
        "css": "depreciation_invoice_style.css"   # 새로 만든 CSS 파일
    }

    try:
        # NaN 값 정리
        context = clean_nan(context)
        
        # 인보이스 데이터 검증 및 기본값 설정
        context = validate_invoice_data(context)
        
        # 총계 계산
        context = calculate_invoice_totals(context)

        # 템플릿 설정
        template_path = depreciation_template_config["template"]
        css_path = TEMPLATE_DIR / depreciation_template_config["css"]

        print(f"DEBUG: Using template: {template_path}")
        print(f"DEBUG: Using CSS: {css_path}")
        print(f"DEBUG: CSS file exists: {css_path.exists()}")

        # Jinja2 환경 설정
        env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
        
        # 필터 등록 (기존 코드와 동일)
        env.filters['float'] = float
        env.filters['replace'] = lambda s, old, new: s.replace(old, new)

        # 템플릿 파일 확인
        template_file_path = TEMPLATE_DIR / template_path
        if not template_file_path.exists():
            print(f"ERROR: Template file not found: {template_file_path}")
            raise FileNotFoundError(f"Template file not found: {template_file_path}")

        # 템플릿 렌더링
        template = env.get_template(template_path)
        print(f"DEBUG: Rendering template...")
        html_content = template.render(**context)

        # 디버그용 HTML 저장
        debug_html_path = Path(output_path).parent / "debug_depreciation_invoice.html"
        with open(debug_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"DEBUG: HTML saved for debugging at: {debug_html_path}")

        # CSS 파일 확인 및 PDF 생성
        if not css_path.exists():
            print(f"WARNING: CSS file not found: {css_path}")
            print(f"DEBUG: Generating PDF without custom CSS...")
            HTML(string=html_content).write_pdf(output_path)
            print(f"DEBUG: PDF generated successfully at: {output_path}")
            return

        # CSS 로드
        with open(css_path, "r", encoding="utf-8") as css_file:
            base_css = CSS(string=css_file.read())
            print(f"DEBUG: CSS loaded successfully")

        # 헤더/푸터 CSS 생성 (기존 코드와 동일한 로직)
        today_str = datetime.today().strftime("%Y-%m-%d")

        company = context.get('company', {})
        company_info_lines = []
        if company.get('name'):
            company_info_lines.append(str(company['name']))
        if company.get('address'):
            company_info_lines.append(str(company['address']))

        city_state_zip = []
        if company.get('city'):
            city_state_zip.append(str(company['city']))
        if company.get('state'):
            city_state_zip.append(str(company['state']))
        if company.get('zip'):
            city_state_zip.append(str(company['zip']))
        if city_state_zip:
            company_info_lines.append(', '.join(city_state_zip))

        if company.get('phone'):
            company_info_lines.append(str(company['phone']))
        if company.get('email'):
            company_info_lines.append(str(company['email']))

        company_info_text = '\\A '.join(company_info_lines)

        client = context.get('client', {})
        client_address_lines = []
        if client.get('address'):
            client_address_lines.append(str(client['address']))

        client_city_state_zip = []
        if client.get('city'):
            client_city_state_zip.append(str(client['city']))
        if client.get('state'):
            client_city_state_zip.append(str(client['state']))
        if client.get('zip'):
            client_city_state_zip.append(str(client['zip']))
        if client_city_state_zip:
            client_address_lines.append(', '.join(client_city_state_zip))

        client_address_text = '\\A '.join(client_address_lines) if client_address_lines else ''

        header_footer_css = CSS(string=f"""
            @page :first {{
                margin: 0.3in 0.4in 0.7in 0.4in;
                @bottom-left {{
                    content: "Generated on {today_str}";
                    font-size: 10px;
                    color: #999;
                }}
                @bottom-right {{
                    content: "Page " counter(page) " of " counter(pages);
                    font-size: 10px;
                    color: #999;
                }}
            }}

            @page {{
                margin: 1.4in 0.4in 0.7in 0.4in;
                @top-left {{
                    content: "{company_info_text}";
                    font-size: 11px;
                    color: #333;
                    line-height: 1.3;
                    white-space: pre;
                    vertical-align: top;
                    padding: 30px 0 6px 0;
                    margin-bottom: 18px;
                    width: 100%;
                    border-bottom: 1px solid #ddd;
                }}
                @top-right {{
                    content: "{client_address_text}";
                    font-size: 11px;
                    color: #333;
                    line-height: 1.3;
                    white-space: pre;
                    text-align: right;
                    vertical-align: top;
                    padding: 30px 0 6px 0;
                    margin-bottom: 18px;
                    width: 100%;
                    border-bottom: 1px solid #ddd;
                }}
                @bottom-left {{
                    content: "Generated on {today_str}";
                    font-size: 10px;
                    color: #999;
                }}
                @bottom-right {{
                    content: "Page " counter(page) " of " counter(pages);
                    font-size: 10px;
                    color: #999;
                }}
            }}

            @page :first {{
                @top-left {{ content: none; }}
                @top-right {{ content: none; }}
            }}

            .line-header {{
                margin-top: 20px;
                page-break-before: auto;
            }}

            .section-header {{
                margin-top: 15px;
                page-break-after: avoid;
            }}

            .line-row {{
                page-break-inside: avoid;
            }}

            .footer-total {{
                page-break-inside: avoid;
                margin-top: 30px;
            }}

            .address-section {{
                page-break-after: avoid;
            }}

            .insurance-section {{
                page-break-after: avoid;
            }}

            .header-top {{
                page-break-after: avoid;
            }}

            body {{
                margin: 0;
                padding: 0;
            }}
        """)

        # PDF 생성
        print(f"DEBUG: Generating PDF with base CSS and header/footer CSS...")
        try:
            HTML(string=html_content).write_pdf(output_path, stylesheets=[base_css, header_footer_css])
            print(f"DEBUG: PDF generated successfully at: {output_path}")
        except Exception as e:
            print(f"ERROR: PDF generation failed: {e}")
            print(f"DEBUG: Trying to generate PDF without custom CSS...")
            HTML(string=html_content).write_pdf(output_path)
            print(f"DEBUG: PDF generated successfully (without custom CSS) at: {output_path}")

    except Exception as e:
        print(f"ERROR: Failed to generate depreciation invoice PDF: {e}")
        raise e

    print(f"DEBUG: ========== DEPRECIATION INVOICE PDF GENERATION END ==========")


def generate_pdf(context: dict, output_path: str, doc_type: str = "insurance_estimate"):
    print(f"DEBUG: ========== PDF GENERATION START ==========")
    print(f"DEBUG: Document type: {doc_type}")
    print(f"DEBUG: Output path: {output_path}")
    print(f"DEBUG: Template directory: {TEMPLATE_DIR}")
    print(f"DEBUG: Template directory exists: {TEMPLATE_DIR.exists()}")

    if TEMPLATE_DIR.exists():
        print(f"DEBUG: Files in template directory:")
        for file in TEMPLATE_DIR.iterdir():
            print(f"DEBUG:   - {file.name}")

    print(f"DEBUG: Input context structure:")
    try:
        print(json.dumps({
            'context_keys': list(context.keys()),
            'trades_count': len(context.get('trades', [])),
            'company_name': context.get('company', {}).get('name', 'N/A'),
            'client_name': context.get('client', {}).get('name', 'N/A'),
            'estimate_number': context.get('estimate_number', 'N/A')
        }, indent=2))
    except Exception as e:
        print(f"DEBUG: Error logging context structure: {e}")

    context = clean_nan(context)

    if doc_type == "insurance_estimate":
        context = validate_estimate_data(context)
        context = calculate_estimate_totals(context)

    config = TEMPLATE_MAP[doc_type]
    template_path = config["template"]
    css_path = TEMPLATE_DIR / config["css"]

    print(f"DEBUG: Using template: {template_path}")
    print(f"DEBUG: Using CSS: {css_path}")
    print(f"DEBUG: CSS file exists: {css_path.exists()}")

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))

    # --- THIS IS THE KEY ADDITION ---
    # Explicitly register built-in functions as filters to avoid 'builtin_function_or_method' object is not iterable error
    # This helps Jinja2 correctly interpret |float and |replace.
    env.filters['float'] = float
    env.filters['replace'] = lambda s, old, new: s.replace(old, new)
    # --- END OF KEY ADDITION ---

    template_file_path = TEMPLATE_DIR / template_path
    if not template_file_path.exists():
        print(f"ERROR: Template file not found: {template_file_path}")
        raise FileNotFoundError(f"Template file not found: {template_file_path}")

    template = env.get_template(template_path)

    print(f"DEBUG: Rendering template...")
    html_content = template.render(**context)

    debug_template_content(html_content, context)

    debug_html_path = Path(output_path).parent / "debug_output.html"
    with open(debug_html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"DEBUG: HTML saved for debugging at: {debug_html_path}")

    if not css_path.exists():
        print(f"WARNING: CSS file not found: {css_path}")
        print(f"DEBUG: Generating PDF without custom CSS...")
        HTML(string=html_content).write_pdf(output_path)
        print(f"DEBUG: PDF generated successfully at: {output_path}")
        return

    with open(css_path, "r", encoding="utf-8") as css_file:
        base_css = CSS(string=css_file.read())
        print(f"DEBUG: CSS loaded successfully")

    today_str = datetime.today().strftime("%Y-%m-%d")

    company = context.get('company', {})
    company_info_lines = []
    if company.get('name'):
        company_info_lines.append(str(company['name']))
    if company.get('address'):
        company_info_lines.append(str(company['address']))

    city_state_zip = []
    if company.get('city'):
        city_state_zip.append(str(company['city']))
    if company.get('state'):
        city_state_zip.append(str(company['state']))
    if company.get('zip'):
        city_state_zip.append(str(company['zip']))
    if city_state_zip:
        company_info_lines.append(', '.join(city_state_zip))

    if company.get('phone'):
        company_info_lines.append(str(company['phone']))
    if company.get('email'):
        company_info_lines.append(str(company['email']))

    company_info_text = '\\A '.join(company_info_lines)

    client = context.get('client', {})
    client_address_lines = []
    if client.get('address'):
        client_address_lines.append(str(client['address']))

    client_city_state_zip = []
    if client.get('city'):
        client_city_state_zip.append(str(client['city']))
    if client.get('state'):
        client_city_state_zip.append(str(client['state']))
    if client.get('zip'):
        client_city_state_zip.append(str(client['zip']))
    if client_city_state_zip:
        client_address_lines.append(', '.join(client_city_state_zip))

    client_address_text = '\\A '.join(client_address_lines) if client_address_lines else ''

    header_footer_css = CSS(string=f"""
        @page :first {{
            margin: 0.3in 0.4in 0.7in 0.4in;
            @bottom-left {{
                content: "Generated on {today_str}";
                font-size: 10px;
                color: #999;
            }}
            @bottom-right {{
                content: "Page " counter(page) " of " counter(pages);
                font-size: 10px;
                color: #999;
            }}
        }}

        @page {{
            margin: 1.4in 0.4in 0.7in 0.4in;
            @top-left {{
                content: "{company_info_text}";
                font-size: 11px;
                color: #333;
                line-height: 1.3;
                white-space: pre;
                vertical-align: top;
                padding: 30px 0 6px 0;
                margin-bottom: 18px;
                width: 100%;
                border-bottom: 1px solid #ddd;
            }}
            @top-right {{
                content: "{client_address_text}";
                font-size: 11px;
                color: #333;
                line-height: 1.3;
                white-space: pre;
                text-align: right;
                vertical-align: top;
                padding: 30px 0 6px 0;
                margin-bottom: 18px;
                width: 100%;
                border-bottom: 1px solid #ddd;
            }}
            @bottom-left {{
                content: "Generated on {today_str}";
                font-size: 10px;
                color: #999;
            }}
            @bottom-right {{
                content: "Page " counter(page) " of " counter(pages);
                font-size: 10px;
                color: #999;
            }}
        }}

        @page :first {{
            @top-left {{ content: none; }}
            @top-right {{ content: none; }}
        }}

        .line-header {{
            margin-top: 20px;
            page-break-before: auto;
        }}

        .section-title {{
            margin-top: 15px;
            page-break-after: avoid;
        }}

        .line-row {{
            page-break-inside: avoid;
        }}

        .footer-total {{
            page-break-inside: avoid;
            margin-top: 30px;
        }}

        .address-section {{
            page-break-after: avoid;
        }}

        .header-top {{
            page-break-after: avoid;
        }}

        body {{
            margin: 0;
            padding: 0;
        }}
    """)

    print(f"DEBUG: Generating PDF with base CSS and header/footer CSS...")
    try:
        HTML(string=html_content).write_pdf(output_path, stylesheets=[base_css, header_footer_css])
        print(f"DEBUG: PDF generated successfully at: {output_path}")
    except Exception as e:
        print(f"ERROR: PDF generation failed: {e}")
        print(f"DEBUG: Trying to generate PDF without custom CSS...")
        HTML(string=html_content).write_pdf(output_path)
        print(f"DEBUG: PDF generated successfully (without custom CSS) at: {output_path}")

    print(f"DEBUG: ========== PDF GENERATION END ==========")

def generate_insurance_estimate_pdf(context: dict, output_path: str):
    generate_pdf(context, output_path, doc_type="insurance_estimate")

def generate_estimate_pdf(context: dict, output_path: str):
    generate_pdf(context, output_path, doc_type="estimate")

def generate_invoice_pdf(context: dict, output_path: str):
    generate_pdf(context, output_path, doc_type="invoice")

def calculate_item_total(qty, price):
    """개별 아이템 총액 계산"""
    return safe_float_conversion(qty) * safe_float_conversion(price)

def calculate_location_subtotal(location):
    """Location별 소계 계산"""
    total = 0.0
    for category in location.get('categories', []):
        for item in category.get('items', []):
            if 'qty' in item and 'price' in item:
                total += calculate_item_total(item['qty'], item['price'])
    return total

def calculate_estimate_totals(data):
    """견적서 전체 계산 수행"""
    print(f"DEBUG: calculate_estimate_totals called")
    subtotal = 0.0

    for trade in data.get('trades', []):
        for location in trade.get('locations', []):
            location_subtotal = calculate_location_subtotal(location)
            location['subtotal'] = location_subtotal
            subtotal += location_subtotal

    data['subtotal'] = subtotal

    discount = safe_float_conversion(data.get('discount', 0))
    after_discount = subtotal - discount

    tax_rate = safe_float_conversion(data.get('tax_rate', 0))
    sales_tax = after_discount * (tax_rate / 100)
    data['sales_tax'] = sales_tax

    total = after_discount + sales_tax
    data['total'] = total

    print(f"DEBUG: Final calculations - Subtotal: {subtotal}, Discount: {discount}, Tax: {sales_tax}, Total: {total}")

    return data