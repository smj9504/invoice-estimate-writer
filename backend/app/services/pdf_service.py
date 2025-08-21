"""
PDF Generation Service for React Backend
Separate from Streamlit's pdf_generator.py
"""

from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import os
import sys
from typing import Dict, Any, Optional
import json
import re

# Add GTK+ path for WeasyPrint on Windows
gtk_path = r"C:\Program Files\GTK3-Runtime Win64\bin"
if os.path.exists(gtk_path):
    current_path = os.environ.get('PATH', '')
    os.environ['PATH'] = f"{gtk_path};{current_path}"
    if hasattr(os, 'add_dll_directory'):
        try:
            os.add_dll_directory(gtk_path)
        except Exception:
            pass

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except Exception as e:
    print(f"WeasyPrint not available: {e}")
    WEASYPRINT_AVAILABLE = False
    HTML = None
    CSS = None

# Template directory for React backend
TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)


class PDFService:
    """Service for generating PDF documents"""
    
    def __init__(self):
        if not WEASYPRINT_AVAILABLE:
            raise RuntimeError("WeasyPrint is not available. Please install it with GTK+ runtime.")
        
        self.template_dir = TEMPLATE_DIR
        self.env = Environment(loader=FileSystemLoader(str(self.template_dir)))
        self._register_filters()
    
    def _register_filters(self):
        """Register custom Jinja2 filters"""
        self.env.filters['format_currency'] = self._format_currency
        self.env.filters['format_number'] = self._format_number
        self.env.filters['format_date'] = self._format_date
        self.env.filters['markdown_to_html'] = self._markdown_to_html
    
    @staticmethod
    def _format_currency(value: float) -> str:
        """Format number as currency"""
        try:
            return f"${value:,.2f}"
        except (ValueError, TypeError):
            return "$0.00"
    
    @staticmethod
    def _format_number(value: float, decimal_places: int = 2) -> str:
        """Format number with commas and decimal places"""
        try:
            return f"{value:,.{decimal_places}f}"
        except (ValueError, TypeError):
            return "0"
    
    @staticmethod
    def _format_date(value, format: str = "%B %d, %Y") -> str:
        """Format date string"""
        if isinstance(value, str):
            try:
                dt = datetime.strptime(value, "%Y-%m-%d")
                return dt.strftime(format)
            except:
                return value
        elif isinstance(value, datetime):
            return value.strftime(format)
        return str(value)
    
    @staticmethod
    def _markdown_to_html(text: str) -> str:
        """Convert basic markdown to HTML for notes section"""
        if not text:
            return ""
        
        # Preserve line breaks
        text = text.replace('\n', '<br>\n')
        
        # Convert bold text (**text** or __text__)
        text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'__([^_]+)__', r'<strong>\1</strong>', text)
        
        # Convert italic text (*text* or _text_)
        text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
        text = re.sub(r'_([^_]+)_', r'<em>\1</em>', text)
        
        # Convert underline text (~~text~~)
        text = re.sub(r'~~([^~]+)~~', r'<u>\1</u>', text)
        
        # Convert headers (### Header)
        text = re.sub(r'^###\s+(.+)$', r'<h4>\1</h4>', text, flags=re.MULTILINE)
        text = re.sub(r'^##\s+(.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
        text = re.sub(r'^#\s+(.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
        
        # Convert unordered lists (- item)
        def convert_ul(match):
            items = match.group(0).split('\n')
            html = '<ul>\n'
            for item in items:
                if item.strip().startswith('- '):
                    html += f'  <li>{item.strip()[2:]}</li>\n'
            html += '</ul>'
            return html
        
        text = re.sub(r'(?:^- .+$\n?)+', convert_ul, text, flags=re.MULTILINE)
        
        # Convert ordered lists (1. item)
        def convert_ol(match):
            items = match.group(0).split('\n')
            html = '<ol>\n'
            for item in items:
                if re.match(r'^\d+\.\s+', item.strip()):
                    html += f'  <li>{re.sub(r"^\d+\.\s+", "", item.strip())}</li>\n'
            html += '</ol>'
            return html
        
        text = re.sub(r'(?:^\d+\.\s+.+$\n?)+', convert_ol, text, flags=re.MULTILINE)
        
        # Wrap paragraphs
        paragraphs = text.split('<br>\n<br>\n')
        text = ''.join(f'<p>{p}</p>' for p in paragraphs if p.strip())
        
        return text
    
    def generate_invoice_pdf(self, data: Dict[str, Any], output_path: str) -> str:
        """
        Generate invoice PDF from data
        
        Args:
            data: Invoice data dictionary
            output_path: Path to save the PDF
            
        Returns:
            Path to the generated PDF
        """
        # Validate and prepare data
        context = self._prepare_invoice_context(data)
        
        # Load template
        template = self.env.get_template("invoice.html")
        html_content = template.render(**context)
        
        # Don't load external CSS - use inline styles only
        stylesheets = []
        
        # Add header/footer CSS
        header_footer_css = self._generate_header_footer_css(context)
        stylesheets.append(CSS(string=header_footer_css))
        
        # Generate PDF
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        HTML(string=html_content).write_pdf(
            output_path,
            stylesheets=stylesheets
        )
        
        return str(output_path)
    
    def generate_estimate_pdf(self, data: Dict[str, Any], output_path: str) -> str:
        """
        Generate estimate PDF from data
        
        Args:
            data: Estimate data dictionary
            output_path: Path to save the PDF
            
        Returns:
            Path to the generated PDF
        """
        # Validate and prepare data
        context = self._prepare_estimate_context(data)
        
        # Load template
        template = self.env.get_template("estimate.html")
        html_content = template.render(**context)
        
        # Load CSS
        css_path = self.template_dir / "estimate.css"
        stylesheets = []
        
        if css_path.exists():
            with open(css_path, 'r', encoding='utf-8') as f:
                stylesheets.append(CSS(string=f.read()))
        
        # Add header/footer CSS
        header_footer_css = self._generate_header_footer_css(context)
        stylesheets.append(CSS(string=header_footer_css))
        
        # Generate PDF
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        HTML(string=html_content).write_pdf(
            output_path,
            stylesheets=stylesheets
        )
        
        return str(output_path)
    
    def _prepare_invoice_context(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare and validate invoice context for template"""
        context = data.copy()
        
        # Set defaults
        context.setdefault('invoice_number', self._generate_invoice_number())
        context.setdefault('date', datetime.now().strftime("%Y-%m-%d"))
        context.setdefault('due_date', datetime.now().strftime("%Y-%m-%d"))
        
        # Ensure required sections exist
        context.setdefault('company', {})
        context.setdefault('client', {})
        context.setdefault('items', [])
        context.setdefault('insurance', {})
        
        # Calculate totals
        subtotal = sum(
            item.get('quantity', 0) * item.get('rate', 0)
            for item in context['items']
        )
        
        context['subtotal'] = subtotal
        context.setdefault('tax_rate', 0)
        context['tax_amount'] = subtotal * context['tax_rate'] / 100
        context.setdefault('discount', 0)
        context.setdefault('shipping', 0)
        context['total'] = subtotal - context.get('discount', 0) + context['tax_amount'] + context.get('shipping', 0)
        
        # Convert markdown in notes and payment_terms
        if context.get('notes'):
            context['notes'] = self._markdown_to_html(context['notes'])
        if context.get('payment_terms'):
            context['payment_terms'] = self._markdown_to_html(context['payment_terms'])
        
        return context
    
    def _prepare_estimate_context(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare and validate estimate context for template"""
        context = data.copy()
        
        # Set defaults
        context.setdefault('estimate_number', self._generate_estimate_number())
        context.setdefault('date', datetime.now().strftime("%Y-%m-%d"))
        context.setdefault('valid_until', datetime.now().strftime("%Y-%m-%d"))
        
        # Ensure required sections exist
        context.setdefault('company', {})
        context.setdefault('client', {})
        context.setdefault('items', [])
        
        # Calculate totals
        subtotal = sum(
            item.get('quantity', 0) * item.get('rate', 0)
            for item in context['items']
        )
        
        context['subtotal'] = subtotal
        context.setdefault('tax_rate', 0)
        context['tax_amount'] = subtotal * context['tax_rate'] / 100
        context['total'] = subtotal + context['tax_amount']
        
        return context
    
    def _generate_header_footer_css(self, context: Dict[str, Any]) -> str:
        """Generate CSS for PDF headers and footers"""
        company = context.get('company', {})
        client = context.get('client', {})
        
        # Build company info text
        company_lines = []
        if company.get('name'):
            company_lines.append(company['name'])
        if company.get('address'):
            company_lines.append(company['address'])
        if company.get('phone'):
            company_lines.append(f"Tel: {company['phone']}")
        if company.get('email'):
            company_lines.append(company['email'])
        
        company_text = '\\A '.join(company_lines)
        
        # Build client info text
        client_lines = []
        if client.get('name'):
            client_lines.append(client['name'])
        if client.get('address'):
            client_lines.append(client['address'])
        if client.get('phone'):
            client_lines.append(f"Tel: {client['phone']}")
        
        client_text = '\\A '.join(client_lines)
        
        return f"""
        @page {{
            size: A4;
            margin: 2.5cm 2cm 2cm 2cm;
            
            @top-left {{
                content: "{company_text}";
                font-size: 9pt;
                white-space: pre;
                padding-top: 10px;
            }}
            
            @top-right {{
                content: "{client_text}";
                font-size: 9pt;
                white-space: pre;
                text-align: right;
                padding-top: 10px;
            }}
            
            @bottom-center {{
                content: "Page " counter(page) " of " counter(pages);
                font-size: 9pt;
            }}
            
            @bottom-right {{
                content: "Generated on {datetime.now().strftime('%Y-%m-%d')}";
                font-size: 8pt;
                color: #666;
            }}
        }}
        
        @page :first {{
            @top-left {{
                content: none;
            }}
            @top-right {{
                content: none;
            }}
        }}
        """
    
    def _generate_invoice_number(self) -> str:
        """Generate unique invoice number"""
        return f"INV-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    def _generate_estimate_number(self) -> str:
        """Generate unique estimate number"""
        return f"EST-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    @staticmethod
    def generate_plumber_report_pdf(
        report_data: Dict[str, Any],
        include_photos: bool = True,
        include_financial: bool = True
    ) -> bytes:
        """Generate PDF for Plumber's Report"""
        if not WEASYPRINT_AVAILABLE:
            raise RuntimeError("WeasyPrint is not available")
        
        # Setup template environment
        template_dir = TEMPLATE_DIR / "plumber_report" / "standard"
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        
        # Register filters
        def date_filter(value):
            if isinstance(value, str):
                try:
                    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    return dt.strftime("%B %d, %Y")
                except:
                    return value
            return value
        
        def nl2br_filter(value):
            if value:
                return value.replace('\n', '<br>')
            return value
        
        def safe_filter(value):
            # Allow HTML tags for rich text
            return value
        
        env.filters['date'] = date_filter
        env.filters['nl2br'] = nl2br_filter
        env.filters['safe'] = safe_filter
        
        # Prepare context
        context = report_data.copy()
        context['include_photos'] = include_photos
        context['include_financial'] = include_financial
        
        # Load template
        template = env.get_template('template.html')
        html_content = template.render(**context)
        
        # Load CSS
        css_path = template_dir / 'style.css'
        stylesheets = []
        if css_path.exists():
            with open(css_path, 'r', encoding='utf-8') as f:
                stylesheets.append(CSS(string=f.read()))
        
        # Add page numbering CSS
        page_css = """
        @page {
            size: letter;
            margin: 0.75in;
            
            @bottom-center {
                content: "Page " counter(page) " of " counter(pages);
                font-size: 9pt;
                color: #666;
            }
        }
        
        .page:after { content: counter(page); }
        .topage:after { content: counter(pages); }
        """
        stylesheets.append(CSS(string=page_css))
        
        # Generate PDF
        pdf_document = HTML(string=html_content).write_pdf(stylesheets=stylesheets)
        
        return pdf_document


# Singleton instance
pdf_service = PDFService() if WEASYPRINT_AVAILABLE else None