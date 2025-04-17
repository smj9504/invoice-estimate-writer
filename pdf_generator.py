from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
from pathlib import Path
import math

TEMPLATE_DIR = Path(__file__).parent / "templates"
# TEMPLATE_NAME = "general_invoice.html"
# CSS_FILE = TEMPLATE_DIR / "style.css"

TEMPLATE_NAME = "general_estimate.html"
CSS_FILE = TEMPLATE_DIR / "estimate_style.css"


def generate_invoice_pdf(context: dict, output_path: str):
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template(TEMPLATE_NAME)
    html_content = template.render(**context)

    with open(CSS_FILE, "r") as css_file:
        css = CSS(string=css_file.read())

    HTML(string=html_content).write_pdf(output_path, stylesheets=[css])

def generate_estimate_pdf(context: dict, output_path: str):
    context = clean_nan(context)
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template(TEMPLATE_NAME)
    html_content = template.render(**context)

    with open(CSS_FILE, "r") as css_file:
        css = CSS(string=css_file.read())

    HTML(string=html_content).write_pdf(output_path, stylesheets=[css])


def clean_nan(obj):
    if isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan(v) for v in obj]
    elif isinstance(obj, float) and math.isnan(obj):
        return ""
    return obj
