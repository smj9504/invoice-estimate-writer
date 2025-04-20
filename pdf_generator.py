from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
from pathlib import Path
import math

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

def generate_pdf(context: dict, output_path: str, doc_type: str = "estimate"):
    context = clean_nan(context)
    config = TEMPLATE_MAP[doc_type]
    template_path = config["template"]
    css_path = TEMPLATE_DIR / config["css"]

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template(template_path)
    html_content = template.render(**context)

    # 🔍 DEBUG: HTML 내용 확인
    with open("debug_output.html", "w", encoding="utf-8") as debug_file:
        debug_file.write(html_content)

    # ✅ CSS 경로 확인
    if not css_path.exists():
        raise FileNotFoundError(f"CSS 파일이 존재하지 않음: {css_path}")

    with open(css_path, "r", encoding="utf-8") as css_file:
        css = CSS(string=css_file.read())

    HTML(string=html_content).write_pdf(output_path, stylesheets=[css])

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