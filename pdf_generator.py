from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
from pathlib import Path
import math
from datetime import datetime
import pandas as pd

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
    footer_css = CSS(string=f"""
        @page {{
            margin: 0.4in;
                     
            @bottom-left {{
                content: "Generated on {today_str}";
                font-size: 10px;
                color: #999;
            }}
            @bottom-right {{
                content: "Page " counter(page);
                font-size: 10px;
                color: #999;
            }}
        }}
    """)

    HTML(string=html_content).write_pdf(output_path, stylesheets=[base_css, footer_css])

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