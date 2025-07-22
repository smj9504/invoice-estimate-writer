from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import math
from datetime import datetime
import pandas as pd

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
    }
}

def replace_nan_with_zero(d):
    if isinstance(d, dict):
        return {k: replace_nan_with_zero(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [replace_nan_with_zero(v) for v in d]
    elif isinstance(d, float) and (str(d) == "nan" or pd.isna(d)):
        return 0.0
    return d

def generate_pdf(context: dict, output_path: str, doc_type: str = "estimate"):
    if not WEASYPRINT_AVAILABLE:
        raise RuntimeError("WeasyPrint is not available.")
    
    context = clean_nan(context)
    config = TEMPLATE_MAP[doc_type]
    template_path = config["template"]
    css_path = TEMPLATE_DIR / config["css"]

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template(template_path)
    html_content = template.render(**context)

    # CSS 경로 확인
    if not css_path.exists():
        raise FileNotFoundError(f"CSS 파일이 존재하지 않음: {css_path}")

    with open(css_path, "r", encoding="utf-8") as css_file:
        base_css = CSS(string=css_file.read())

    # 동적 푸터 CSS 생성
    today_str = datetime.today().strftime("%Y-%m-%d")

    # 회사 정보 문자열 생성 (좌측 헤더)
    company = context.get('company', {})
    company_info_lines = []
    if company.get('name'):
        company_info_lines.append(str(company['name']))
    if company.get('address'):
        company_info_lines.append(str(company['address']))
    
    # 도시, 주, 우편번호를 한 줄로 결합 (모든 값을 문자열로 변환)
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
    
    # CSS에서 줄바꿈을 위해 \\A 대신 개행 문자 사용
    company_info_text = '\\A '.join(company_info_lines)

    # 고객 주소 문자열 생성 (우측 헤더) 
    client = context.get('client', {})
    client_address_lines = []
    if client.get('address'):
        client_address_lines.append(str(client['address']))
    
    # 고객 도시, 주, 우편번호를 한 줄로 결합 (모든 값을 문자열로 변환)
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
    # client_address_text = client_address_text.replace('\\A ', '\\00000A ')

    # 동적 헤더 및 푸터 CSS 생성
    header_footer_css = CSS(string=f"""
        /* 첫 페이지 설정 */
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
        
        /* 나머지 페이지 설정 */
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
        
        /* 첫 페이지 헤더 영역만 헤더 숨기기 */
        @page :first {{
            @top-left {{ content: none; }}
            @top-right {{ content: none; }}
        }}
        
        /* 콘텐츠가 페이지를 넘어갈 때 적절한 여백 확보 */
        .line-header {{
            margin-top: 20px;
            page-break-before: auto;
        }}
        
        /* 섹션 제목이 페이지 상단에 올 때 여백 추가 */
        .section-title {{
            margin-top: 15px;
            page-break-after: avoid;
        }}
        
        /* 행이 페이지를 넘어가지 않도록 */
        .line-row {{
            page-break-inside: avoid;
        }}
        
        /* 총계 부분이 페이지를 넘어가지 않도록 */
        .footer-total {{
            page-break-inside: avoid;
            margin-top: 30px;
        }}
        
        /* 주요 요소들이 혼자 페이지에 남지 않도록 */
        .address-section {{
            page-break-after: avoid;
        }}
        
        .header-top {{
            page-break-after: avoid;
        }}
        
        /* 본문 전체 여백 최적화 */
        body {{
            margin: 0;
            padding: 0;
        }}
    """)

    HTML(string=html_content).write_pdf(output_path, stylesheets=[base_css, header_footer_css])

def generate_estimate_pdf(context: dict, output_path: str):
    generate_pdf(context, output_path, doc_type="estimate")

def generate_invoice_pdf(context: dict, output_path: str):
    generate_pdf(context, output_path, doc_type="invoice")

def clean_nan(obj):
    if isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan(v) for v in obj]
    elif isinstance(obj, float) and math.isnan(obj):
        return ""
    return obj