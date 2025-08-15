from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import math
from datetime import datetime
import pandas as pd
import json
import re

# Add GTK+ path if available, then import WeasyPrint
import os
import sys

# Force add GTK+ to PATH before any imports
gtk_path = r"C:\Program Files\GTK3-Runtime Win64\bin"
if os.path.exists(gtk_path):
    # Add to both os.environ and sys.path for immediate effect
    current_path = os.environ.get('PATH', '')
    os.environ['PATH'] = f"{gtk_path};{current_path}"
    
    # Also add to Windows DLL search path if on Windows
    if hasattr(os, 'add_dll_directory'):
        try:
            os.add_dll_directory(gtk_path)
        except:
            pass

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except Exception as e:
    print(f"WeasyPrint not available: {e}")
    print("Try running with run_app.bat to set the correct PATH")
    WEASYPRINT_AVAILABLE = False
    HTML = None
    CSS = None

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
    "insurance_estimate_with_plans": {
        "template": "insurance_estimate_with_plans.html",
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
    """
    Safely convert value to float, handling:
    - Empty strings and None
    - Dollar signs ($)
    - Commas (,)
    - Percentage signs (%)
    - Various string formats
    """
    if value is None or value == '' or value == 'None':
        return default
    
    try:
        # Convert to string first
        str_value = str(value).strip()
        
        # Handle empty string
        if not str_value:
            return default
        
        # Handle special cases
        if str_value.lower() in ['nan', 'none', 'null']:
            return default
        
        # Remove dollar signs, commas, and spaces
        cleaned_value = re.sub(r'[$,\s]', '', str_value)
        
        # Handle percentage - remove % but keep the number as-is
        # e.g., "10%" → 10.0, not 0.1
        if '%' in cleaned_value:
            cleaned_value = cleaned_value.replace('%', '')
            # Don't divide by 100 here - the calculation will handle it later
            return float(cleaned_value)
        
        # Handle empty string after cleaning
        if not cleaned_value:
            return default
        
        # Convert to float
        return float(cleaned_value)
        
    except (ValueError, TypeError, AttributeError):
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
    """견적서 데이터 유효성 검사 및 기본값 설정 - 보험 견적서 형식 지원 + categories 없는 경우 처리"""
    import copy
    
    print(f"DEBUG: validate_estimate_data called with enhanced parsing")
    print(f"DEBUG: Input context keys: {list(context.keys())}")
    
    # 깊은 복사를 사용하여 원본 데이터 보호
    context = copy.deepcopy(context)

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

    # 보험 견적서 관련 필드 초기화 (enhanced parsing 적용)
    context['subtotal'] = safe_float_conversion(context.get('subtotal', 0.0))
    context['discount'] = safe_float_conversion(context.get('discount', 0.0))
    context['tax_rate'] = safe_float_conversion(context.get('tax_rate', 0.0))
    context['sales_tax'] = safe_float_conversion(context.get('sales_tax', 0.0))
    context['overhead_rate'] = safe_float_conversion(context.get('overhead_rate', 0.0))
    context['overhead_amount'] = safe_float_conversion(context.get('overhead_amount', 0.0))
    context['profit_rate'] = safe_float_conversion(context.get('profit_rate', 0.0))
    context['profit_amount'] = safe_float_conversion(context.get('profit_amount', 0.0))
    context['sales_tax_amount'] = safe_float_conversion(context.get('sales_tax_amount', 0.0))
    context['total'] = safe_float_conversion(context.get('total', 0.0))
    
    # 중첩 객체 구조 지원 (enhanced parsing 적용)
    if 'overhead' not in context:
        context['overhead'] = {
            'rate': context.get('overhead_rate', 0.0),
            'amount': context.get('overhead_amount', 0.0)
        }
    else:
        if isinstance(context['overhead'], dict):
            # Convert rate from decimal to percentage if needed (0.10 -> 10)
            overhead_rate = safe_float_conversion(context['overhead'].get('rate', 0.0))
            if overhead_rate > 0 and overhead_rate <= 1:
                overhead_rate = overhead_rate * 100
            context['overhead']['rate'] = overhead_rate
            context['overhead']['amount'] = safe_float_conversion(context['overhead'].get('amount', 0.0))
    
    if 'profit' not in context:
        context['profit'] = {
            'rate': context.get('profit_rate', 0.0),
            'amount': context.get('profit_amount', 0.0)
        }
    else:
        if isinstance(context['profit'], dict):
            # Convert rate from decimal to percentage if needed (0.05 -> 5)
            profit_rate = safe_float_conversion(context['profit'].get('rate', 0.0))
            if profit_rate > 0 and profit_rate <= 1:
                profit_rate = profit_rate * 100
            context['profit']['rate'] = profit_rate
            context['profit']['amount'] = safe_float_conversion(context['profit'].get('amount', 0.0))
    
    if 'sales_tax' not in context or not isinstance(context['sales_tax'], dict):
        context['sales_tax'] = {
            'amount': context.get('sales_tax_amount', context.get('sales_tax', 0.0))
        }
    else:
        context['sales_tax']['amount'] = safe_float_conversion(context['sales_tax'].get('amount', 0.0))

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

    # trades 처리 - enhanced parsing + categories 없는 경우 처리
    new_trades = []
    for i, trade in enumerate(context.get('trades', [])):
        new_trade = {
            'name': safe_note_processing(trade.get('name', f'Trade {i+1}')),
            'note': safe_note_processing(trade.get('note', '')),
            'locations': []
        }

        for j, location in enumerate(trade.get('locations', [])):
            # Enhanced parsing for location subtotal
            location_subtotal = safe_float_conversion(location.get('subtotal', 0.0))
            
            new_location = {
                'name': safe_note_processing(location.get('name', f'Location {j+1}')),
                'note': safe_note_processing(location.get('note', '')),
                'showSubtotal': location.get('showSubtotal', True),
                'subtotal': location_subtotal,
                'categories': []
            }

            # categories 처리 - 없는 경우도 안전하게 처리
            categories = location.get('categories', [])
            if not categories:
                print(f"DEBUG: No categories found for location '{new_location['name']}', using stored subtotal: ${location_subtotal}")
                # categories가 없어도 location 자체는 유지
                new_location['categories'] = []
            else:
                # categories가 있는 경우 정상 처리
                for k, category in enumerate(categories):
                    new_category = {
                        'name': safe_note_processing(category.get('name', f'Category {k+1}')),
                        'items': []
                    }

                    # items 처리 (enhanced parsing 적용)
                    items = category.get('items', [])
                    if isinstance(items, list):
                        for l, item in enumerate(items):
                            if isinstance(item, dict):
                                new_item = {
                                    'name': safe_note_processing(item.get('name', '')),
                                    'qty': safe_float_conversion(item.get('qty', 0)),
                                    'unit': str(item.get('unit', 'ea')),
                                    'price': safe_float_conversion(item.get('price', 0)),
                                    'description': safe_note_processing(item.get('description', ''))
                                }
                                # name이 비어있지 않은 경우만 추가
                                if new_item['name']:
                                    new_category['items'].append(new_item)
                                    print(f"DEBUG: Added item '{new_item['name']}' (qty: {new_item['qty']}, price: ${new_item['price']}) to category '{new_category['name']}'")

                    new_location['categories'].append(new_category)
                    print(f"DEBUG: Category '{new_category['name']}' has {len(new_category['items'])} items")

            new_trade['locations'].append(new_location)
            print(f"DEBUG: Location '{new_location['name']}' has {len(new_location['categories'])} categories, subtotal: ${new_location['subtotal']}")

        new_trades.append(new_trade)

    context['trades'] = new_trades
    
    # 최종 확인
    print(f"DEBUG: Final validation - trades count: {len(context['trades'])}")
    for trade in context['trades']:
        print(f"DEBUG: Trade '{trade['name']}' has {len(trade['locations'])} locations")
        for location in trade['locations']:
            print(f"  Location '{location['name']}' has {len(location['categories'])} categories, subtotal: ${location['subtotal']}")
            for category in location['categories']:
                print(f"    Category '{category['name']}' has {len(category['items'])} items")

    return context

def debug_template_content(html_content, context):
    """템플릿 렌더링 디버깅 - categories 없는 경우 확인"""
    print(f"DEBUG: ========== TEMPLATE RENDERING DEBUG ==========")
    print(f"DEBUG: HTML content length: {len(html_content)}")

    if 'trades' in html_content.lower():
        print("DEBUG: OK 'trades' found in HTML content")
    else:
        print("DEBUG: X 'trades' NOT found in HTML content")

    note_elements = ['trade-note', 'location-note', 'amount-due-note']
    for element in note_elements:
        if element in html_content:
            print(f"DEBUG: OK '{element}' found in HTML content")
        else:
            print(f"DEBUG: X '{element}' NOT found in HTML content")

    trades = context.get('trades', [])
    if trades:
        # categories 없는 location 확인
        locations_without_categories = []
        locations_with_stored_subtotal = []
        first_item_name = None
        
        for trade in trades:
            for location in trade.get('locations', []):
                categories = location.get('categories', [])
                stored_subtotal = safe_float_conversion(location.get('subtotal', 0))
                
                if not categories:
                    locations_without_categories.append(f"{trade.get('name', 'Unknown Trade')} > {location.get('name', 'Unknown Location')}")
                    if stored_subtotal > 0:
                        locations_with_stored_subtotal.append(f"{location.get('name', 'Unknown Location')}: ${stored_subtotal}")
                else:
                    for category in categories:
                        for item in category.get('items', []):
                            if item.get('name') and not first_item_name:
                                first_item_name = item['name']
                                break
                        if first_item_name:
                            break
                if first_item_name:
                    break
        
        if locations_without_categories:
            print(f"DEBUG: ⚠️ Locations without categories: {locations_without_categories}")
            if locations_with_stored_subtotal:
                print(f"DEBUG: OK Locations with stored subtotals: {locations_with_stored_subtotal}")
        else:
            print(f"DEBUG: OK All locations have categories")

        if first_item_name:
            if first_item_name in html_content:
                print(f"DEBUG: OK First item '{first_item_name}' found in HTML")
            else:
                print(f"DEBUG: X First item '{first_item_name}' NOT found in HTML")

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
    if not WEASYPRINT_AVAILABLE:
        raise RuntimeError("WeasyPrint is not available.")
    
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
                margin: 0.3in 0.4in 0.5in 0.4in;
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
                margin: 1.2in 0.4in 0.7in 0.4in;
                @top-left {{
                    content: "{company_info_text}";
                    font-size: 11px;
                    color: #333;
                    line-height: 1.3;
                    white-space: pre;
                    vertical-align: top;
                    padding: 20px 0 6px 0;
                    margin-bottom: 15px;
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
                    padding: 20px 0 6px 0;
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
    if not WEASYPRINT_AVAILABLE:
        raise RuntimeError("WeasyPrint is not available.")
    
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

    if doc_type in ["insurance_estimate", "insurance_estimate_with_plans"]:
        context = validate_estimate_data(context)
        context = calculate_estimate_totals(context)

    config = TEMPLATE_MAP[doc_type]
    template_path = config["template"]
    css_path = TEMPLATE_DIR / config["css"]

    print(f"DEBUG: Using template: {template_path}")
    print(f"DEBUG: Using CSS: {css_path}")

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))

    # Enhanced 필터 등록
    def safe_float_filter(value):
        """안전한 float 변환 필터 (enhanced parsing)"""
        return safe_float_conversion(value, 0.0)
    
    def safe_replace(text, old, new):
        """안전한 문자열 치환 필터"""
        if text is None:
            return ''
        try:
            return str(text).replace(str(old), str(new))
        except Exception:
            return str(text)
    
    def format_number(value, decimal_places=2):
        """숫자 포맷팅 필터 (enhanced parsing)"""
        try:
            num = safe_float_conversion(value, 0.0)
            return f"{num:,.{decimal_places}f}"
        except:
            return "0.00"
    
    # 필터 등록
    env.filters['float'] = safe_float_filter
    env.filters['replace'] = safe_replace
    env.filters['format_number'] = format_number

    template_file_path = TEMPLATE_DIR / template_path
    if not template_file_path.exists():
        print(f"ERROR: Template file not found: {template_file_path}")
        raise FileNotFoundError(f"Template file not found: {template_file_path}")

    template = env.get_template(template_path)

    print(f"DEBUG: Rendering template with enhanced parsing...")
    
    # 템플릿 렌더링 전에 컨텍스트 검증
    print(f"DEBUG: Context validation before rendering:")
    if 'trades' in context:
        for i, trade in enumerate(context['trades']):
            print(f"  Trade {i}: {trade.get('name', 'unnamed')}")
            for j, location in enumerate(trade.get('locations', [])):
                subtotal = location.get('subtotal', 0)
                categories_count = len(location.get('categories', []))
                print(f"    Location {j}: {location.get('name', 'unnamed')} - Subtotal: ${subtotal}, Categories: {categories_count}")
    
    try:
        html_content = template.render(**context)
    except Exception as e:
        print(f"ERROR: Template rendering failed: {e}")
        import traceback
        traceback.print_exc()
        raise

    debug_template_content(html_content, context)

    debug_html_path = Path(output_path).parent / "debug_output.html"
    with open(debug_html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"DEBUG: HTML saved for debugging at: {debug_html_path}")

    # PDF 생성...
    if not css_path.exists():
        print(f"WARNING: CSS file not found: {css_path}")
        HTML(string=html_content).write_pdf(output_path)
        print(f"DEBUG: PDF generated successfully at: {output_path}")
        return

    with open(css_path, "r", encoding="utf-8") as css_file:
        base_css = CSS(string=css_file.read())

    # 헤더/푸터 생성...
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
                padding: 40px 0 6px 0;  
                margin-bottom: 15px;   
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
                padding: 40px 0 6px 0;  
                margin-bottom: 15px;     
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
    """)

    print(f"DEBUG: Generating PDF with enhanced parsing...")
    try:
        HTML(string=html_content).write_pdf(output_path, stylesheets=[base_css, header_footer_css])
        print(f"DEBUG: PDF generated successfully at: {output_path}")
    except Exception as e:
        print(f"ERROR: PDF generation failed: {e}")
        HTML(string=html_content).write_pdf(output_path)
        print(f"DEBUG: PDF generated successfully (without custom CSS) at: {output_path}")

    print(f"DEBUG: ========== PDF GENERATION END ==========")

def generate_insurance_estimate_html(context: dict, output_path: str):
    """보험 견적서 HTML 생성 (PDF와 동일한 템플릿 사용)"""
    import copy
    
    print(f"DEBUG: generate_insurance_estimate_html called")
    print(f"DEBUG: Output path: {output_path}")
    
    # 깊은 복사로 원본 보호
    context_copy = copy.deepcopy(context)
    
    # Process floor plans if they exist (for consistency)
    from floor_plan_generator import FloorPlanGenerator
    
    if 'floor_plans' in context_copy and context_copy.get('floor_plans', {}).get('rooms'):
        generator = FloorPlanGenerator()
        rooms_data = context_copy['floor_plans']['rooms']
        
        # Handle both list and dict formats
        if isinstance(rooms_data, list):
            for i, room_data in enumerate(rooms_data):
                if isinstance(room_data, dict):
                    # Generate SVG floor plan
                    if 'coordinates' in room_data and room_data['coordinates']:
                        svg = generator.generate_complex_room_svg(room_data)
                    else:
                        svg = generator.generate_room_svg(room_data)
                    context_copy['floor_plans']['rooms'][i]['svg_plan'] = svg
        elif isinstance(rooms_data, dict):
            for room_key, room_data in rooms_data.items():
                if isinstance(room_data, dict):
                    # Generate SVG floor plan
                    if 'coordinates' in room_data and room_data['coordinates']:
                        svg = generator.generate_complex_room_svg(room_data)
                    else:
                        svg = generator.generate_room_svg(room_data)
                    context_copy['floor_plans']['rooms'][room_key]['svg_plan'] = svg
    
    # HTML 생성
    _generate_html_output(context_copy, output_path, "insurance_estimate")

def generate_insurance_estimate_html_with_plans(context: dict, output_path: str):
    """보험 견적서 HTML 생성 with Floor Plans"""
    import copy
    
    print(f"DEBUG: generate_insurance_estimate_html_with_plans called")
    print(f"DEBUG: Output path: {output_path}")
    
    # 깊은 복사로 원본 보호
    context_copy = copy.deepcopy(context)
    
    # Floor plan data validation
    from floor_plan_generator import FloorPlanGenerator
    
    if 'floor_plans' in context_copy and context_copy.get('floor_plans', {}).get('rooms'):
        print(f"DEBUG: Processing floor plans for HTML with plans")
        generator = FloorPlanGenerator()
        rooms_data = context_copy['floor_plans']['rooms']
        print(f"DEBUG: Rooms data type: {type(rooms_data)}")
        print(f"DEBUG: Number of rooms: {len(rooms_data) if isinstance(rooms_data, (list, dict)) else 0}")
        
        # Handle both list and dict formats
        if isinstance(rooms_data, list):
            # If rooms is a list, iterate directly
            print(f"DEBUG: Processing rooms as list")
            for i, room_data in enumerate(rooms_data):
                if isinstance(room_data, dict):
                    print(f"DEBUG: Processing room {i}: {room_data.get('name', 'Unknown')}")
                    # Generate SVG floor plan
                    if 'coordinates' in room_data and room_data['coordinates']:
                        svg = generator.generate_complex_room_svg(room_data)
                        print(f"DEBUG: Generated complex SVG for room {i}")
                    else:
                        svg = generator.generate_room_svg(room_data)
                        print(f"DEBUG: Generated simple SVG for room {i}, length: {len(svg) if svg else 0}")
                    
                    # Use svg_plan to match template expectation
                    context_copy['floor_plans']['rooms'][i]['svg_plan'] = svg
                    print(f"DEBUG: Set svg_plan for room {i}")
                    
                    measurements_html = generator.generate_measurement_table_html(room_data)
                    context_copy['floor_plans']['rooms'][i]['measurements_html'] = measurements_html
        elif isinstance(rooms_data, dict):
            # If rooms is a dict, iterate over items
            print(f"DEBUG: Processing rooms as dict")
            for room_key, room_data in rooms_data.items():
                if isinstance(room_data, dict):
                    print(f"DEBUG: Processing room {room_key}: {room_data.get('name', 'Unknown')}")
                    # Generate SVG floor plan
                    if 'coordinates' in room_data and room_data['coordinates']:
                        svg = generator.generate_complex_room_svg(room_data)
                        print(f"DEBUG: Generated complex SVG for room {room_key}")
                    else:
                        svg = generator.generate_room_svg(room_data)
                        print(f"DEBUG: Generated simple SVG for room {room_key}, length: {len(svg) if svg else 0}")
                    
                    # Use svg_plan to match template expectation
                    context_copy['floor_plans']['rooms'][room_key]['svg_plan'] = svg
                    print(f"DEBUG: Set svg_plan for room {room_key}")
                    
                    measurements_html = generator.generate_measurement_table_html(room_data)
                    context_copy['floor_plans']['rooms'][room_key]['measurements_html'] = measurements_html
    else:
        print(f"DEBUG: No floor plans found or rooms is empty")
        print(f"DEBUG: floor_plans exists: {'floor_plans' in context_copy}")
        if 'floor_plans' in context_copy:
            print(f"DEBUG: floor_plans.rooms exists: {'rooms' in context_copy.get('floor_plans', {})}")
            if 'rooms' in context_copy.get('floor_plans', {}):
                print(f"DEBUG: rooms value: {context_copy['floor_plans']['rooms']}")
    
    # Convert rooms dict to list if needed for template compatibility
    if 'floor_plans' in context_copy and 'rooms' in context_copy['floor_plans']:
        rooms = context_copy['floor_plans']['rooms']
        if isinstance(rooms, dict):
            # Convert dict to list for template iteration
            context_copy['floor_plans']['rooms'] = list(rooms.values())
            print(f"DEBUG: Converted rooms dict to list of {len(context_copy['floor_plans']['rooms'])} rooms")
    
    # HTML 생성
    _generate_html_output(context_copy, output_path, "insurance_estimate_with_plans")

def _generate_html_output(context: dict, output_path: str, template_type: str):
    """HTML 파일 생성 헬퍼 함수"""
    
    # Define filter functions
    def format_currency(value):
        """통화 포맷팅 필터"""
        try:
            if value is None or value == '':
                return "$0.00"
            # Convert to float, handling various input types
            if isinstance(value, str):
                # Remove $ and commas
                value = value.replace('$', '').replace(',', '').strip()
            
            num_value = float(value)
            # Format with commas and 2 decimal places
            return f"${num_value:,.2f}"
        except (ValueError, TypeError):
            return "$0.00"
    
    def format_number(value, decimal_places=2):
        """숫자 포맷팅 필터"""
        try:
            num_value = safe_float_conversion(value)
            return f"{num_value:,.{decimal_places}f}"
        except:
            return "0"
    
    # NaN 값 정리
    context = clean_nan(context)
    
    # 견적서 타입별 계산 수행 (PDF와 동일한 로직)
    if template_type in ["insurance_estimate", "insurance_estimate_with_plans"]:
        # Calculate totals - same logic as in generate_insurance_estimate_pdf
        subtotal = 0.0
        for trade in context.get('trades', []):
            for location in trade.get('locations', []):
                location_subtotal = calculate_location_subtotal(location)
                location['subtotal'] = location_subtotal
                subtotal += location_subtotal
        
        context['subtotal'] = subtotal
        
        # Calculate overhead and profit
        overhead_rate = safe_float_conversion(context.get('overhead_rate', 0))
        profit_rate = safe_float_conversion(context.get('profit_rate', 0))
        
        overhead_amount = safe_float_conversion(context.get('overhead_amount', 0))
        profit_amount = safe_float_conversion(context.get('profit_amount', 0))
        
        if overhead_amount <= 0 and overhead_rate > 0:
            if overhead_rate <= 1:
                overhead_amount = subtotal * overhead_rate
            else:
                overhead_amount = subtotal * (overhead_rate / 100)
            context['overhead_amount'] = overhead_amount
        
        if profit_amount <= 0 and profit_rate > 0:
            if profit_rate <= 1:
                profit_amount = subtotal * profit_rate
            else:
                profit_amount = subtotal * (profit_rate / 100)
            context['profit_amount'] = profit_amount
        
        # Sales tax
        sales_tax_amount = safe_float_conversion(context.get('sales_tax_amount', 0))
        if sales_tax_amount <= 0:
            sales_tax_amount = safe_float_conversion(context.get('sales_tax', 0))
        context['sales_tax_amount'] = sales_tax_amount
        
        # Calculate total
        total = subtotal + overhead_amount + profit_amount + sales_tax_amount
        context['total'] = total
    
    # Jinja2 템플릿 렌더링
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    env.filters['format_currency'] = format_currency
    env.filters['format_number'] = format_number
    
    template_info = TEMPLATE_MAP[template_type]
    template = env.get_template(template_info["template"])
    
    # HTML 렌더링
    html_content = template.render(context)
    
    # CSS 파일 경로
    css_path = TEMPLATE_DIR / template_info["css"]
    
    # CSS를 인라인으로 포함
    with open(css_path, 'r', encoding='utf-8') as css_file:
        css_content = css_file.read()
    
    # HTML에 CSS 삽입
    html_with_css = html_content.replace('</head>', f'<style>{css_content}</style></head>')
    
    # HTML 파일 저장
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_with_css)
    
    print(f"HTML file saved to: {output_path}")

def generate_insurance_estimate_pdf_with_plans(context: dict, output_path: str):
    """보험 견적서 PDF 생성 with Floor Plans"""
    import copy
    
    print(f"DEBUG: generate_insurance_estimate_pdf_with_plans called")
    print(f"DEBUG: Output path: {output_path}")
    
    # 깊은 복사로 원본 보호
    context_copy = copy.deepcopy(context)
    
    try:
        from floor_plan_generator import FloorPlanGenerator
        
        # Generate floor plans if data is available
        if 'floor_plans' in context_copy and 'rooms' in context_copy['floor_plans']:
            print(f"DEBUG: Generating floor plans for {len(context_copy['floor_plans']['rooms'])} rooms")
            generator = FloorPlanGenerator()
            
            for room in context_copy['floor_plans']['rooms']:
                # Generate SVG floor plan
                if 'coordinates' in room and room['coordinates']:
                    room['svg_plan'] = generator.generate_complex_room_svg(room)
                else:
                    room['svg_plan'] = generator.generate_room_svg(room)
                
                # Generate measurement table
                room['measurement_table'] = generator.generate_measurement_table_html(room)
                print(f"DEBUG: Generated floor plan for room: {room.get('name', 'Unknown')}")
        
        # PDF 생성 전 컨텍스트 디버깅
        debug_pdf_context_before_generation(context_copy)
        
        # PDF 생성 with floor plans template
        generate_pdf(context_copy, output_path, doc_type="insurance_estimate_with_plans")
        
    except ImportError as e:
        print(f"Floor plan generator not available: {e}, generating standard estimate")
        generate_insurance_estimate_pdf(context_copy, output_path)

def generate_insurance_estimate_pdf(context: dict, output_path: str):
    """보험 견적서 PDF 생성 - 향상된 디버깅 및 계산 검증 포함"""
    import copy
    
    print(f"DEBUG: generate_insurance_estimate_pdf called")
    print(f"DEBUG: Output path: {output_path}")
    
    # 깊은 복사로 원본 보호
    context_copy = copy.deepcopy(context)
    
    # PDF 생성 전 컨텍스트 디버깅
    debug_pdf_context_before_generation(context_copy)
    
    # PDF 생성
    generate_pdf(context_copy, output_path, doc_type="insurance_estimate")

def generate_estimate_pdf(context: dict, output_path: str):
    generate_pdf(context, output_path, doc_type="estimate")

def generate_invoice_pdf(context: dict, output_path: str):
    generate_pdf(context, output_path, doc_type="invoice")

def calculate_item_total(qty, price):
    """개별 아이템 총액 계산"""
    return safe_float_conversion(qty) * safe_float_conversion(price)

def calculate_location_subtotal(location):
    """Location별 소계 계산 - categories 없는 경우 stored subtotal 우선 사용"""
    # 먼저 stored subtotal 확인
    stored_subtotal = safe_float_conversion(location.get('subtotal', 0))
    
    if stored_subtotal > 0:
        print(f"DEBUG: Using stored subtotal for location '{location.get('name', 'Unknown')}': ${stored_subtotal}")
        return stored_subtotal
    
    # stored subtotal이 없으면 categories로 계산
    categories = location.get('categories', [])
    if not categories:
        print(f"DEBUG: No categories and no stored subtotal for location '{location.get('name', 'Unknown')}', returning 0")
        return 0.0
    
    total = 0.0
    for category in categories:
        items = category.get('items', [])
        for item in items:
            if 'qty' in item and 'price' in item:
                total += calculate_item_total(item['qty'], item['price'])
    
    print(f"DEBUG: Calculated subtotal for location '{location.get('name', 'Unknown')}': ${total}")
    return total

def calculate_estimate_totals(data):
    """
    견적서 전체 계산 수행 - 보험 견적서 형식 지원 (Overhead & Profit 포함)
    Enhanced parsing + categories 없는 경우 stored subtotal 우선 사용
    수정: overhead_rate와 profit_rate가 이미 소수점 형태로 들어오는 경우 처리
    """
    print(f"DEBUG: calculate_estimate_totals called with enhanced parsing (fixed percentage handling)")
    
    # 기존 계산된 값이 있는지 확인 (enhanced parsing 적용)
    existing_subtotal = safe_float_conversion(data.get('subtotal', 0))
    existing_total = safe_float_conversion(data.get('total', 0))
    existing_overhead = safe_float_conversion(data.get('overhead_amount', 0))
    existing_profit = safe_float_conversion(data.get('profit_amount', 0))
    
    # 만약 이미 정확한 계산이 되어있다면 그대로 사용
    if existing_total > 0 and existing_subtotal > 0:
        # 검증: 기존 값들이 일치하는지 확인
        manual_total = (
            existing_subtotal + 
            existing_overhead + 
            existing_profit + 
            safe_float_conversion(data.get('sales_tax_amount', data.get('sales_tax', {}).get('amount', 0))) - 
            safe_float_conversion(data.get('discount', 0))
        )
        
        if abs(manual_total - existing_total) < 0.01:
            print(f"DEBUG: Using existing calculated values - Subtotal: ${existing_subtotal}, Total: ${existing_total}")
            return data
    
    # 새로 계산 수행
    subtotal = 0.0

    # Location별 subtotal 계산 (stored subtotal 우선)
    for trade in data.get('trades', []):
        for location in trade.get('locations', []):
            location_subtotal = calculate_location_subtotal(location)
            location['subtotal'] = location_subtotal
            subtotal += location_subtotal

    data['subtotal'] = subtotal
    print(f"DEBUG: Calculated total subtotal: ${subtotal}")

    # Overhead & Profit 계산 (FIXED: 퍼센트/소수점 형태 자동 감지)
    overhead_rate = safe_float_conversion(data.get('overhead_rate', 0))
    profit_rate = safe_float_conversion(data.get('profit_rate', 0))
    
    print(f"DEBUG: Original overhead_rate: {overhead_rate}, profit_rate: {profit_rate}")
    
    # 만약 overhead_amount, profit_amount가 이미 있으면 사용
    overhead_amount = safe_float_conversion(data.get('overhead_amount', 0))
    profit_amount = safe_float_conversion(data.get('profit_amount', 0))
    
    if overhead_amount <= 0 and overhead_rate > 0:
        # 퍼센트 vs 소수점 형태 자동 감지
        if overhead_rate <= 1:
            # 이미 소수점 형태 (0.04 for 4%)
            overhead_amount = subtotal * overhead_rate
            print(f"DEBUG: Using decimal form overhead_rate: {overhead_rate}")
        else:
            # 퍼센트 형태 (4 for 4%)
            overhead_amount = subtotal * (overhead_rate / 100)
            print(f"DEBUG: Using percentage form overhead_rate: {overhead_rate}")
        data['overhead_amount'] = overhead_amount
    
    if profit_amount <= 0 and profit_rate > 0:
        # 퍼센트 vs 소수점 형태 자동 감지
        if profit_rate <= 1:
            # 이미 소수점 형태 (0.1 for 10%)
            profit_amount = subtotal * profit_rate
            print(f"DEBUG: Using decimal form profit_rate: {profit_rate}")
        else:
            # 퍼센트 형태 (10 for 10%)
            profit_amount = subtotal * (profit_rate / 100)
            print(f"DEBUG: Using percentage form profit_rate: {profit_rate}")
        data['profit_amount'] = profit_amount
    
    print(f"DEBUG: Calculated Overhead: ${overhead_amount}, Profit: ${profit_amount}")

    # Sales Tax is a fixed amount (not calculated from rate)
    sales_tax_amount = 0.0
    
    # 1. 직접 입력된 sales_tax_amount 사용
    if 'sales_tax_amount' in data:
        sales_tax_amount = safe_float_conversion(data['sales_tax_amount'])
    # 2. 중첩 객체에서 가져오기
    elif isinstance(data.get('sales_tax'), dict):
        sales_tax_amount = safe_float_conversion(data['sales_tax'].get('amount', 0))
    # 3. 기존 sales_tax 필드 (하위 호환성)
    elif 'sales_tax' in data and not isinstance(data.get('sales_tax'), dict):
        sales_tax_amount = safe_float_conversion(data['sales_tax'])
    
    # Note: We do NOT calculate from rate - sales tax is always a fixed amount
    data['sales_tax_amount'] = sales_tax_amount
    print(f"DEBUG: Sales Tax (fixed amount): ${sales_tax_amount}")

    # 최종 total 계산
    discount = safe_float_conversion(data.get('discount', 0))
    total = subtotal + overhead_amount + profit_amount + sales_tax_amount - discount
    data['total'] = total

    print(f"DEBUG: Final calculations - Subtotal: ${subtotal}, Overhead: ${overhead_amount}, Profit: ${profit_amount}, Sales Tax: ${sales_tax_amount}, Discount: ${discount}, Total: ${total}")

    # 중첩 객체 구조 업데이트 (rate를 다시 소수점 형태로 저장)
    # Display용으로는 퍼센트로 변환되어 사용되지만, 저장은 소수점 형태로
    data['overhead'] = {
        'rate': overhead_rate if overhead_rate > 1 else overhead_rate,  # Keep as-is
        'amount': overhead_amount
    }
    data['profit'] = {
        'rate': profit_rate if profit_rate > 1 else profit_rate,  # Keep as-is
        'amount': profit_amount
    }
    data['sales_tax'] = {
        'amount': sales_tax_amount
    }

    return data

def debug_pdf_context_before_generation(context):
    """PDF 생성 전 컨텍스트 디버깅"""
    print(f"DEBUG: ========== PDF CONTEXT DEBUG ==========")
    print(f"DEBUG: Key financial values:")
    print(f"  subtotal: {context.get('subtotal', 'NOT_FOUND')} (type: {type(context.get('subtotal', 'NOT_FOUND'))})")
    print(f"  overhead_amount: {context.get('overhead_amount', 'NOT_FOUND')}")
    print(f"  profit_amount: {context.get('profit_amount', 'NOT_FOUND')}")
    print(f"  sales_tax_amount: {context.get('sales_tax_amount', 'NOT_FOUND')}")
    print(f"  discount: {context.get('discount', 'NOT_FOUND')}")
    print(f"  total: {context.get('total', 'NOT_FOUND')}")
    
    print(f"DEBUG: Location subtotals:")
    for trade in context.get('trades', []):
        for location in trade.get('locations', []):
            subtotal = location.get('subtotal', 0)
            categories_count = len(location.get('categories', []))
            print(f"  {location.get('name', 'Unknown')}: ${subtotal} (categories: {categories_count})")

    # 중첩 객체 확인
    if 'sales_tax' in context:
        print(f"  sales_tax object: {context['sales_tax']}")
    if 'overhead' in context:
        print(f"  overhead object: {context['overhead']}")
    if 'profit' in context:
        print(f"  profit object: {context['profit']}")
    
    # 수동 계산 검증
    try:
        manual_total = (
            safe_float_conversion(context.get('subtotal', 0)) +
            safe_float_conversion(context.get('overhead_amount', 0)) +
            safe_float_conversion(context.get('profit_amount', 0)) +
            safe_float_conversion(context.get('sales_tax_amount', 0)) -
            safe_float_conversion(context.get('discount', 0))
        )
        stored_total = safe_float_conversion(context.get('total', 0))
        print(f"  Manual calculation: {manual_total}")
        print(f"  Stored total: {stored_total}")
        print(f"  Difference: {abs(manual_total - stored_total)}")
    except Exception as e:
        print(f"  Error in manual calculation: {e}")
    
    print(f"DEBUG: =====================================")