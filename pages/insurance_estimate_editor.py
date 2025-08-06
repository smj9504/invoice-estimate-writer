import streamlit as st
import json
import tempfile
import pandas as pd
import math
import re
from pathlib import Path
import copy
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import logging
from pdf_generator import generate_insurance_estimate_pdf
from modules.company_module import get_all_companies

# =============================================================================
# CONFIGURATION - Data Storage Paths
# =============================================================================
def get_project_root():
    """프로젝트 루트 디렉토리 반환"""
    current_file = Path(__file__).resolve()
    
    # pages 폴더에서 상위로 이동하여 프로젝트 루트 찾기
    if current_file.parent.name == "pages":
        return current_file.parent.parent
    else:
        # 파일이 루트에 있는 경우
        return current_file.parent
    

PROJECT_ROOT = get_project_root()
DATA_STORAGE_PATH = PROJECT_ROOT / "data" / "insurance_estimate"
TEMP_STORAGE_PATH = DATA_STORAGE_PATH / "temp"
PDF_STORAGE_PATH = DATA_STORAGE_PATH / "pdf"
JSON_STORAGE_PATH = DATA_STORAGE_PATH / "json"

# Configure logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Estimate Editor", page_icon="📋", layout="wide")

def safe_float_conversion(value, default=0.0):
    """
    Enhanced 안전한 float 변환 with string parsing
    Handles: $, commas, percentages, empty strings, None
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

def safe_decimal_conversion(value, default=0.0):
    """
    Safely convert value to Decimal for precise calculations, handling:
    - Empty strings and None
    - Dollar signs ($)
    - Commas (,)
    - Percentage signs (%)
    - Various string formats
    """
    if value is None or value == '' or value == 'None':
        return Decimal(str(default))
    
    try:
        # Convert to string first
        str_value = str(value).strip()
        
        # Handle empty string
        if not str_value:
            return Decimal(str(default))
        
        # Handle special cases
        if str_value.lower() in ['nan', 'none', 'null']:
            return Decimal(str(default))
        
        # Remove dollar signs, commas, and spaces
        cleaned_value = re.sub(r'[$,\s]', '', str_value)
        
        # Handle percentage - remove % but keep the number as-is
        # e.g., "10%" → 10.0, not 0.1
        if '%' in cleaned_value:
            cleaned_value = cleaned_value.replace('%', '')
            # Don't divide by 100 here - the calculation will handle it later
            return Decimal(str(float(cleaned_value)))
        
        # Handle empty string after cleaning
        if not cleaned_value:
            return Decimal(str(default))
        
        # Convert to Decimal
        return Decimal(str(float(cleaned_value)))
        
    except (ValueError, TypeError, AttributeError):
        return Decimal(str(default))

def round_to_cents(decimal_value):
    """Round decimal value to 2 decimal places (cents)"""
    return decimal_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

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

def ensure_storage_directories():
    """필요한 저장 디렉토리들이 존재하는지 확인하고 생성"""
    directories = [DATA_STORAGE_PATH, TEMP_STORAGE_PATH, PDF_STORAGE_PATH, JSON_STORAGE_PATH]
    
    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create directory {directory}: {str(e)}")
    
    return DATA_STORAGE_PATH

def get_storage_path(storage_type="temp"):
    """
    저장 경로 반환
    Args:
        storage_type: 'temp', 'pdf', 'json', or 'base'
    Returns:
        Path object for the requested storage type
    """
    path_mapping = {
        'base': DATA_STORAGE_PATH,
        'temp': TEMP_STORAGE_PATH,
        'pdf': PDF_STORAGE_PATH, 
        'json': JSON_STORAGE_PATH
    }
    
    return path_mapping.get(storage_type, TEMP_STORAGE_PATH)

def generate_estimate_number(client_address=""):
    """Generate estimate number: EST_YYYYMM_{property address first 4 chars}"""
    now = datetime.now()
    year_month = now.strftime("%Y%m")
    
    # Extract first 4 alphanumeric characters from address
    address_prefix = ""
    if client_address:
        alphanumeric = ''.join(c.upper() for c in client_address if c.isalnum())
        address_prefix = alphanumeric[:4].ljust(4, '0')  # Pad with 0 if less than 4 chars
    else:
        address_prefix = "0000"
    
    return f"EST_{year_month}_{address_prefix}"

def get_default_estimate_date():
    """Return today's date"""
    return datetime.now().strftime("%Y-%m-%d")

def validate_json_subtotal(data):
    """
    Validate if the subtotal in the JSON matches the sum of location subtotals
    Returns: (is_valid, calculated_subtotal, json_subtotal, discrepancy)
    """
    calculated_subtotal = 0.0
    
    # Calculate subtotal from location subtotals
    for trade in data.get('trades', []):
        for location in trade.get('locations', []):
            # 먼저 stored subtotal 사용
            location_subtotal = safe_float_conversion(location.get('subtotal', 0))
            
            if location_subtotal > 0:
                # stored subtotal이 있으면 사용
                calculated_subtotal += location_subtotal
                logger.info(f"Using stored subtotal for location '{location.get('name', 'Unknown')}': ${location_subtotal}")
            else:
                # stored subtotal이 없으면 아이템별 계산
                categories = location.get('categories', [])
                if categories:
                    item_total = 0.0
                    for category in categories:
                        items = category.get('items', [])
                        for item in items:
                            if all(key in item for key in ['qty', 'price']):
                                qty = safe_float_conversion(item.get('qty', 0))
                                price = safe_float_conversion(item.get('price', 0))
                                item_total += qty * price
                    location_subtotal = item_total
                    calculated_subtotal += location_subtotal
                    logger.info(f"Calculated subtotal for location '{location.get('name', 'Unknown')}': ${location_subtotal}")
                else:
                    logger.warning(f"No categories and no stored subtotal for location '{location.get('name', 'Unknown')}'")
    
    json_subtotal = safe_float_conversion(data.get('subtotal', 0))
    discrepancy = abs(calculated_subtotal - json_subtotal)
    is_valid = discrepancy < 0.01
    
    logger.info(f"Subtotal validation - Calculated: ${calculated_subtotal:,.2f}, JSON: ${json_subtotal:,.2f}, Discrepancy: ${discrepancy:,.2f}")
    
    return is_valid, calculated_subtotal, json_subtotal, discrepancy

def validate_json_item_subtotals(data):
    """
    Validate if location subtotals match the sum of their items
    Returns: (is_valid, validation_details)
    """
    validation_details = []
    all_valid = True
    
    for trade_idx, trade in enumerate(data.get('trades', [])):
        for loc_idx, location in enumerate(trade.get('locations', [])):
            stored_location_total = safe_float_conversion(location.get('subtotal', 0))
            
            # categories가 있는 경우만 계산으로 검증
            categories = location.get('categories', [])
            if categories:
                calculated_location_total = 0.0
                for category in categories:
                    items = category.get('items', [])
                    for item in items:
                        if all(key in item for key in ['qty', 'price']):
                            qty = safe_float_conversion(item.get('qty', 0))
                            price = safe_float_conversion(item.get('price', 0))
                            calculated_location_total += qty * price
                
                discrepancy = abs(calculated_location_total - stored_location_total)
                is_location_valid = discrepancy < 0.01
                
                if not is_location_valid:
                    all_valid = False
                
                validation_details.append({
                    'trade_name': trade.get('name', f'Trade {trade_idx+1}'),
                    'location_name': location.get('name', f'Location {loc_idx+1}'),
                    'calculated': calculated_location_total,
                    'stored': stored_location_total,
                    'discrepancy': discrepancy,
                    'is_valid': is_location_valid,
                    'has_categories': True
                })
            else:
                # categories가 없으면 stored value 사용하고 유효한 것으로 처리
                validation_details.append({
                    'trade_name': trade.get('name', f'Trade {trade_idx+1}'),
                    'location_name': location.get('name', f'Location {loc_idx+1}'),
                    'calculated': stored_location_total,
                    'stored': stored_location_total,
                    'discrepancy': 0.0,
                    'is_valid': True,
                    'has_categories': False
                })
    
    return all_valid, validation_details

def initialize_missing_fields(data):
    """
    Ensure all required fields are initialized in the JSON if missing
    """
    # Initialize main structure
    if 'company' not in data:
        data['company'] = {}
    if 'client' not in data:
        data['client'] = {}
    if 'trades' not in data:
        data['trades'] = []
    
    # Initialize financial fields with safe defaults
    financial_fields = {
        'subtotal': 0.0,
        'total': 0.0,
        'overhead_rate': 0.0,
        'profit_rate': 0.0,
        'overhead_amount': 0.0,
        'profit_amount': 0.0,
        'sales_tax_amount': 0.0,
        'discount': 0.0
    }
    
    for field, default_value in financial_fields.items():
        if field not in data or data[field] is None or data[field] == '':
            data[field] = default_value
            logger.info(f"Initialized missing field '{field}' with default value: {default_value}")
    
    # Initialize nested objects
    if 'overhead' not in data:
        data['overhead'] = {'rate': 0.0, 'amount': 0.0}
    if 'profit' not in data:
        data['profit'] = {'rate': 0.0, 'amount': 0.0}
    if 'sales_tax' not in data:
        data['sales_tax'] = {'amount': 0.0}
    
    # Initialize date fields
    if not data.get('estimate_date'):
        data['estimate_date'] = datetime.now().strftime("%Y-%m-%d")
        logger.info(f"Initialized missing estimate_date with today: {data['estimate_date']}")
    
    # Initialize estimate number if missing
    if not data.get('estimate_number'):
        client_address = data.get('client', {}).get('address', '')
        data['estimate_number'] = generate_estimate_number(client_address)
        logger.info(f"Generated missing estimate_number: {data['estimate_number']}")
    
    return data

def test_edge_cases(data):
    """
    Test the data with various edge cases to ensure robustness
    Returns: list of issues found
    """
    issues = []
    
    # Test 1: Missing trades
    if not data.get('trades'):
        issues.append("No trades found in data")
    
    # Test 2: Empty items and categories
    empty_locations = 0
    locations_without_categories = 0
    
    for trade in data.get('trades', []):
        for location in trade.get('locations', []):
            categories = location.get('categories', [])
            if not categories:
                locations_without_categories += 1
                continue
                
            has_items = False
            for category in categories:
                if category.get('items'):
                    has_items = True
                    break
            if not has_items:
                empty_locations += 1
    
    if empty_locations > 0:
        issues.append(f"{empty_locations} location(s) have no items")
    
    if locations_without_categories > 0:
        issues.append(f"{locations_without_categories} location(s) have no categories")
    
    # Test 3: Negative values
    if safe_float_conversion(data.get('subtotal', 0)) < 0:
        issues.append("Negative subtotal detected")
    
    if safe_float_conversion(data.get('total', 0)) < 0:
        issues.append("Negative total detected")
    
    # Test 4: Inconsistent rates
    overhead_rate = safe_float_conversion(data.get('overhead_rate', 0))
    profit_rate = safe_float_conversion(data.get('profit_rate', 0))
    
    if overhead_rate > 50:
        issues.append(f"Unusually high overhead rate: {overhead_rate}%")
    
    if profit_rate > 50:
        issues.append(f"Unusually high profit rate: {profit_rate}%")
    
    # Test 5: Missing required client info
    client = data.get('client', {})
    if not client.get('name'):
        issues.append("Missing client name")
    
    return issues

def normalize_overhead_profit_structure(data):
    """Normalize overhead, profit, and sales tax structure to handle both formats"""
    # Handle overhead
    if 'overhead' in data and isinstance(data['overhead'], dict):
        # New format: {"rate": 0.10, "amount": 4229.73}
        # Convert rate from decimal to percentage (0.10 -> 10%)
        overhead_rate = safe_float_conversion(data['overhead'].get('rate', 0))
        if overhead_rate > 0 and overhead_rate <= 1:
            overhead_rate = overhead_rate * 100  # Convert 0.10 to 10
        overhead_amount = safe_float_conversion(data['overhead'].get('amount', 0))
        data['overhead_rate'] = overhead_rate
        data['overhead_amount'] = overhead_amount
    else:
        # Old format or missing - use existing values if available
        data['overhead_rate'] = safe_float_conversion(data.get('overhead_rate', 0))
        data['overhead_amount'] = safe_float_conversion(data.get('overhead_amount', 0))
    
    # Handle profit
    if 'profit' in data and isinstance(data['profit'], dict):
        # New format: {"rate": 0.05, "amount": 1626.82}
        # Convert rate from decimal to percentage (0.05 -> 5%)
        profit_rate = safe_float_conversion(data['profit'].get('rate', 0))
        if profit_rate > 0 and profit_rate <= 1:
            profit_rate = profit_rate * 100  # Convert 0.05 to 5
        profit_amount = safe_float_conversion(data['profit'].get('amount', 0))
        data['profit_rate'] = profit_rate
        data['profit_amount'] = profit_amount
    else:
        # Old format or missing - use existing values if available
        data['profit_rate'] = safe_float_conversion(data.get('profit_rate', 0))
        data['profit_amount'] = safe_float_conversion(data.get('profit_amount', 0))
    
    # Handle sales tax - amount only (no rate calculation)
    if 'sales_tax' in data and isinstance(data['sales_tax'], dict):
        # New format: {"amount": 1293.67}
        tax_amount = safe_float_conversion(data['sales_tax'].get('amount', 0))
        data['sales_tax_amount'] = tax_amount
    else:
        # Old format or missing - use existing values if available
        data['sales_tax_amount'] = safe_float_conversion(data.get('sales_tax_amount', data.get('sales_tax', 0)))
    
    # Ensure the overhead, profit, and sales_tax objects are properly structured
    data['overhead'] = {
        'rate': data.get('overhead_rate', 0),
        'amount': data.get('overhead_amount', 0)
    }
    data['profit'] = {
        'rate': data.get('profit_rate', 0),
        'amount': data.get('profit_amount', 0)
    }
    data['sales_tax'] = {
        'amount': data.get('sales_tax_amount', 0)
    }
    
    return data

def calculate_totals(data, force_recalculate=False):
    """
    Calculate all totals with precise decimal arithmetic to avoid floating point errors
    Enhanced to handle categories 없는 경우 with stored subtotal priority
    """
    # Initialize missing fields first
    data = initialize_missing_fields(data)
    
    # Normalize overhead, profit, and sales tax structure
    data = normalize_overhead_profit_structure(data)
    
    # Validate input data
    is_subtotal_valid, calc_subtotal, json_subtotal, discrepancy = validate_json_subtotal(data)
    items_valid, validation_details = validate_json_item_subtotals(data)
    
    # Calculate subtotal from items using Decimal for precision
    subtotal_from_items = Decimal('0.0')
    
    for trade in data.get('trades', []):
        for location in trade.get('locations', []):
            location_total = Decimal('0.0')
            
            # Check if we have categories with items
            categories = location.get('categories', [])
            if categories:
                # Always calculate from items when categories exist
                for category in categories:
                    items = category.get('items', [])
                    for item in items:
                        if all(key in item for key in ['qty', 'price']):
                            qty = safe_decimal_conversion(item.get('qty', 0))
                            price = safe_decimal_conversion(item.get('price', 0))
                            item_total = qty * price
                            
                            # Store rounded value back to item for display
                            item['total_price'] = float(round_to_cents(item_total))
                            location_total += item_total
                            logger.info(f"Item '{item.get('name', 'Unknown')}': ${qty} × ${price} = ${item_total}")
                
                logger.info(f"Calculated subtotal for location '{location.get('name', 'Unknown')}': ${location_total}")
            else:
                # Only use stored subtotal when no categories exist
                stored_subtotal = safe_decimal_conversion(location.get('subtotal', 0))
                if stored_subtotal > 0:
                    location_total = stored_subtotal
                    logger.info(f"No categories found, using stored subtotal for location '{location.get('name', 'Unknown')}': ${stored_subtotal}")
                else:
                    logger.warning(f"No categories and no stored subtotal for location '{location.get('name', 'Unknown')}'")
                    location_total = Decimal('0.0')
            
            # Round and store location subtotal
            location_subtotal_rounded = round_to_cents(location_total)
            location['subtotal'] = float(location_subtotal_rounded)
            subtotal_from_items += location_subtotal_rounded
    
    # Get existing values as Decimals
    existing_subtotal = safe_decimal_conversion(data.get('subtotal', 0))
    existing_overhead_amount = safe_decimal_conversion(data.get('overhead_amount', 0))
    existing_profit_amount = safe_decimal_conversion(data.get('profit_amount', 0))
    existing_total = safe_decimal_conversion(data.get('total', 0))
    existing_sales_tax_amount = safe_decimal_conversion(data.get('sales_tax_amount', 0))
    
    # Decision logic for recalculation
    # Always recalculate if items don't match subtotals (validation failed)
    should_recalculate = (
        force_recalculate or
        not is_subtotal_valid or
        not items_valid or  # This ensures recalculation when location subtotals don't match items
        existing_subtotal <= 0 or
        existing_total <= 0 or
        abs(float(existing_subtotal - subtotal_from_items)) > 0.01
    )
    
    if should_recalculate:
        logger.info("Performing precise recalculation with enhanced parsing")
        
        # Use calculated subtotal
        data['subtotal'] = float(round_to_cents(subtotal_from_items))
        
        # Calculate Overhead & Profit with Decimal precision
        overhead_rate = safe_decimal_conversion(data.get('overhead_rate', 0))
        profit_rate = safe_decimal_conversion(data.get('profit_rate', 0))
        
        # Precise percentage calculations
        overhead_amount = round_to_cents(subtotal_from_items * overhead_rate / Decimal('100'))
        profit_amount = round_to_cents(subtotal_from_items * profit_rate / Decimal('100'))
        
        data['overhead_amount'] = float(overhead_amount)
        data['profit_amount'] = float(profit_amount)
        
        # Sales tax is a fixed amount (not calculated from rate)
        # Always use the amount from JSON, never calculate from rate
        sales_tax_amount = safe_decimal_conversion(data.get('sales_tax_amount', 0))
        # Also check if it's in the nested object
        if sales_tax_amount == 0 and isinstance(data.get('sales_tax'), dict):
            sales_tax_amount = safe_decimal_conversion(data['sales_tax'].get('amount', 0))
        data['sales_tax_amount'] = float(round_to_cents(sales_tax_amount))
        
        # Update objects for consistency
        data['overhead'] = {
            'rate': float(overhead_rate),
            'amount': float(overhead_amount)
        }
        data['profit'] = {
            'rate': float(profit_rate),
            'amount': float(profit_amount)
        }
        data['sales_tax'] = {
            'amount': float(sales_tax_amount)
        }
        
        # Final total calculation with Decimal precision
        discount = safe_decimal_conversion(data.get('discount', 0))
        calculated_total = round_to_cents(
            subtotal_from_items + overhead_amount + profit_amount + sales_tax_amount - discount
        )
        data['total'] = float(calculated_total)
        
        # Log precise calculation details
        logger.info("=== ENHANCED CALCULATION DETAILS ===")
        logger.info(f"Subtotal from items: ${subtotal_from_items}")
        logger.info(f"Overhead ({overhead_rate}%): ${overhead_amount}")
        logger.info(f"Profit ({profit_rate}%): ${profit_amount}")
        logger.info(f"Sales Tax: ${sales_tax_amount}")
        logger.info(f"Discount: ${discount}")
        logger.info(f"Total: ${calculated_total}")
        logger.info("=== END ENHANCED CALCULATION ===")
        
    else:
        # Preserve existing values but ensure consistency
        data['subtotal'] = float(existing_subtotal)
        data['total'] = float(existing_total)
        data['overhead_amount'] = float(existing_overhead_amount)
        data['profit_amount'] = float(existing_profit_amount)
        data['sales_tax_amount'] = float(existing_sales_tax_amount)
        
        # Ensure objects exist for consistency
        data['overhead'] = {
            'rate': data.get('overhead_rate', 0),
            'amount': float(existing_overhead_amount)
        }
        data['profit'] = {
            'rate': data.get('profit_rate', 0),
            'amount': float(existing_profit_amount)
        }
        data['sales_tax'] = {
            'amount': float(existing_sales_tax_amount)
        }
        
        logger.info("✅ Preserved existing calculations")
    
    return data

def display_validation_results(data):
    """
    Display validation results in Streamlit UI
    """
    st.subheader("🔍 JSON Validation Results")
    
    # Validate subtotals
    is_subtotal_valid, calc_subtotal, json_subtotal, discrepancy = validate_json_subtotal(data)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if is_subtotal_valid:
            st.success("✅ Subtotal Valid")
        else:
            st.error("❌ Subtotal Invalid")
        st.metric("JSON Subtotal", f"${json_subtotal:,.2f}")
    
    with col2:
        st.metric("Calculated Subtotal", f"${calc_subtotal:,.2f}")
    
    with col3:
        st.metric("Discrepancy", f"${discrepancy:,.2f}")
    
    # Validate item-level subtotals
    items_valid, validation_details = validate_json_item_subtotals(data)
    
    if not items_valid:
        st.warning("⚠️ Some location subtotals don't match their items")
        
        with st.expander("Location Validation Details"):
            for detail in validation_details:
                if not detail['is_valid']:
                    if detail['has_categories']:
                        st.error(f"❌ {detail['trade_name']} > {detail['location_name']}: "
                                f"Stored: ${detail['stored']:,.2f}, "
                                f"Calculated: ${detail['calculated']:,.2f}, "
                                f"Diff: ${detail['discrepancy']:,.2f}")
                    else:
                        st.warning(f"⚠️ {detail['trade_name']} > {detail['location_name']}: "
                                  f"No categories found, using stored value: ${detail['stored']:,.2f}")
    
    # Display locations without categories
    locations_without_categories = []
    for trade in data.get('trades', []):
        for location in trade.get('locations', []):
            if not location.get('categories', []):
                locations_without_categories.append(f"{trade.get('name', 'Unknown')} > {location.get('name', 'Unknown')}")
    
    if locations_without_categories:
        st.info(f"ℹ️ Locations without categories: {', '.join(locations_without_categories)}")

def save_temp_json(data, filename="temp_estimate.json", storage_type="temp"):
    """
    Save JSON file to specified storage path
    """
    storage_path = get_storage_path(storage_type)
    file_path = storage_path / filename
    
    try:
        # Deep copy to protect original data
        data_to_save = copy.deepcopy(data)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=2, ensure_ascii=False)
        
        logger.info(f"JSON saved successfully: {file_path}")
        return file_path
        
    except Exception as e:
        logger.error(f"Failed to save JSON to {file_path}: {str(e)}")
        # Fallback to system temp directory
        fallback_dir = Path(tempfile.gettempdir()) / "estimate_editor"
        fallback_dir.mkdir(exist_ok=True)
        fallback_path = fallback_dir / filename
        
        with open(fallback_path, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=2, ensure_ascii=False)
        
        logger.warning(f"JSON saved to fallback location: {fallback_path}")
        return fallback_path

def load_temp_json(filename="temp_estimate.json", storage_type="temp"):
    """
    Load JSON file from specified storage path
    """
    storage_path = get_storage_path(storage_type)
    file_path = storage_path / filename
    
    # Try main storage location first
    if file_path.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"JSON loaded successfully: {file_path}")
            return data
        except Exception as e:
            logger.error(f"Failed to load JSON from {file_path}: {str(e)}")
    
    # Fallback to system temp directory
    fallback_dir = Path(tempfile.gettempdir()) / "estimate_editor"
    fallback_path = fallback_dir / filename
    
    if fallback_path.exists():
        try:
            with open(fallback_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"JSON loaded from fallback location: {fallback_path}")
            return data
        except Exception as e:
            logger.error(f"Failed to load JSON from fallback {fallback_path}: {str(e)}")
    
    logger.info(f"JSON file not found: {filename}")
    return None

def save_permanent_json(data, estimate_number):
    """
    Save estimate as permanent JSON file
    """
    # Sanitize estimate number for filename
    safe_estimate_number = "".join(c for c in estimate_number if c.isalnum() or c in ['_', '-'])
    filename = f"{safe_estimate_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    return save_temp_json(data, filename, storage_type="json")

def get_pdf_file_path(session_id, estimate_number="unknown"):
    """
    Get PDF file path for the estimate
    """
    pdf_storage_path = get_storage_path("pdf")
    
    # Sanitize estimate number for filename
    safe_estimate_number = "".join(c for c in estimate_number if c.isalnum() or c in ['_', '-'])
    filename = f"estimate_{safe_estimate_number}_{session_id}.pdf"
    
    return pdf_storage_path / filename

def cleanup_old_temp_files(days_old=7):
    """
    Clean up temporary files older than specified days
    """
    try:
        temp_path = get_storage_path("temp")
        current_time = datetime.now().timestamp()
        cutoff_time = current_time - (days_old * 24 * 3600)
        
        deleted_count = 0
        for file_path in temp_path.glob("*"):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"Failed to delete old temp file {file_path}: {str(e)}")
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old temporary files")
            
    except Exception as e:
        logger.error(f"Failed to cleanup old temp files: {str(e)}")

def display_storage_info():
    """
    Display storage information in Streamlit sidebar
    """
    with st.sidebar:
        st.subheader("📁 Storage Information")
        
        base_path = get_storage_path("base")
        st.write(f"**Base Path:** `{base_path}`")
        
        # Check directory sizes and file counts
        storage_types = ['temp', 'json', 'pdf']
        
        for storage_type in storage_types:
            path = get_storage_path(storage_type)
            if path.exists():
                try:
                    files = list(path.glob("*"))
                    file_count = len([f for f in files if f.is_file()])
                    st.write(f"**{storage_type.title()}:** {file_count} files")
                except Exception:
                    st.write(f"**{storage_type.title()}:** Error reading")
            else:
                st.write(f"**{storage_type.title()}:** Directory not found")
        
        # Cleanup button
        if st.button("🧹 Cleanup Old Files"):
            cleanup_old_temp_files()
            st.success("Cleanup completed!")
            st.rerun()

def save_estimate_with_validation(data, session_id, is_permanent=False):
    """
    Save estimate with validation and proper error handling
    """
    try:
        # Validate data before saving
        if not data:
            return False, None, "No data to save"
        
        # Generate filename
        estimate_number = data.get('estimate_number', 'unknown')
        
        if is_permanent:
            file_path = save_permanent_json(data, estimate_number)
            message = f"Estimate saved permanently: {file_path.name}"
        else:
            temp_filename = f"estimate_{session_id}.json"
            file_path = save_temp_json(data, temp_filename, storage_type="temp")
            message = f"Estimate saved temporarily: {file_path.name}"
        
        return True, file_path, message
        
    except Exception as e:
        error_message = f"Failed to save estimate: {str(e)}"
        logger.error(error_message)
        return False, None, error_message

def render_company_info(data):
    """Company information selection UI (from database)"""
    st.subheader("Company Information")
    
    # Get company information from database
    companies = get_all_companies()
    if not companies:
        st.warning("No registered companies found. Please register company information first.")
        st.stop()

    company_names = [c["name"] for c in companies]
    
    # Set default index based on current selection
    current_company_name = data.get('company', {}).get('name', '')
    default_index = 0
    if current_company_name in company_names:
        default_index = company_names.index(current_company_name)
    elif st.session_state.get("selected_company", {}).get("name") in company_names:
        default_index = company_names.index(st.session_state["selected_company"]["name"])
    
    company_name = st.selectbox(
        "Select Company",
        company_names,
        index=default_index,
        key="company_selector"
    )
    
    selected_company = next((c for c in companies if c["name"] == company_name), None)
    
    if selected_company:
        # Update data with selected company information
        data['company'] = {
            'name': selected_company.get('name', ''),
            'address': selected_company.get('address', ''),
            'city': selected_company.get('city', ''),
            'state': selected_company.get('state', ''),
            'zip': selected_company.get('zip', ''),
            'phone': selected_company.get('phone', ''),
            'email': selected_company.get('email', ''),
            'logo': selected_company.get('logo', '')
        }
        
        # Display selected company information (read-only)
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("Company Name", selected_company.get('name', ''), disabled=True)
            st.text_input("Address", selected_company.get('address', ''), disabled=True)
            st.text_input("City", selected_company.get('city', ''), disabled=True)
        
        with col2:
            st.text_input("State", selected_company.get('state', ''), disabled=True)
            st.text_input("ZIP Code", selected_company.get('zip', ''), disabled=True)
            st.text_input("Phone", selected_company.get('phone', ''), disabled=True)
            st.text_input("Email", selected_company.get('email', ''), disabled=True)

def render_client_info(data):
    """Client information editing UI"""
    st.subheader("Client Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        data['client']['name'] = st.text_input("Client Name", data.get('client', {}).get('name', ''))
        data['client']['address'] = st.text_input("Client Address", data.get('client', {}).get('address', ''))
        data['client']['city'] = st.text_input("Client City", data.get('client', {}).get('city', ''))
    
    with col2:
        data['client']['state'] = st.text_input("Client State", data.get('client', {}).get('state', ''))
        data['client']['zip'] = st.text_input("Client ZIP Code", data.get('client', {}).get('zip', ''))
        data['client']['phone'] = st.text_input("Client Phone", data.get('client', {}).get('phone', ''))
        data['client']['email'] = st.text_input("Client Email", data.get('client', {}).get('email', ''))

def render_estimate_meta(data):
    """Estimate meta information editing UI"""
    st.subheader("Estimate Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Estimate number - auto-generate default value
        current_estimate_number = data.get('estimate_number', '')
        if not current_estimate_number:
            client_address = data.get('client', {}).get('address', '')
            current_estimate_number = generate_estimate_number(client_address)
            data['estimate_number'] = current_estimate_number
        
        data['estimate_number'] = st.text_input("Estimate Number", current_estimate_number)
        
        # Estimate date - default is today's date
        current_date = data.get('estimate_date', '')
        if not current_date:
            current_date = get_default_estimate_date()
            data['estimate_date'] = current_date
        
        data['estimate_date'] = st.text_input("Estimate Date", current_date)
    
    with col2:
        current_discount = safe_float_conversion(data.get('discount', 0))
        
        data['discount'] = st.number_input("Discount", value=current_discount, min_value=0.0, step=0.01)
        
        # Sales Tax Amount (not rate-based)
        current_sales_tax_amount = safe_float_conversion(data.get('sales_tax_amount', data.get('sales_tax', {}).get('amount', 0)))
        data['sales_tax_amount'] = st.number_input("Sales Tax Amount", value=current_sales_tax_amount, min_value=0.0, step=0.01)
    
    # Overhead & Profit section
    st.subheader("Overhead & Profit")
    col3, col4 = st.columns(2)
    
    with col3:
        current_overhead_rate = safe_float_conversion(data.get('overhead_rate', 0))
        data['overhead_rate'] = st.number_input("Overhead Rate (%)", value=current_overhead_rate, min_value=0.0, step=0.1)
    
    with col4:
        current_profit_rate = safe_float_conversion(data.get('profit_rate', 0))
        data['profit_rate'] = st.number_input("Profit Rate (%)", value=current_profit_rate, min_value=0.0, step=0.1)

def render_trade_items(data):
    """Trade items editing UI - categories 없는 경우도 처리"""
    st.subheader("Work Items")
    
    for trade_idx, trade in enumerate(data.get('trades', [])):
        with st.expander(f"**{trade.get('name', f'Trade {trade_idx+1}')}**", expanded=True):
            
            # Trade name and note editing
            col1, col2 = st.columns([2, 3])
            with col1:
                trade['name'] = st.text_input(f"Trade Name", trade.get('name', ''), key=f"trade_name_{trade_idx}")
            with col2:
                trade['note'] = st.text_area(f"Trade Note", trade.get('note', ''), key=f"trade_note_{trade_idx}", height=70)
            
            # Locations
            for loc_idx, location in enumerate(trade.get('locations', [])):
                st.markdown(f"**Location: {location.get('name', f'Location {loc_idx+1}')}**")
                
                # Location name and note editing
                col1, col2 = st.columns([2, 3])
                with col1:
                    location['name'] = st.text_input(f"Location Name", location.get('name', ''), key=f"loc_name_{trade_idx}_{loc_idx}")
                with col2:
                    location['note'] = st.text_area(f"Location Note", location.get('note', ''), key=f"loc_note_{trade_idx}_{loc_idx}", height=70)
                
                # Categories and Items - categories 없는 경우 처리
                categories = location.get('categories', [])
                if not categories:
                    st.warning(f"⚠️ No categories found for location '{location.get('name', 'Unknown')}'")
                    # categories가 없으면 빈 리스트로 초기화
                    location['categories'] = []
                else:
                    for cat_idx, category in enumerate(categories):
                        if category.get('name'):
                            st.markdown(f"*{category.get('name')}*")
                        
                        # Items table
                        items = category.get('items', [])
                        if not items:
                            st.info(f"No items in category '{category.get('name', 'Unknown')}'")
                        else:
                            for item_idx, item in enumerate(items):
                                col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 1, 1.5, 1.5, 3])
                                
                                with col1:
                                    item['name'] = st.text_input("Item Name", item.get('name', ''), key=f"item_name_{trade_idx}_{loc_idx}_{cat_idx}_{item_idx}")
                                with col2:
                                    current_qty = safe_float_conversion(item.get('qty', 0))
                                    item['qty'] = st.number_input("Qty", value=current_qty, key=f"item_qty_{trade_idx}_{loc_idx}_{cat_idx}_{item_idx}", step=0.01)
                                with col3:
                                    item['unit'] = st.text_input("Unit", item.get('unit', ''), key=f"item_unit_{trade_idx}_{loc_idx}_{cat_idx}_{item_idx}")
                                with col4:
                                    current_price = safe_float_conversion(item.get('price', 0))
                                    item['price'] = st.number_input("Unit Price", value=current_price, key=f"item_price_{trade_idx}_{loc_idx}_{cat_idx}_{item_idx}", step=0.01)
                                with col5:
                                    # Calculate and display total price
                                    item_qty = safe_float_conversion(item.get('qty', 0))
                                    item_price = safe_float_conversion(item.get('price', 0))
                                    total_price = item_qty * item_price
                                    st.metric("Total", f"${total_price:,.2f}")
                                with col6:
                                    item['description'] = st.text_input("Description", item.get('description', ''), key=f"item_desc_{trade_idx}_{loc_idx}_{cat_idx}_{item_idx}")
                        
                        st.markdown("---")

def render_notes(data):
    """Notes editing UI"""
    st.subheader("Notes")
    
    col1, col2 = st.columns(2)
    
    with col1:
        data['top_note'] = st.text_area("Top Note", data.get('top_note', ''), height=100)
    
    with col2:
        data['bottom_note'] = st.text_area("Bottom Note", data.get('bottom_note', ''), height=100)
    
    data['disclaimer'] = st.text_area("Disclaimer", data.get('disclaimer', ''), height=100)

def main():
    st.title("Estimate Editor")
    
    # Initialize storage directories
    try:
        ensure_storage_directories()
    except Exception as e:
        st.warning(f"Storage initialization warning: {str(e)}")
    
    # Display storage information in sidebar
    display_storage_info()
    
    # Check company information
    try:
        companies = get_all_companies()
        if not companies:
            st.error("No registered companies found. Please register company information first.")
            st.stop()
    except Exception as e:
        st.error(f"Error loading company information: {str(e)}")
        st.stop()
    
    # JSON file upload
    uploaded_file = st.file_uploader("Upload JSON Estimate File", type=['json'])
    
    if uploaded_file is not None:
        # Load JSON file with enhanced error handling
        try:
            data = json.load(uploaded_file)
            st.success(f"✅ JSON file '{uploaded_file.name}' loaded successfully")
            
            # Initialize missing fields and normalize structure
            data = initialize_missing_fields(data)
            data = normalize_overhead_profit_structure(data)
            
            # Test edge cases and display warnings
            edge_case_issues = test_edge_cases(data)
            if edge_case_issues:
                st.warning("⚠️ Potential issues detected:")
                for issue in edge_case_issues:
                    st.write(f"• {issue}")
                st.write("---")
            
            # Session-based filename for temporary storage
            if 'session_id' not in st.session_state:
                st.session_state.session_id = str(hash(uploaded_file.name + str(uploaded_file.size)))
            
            temp_filename = f"estimate_{st.session_state.session_id}.json"
            
        except json.JSONDecodeError as e:
            st.error(f"❌ Invalid JSON file: {str(e)}")
            return
        except Exception as e:
            st.error(f"❌ Error loading file: {str(e)}")
            return
        
        # Mode selection
        mode = st.radio("Select Mode", ["Edit", "Preview"], horizontal=True)
        
        if mode == "Edit":
            # Auto-generate estimate number button
            col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
            
            with col_btn1:
                if st.button("Generate Estimate Number", key="generate_estimate_num_btn"):
                    client_address = data.get('client', {}).get('address', '')
                    new_estimate_number = generate_estimate_number(client_address)
                    data['estimate_number'] = new_estimate_number
                    st.success(f"Estimate number generated: '{new_estimate_number}'")
                    st.rerun()
            
            with col_btn2:
                if st.button("🧹 Cleanup Old Files", key="main_cleanup_btn"):
                    cleanup_old_temp_files()
                    st.success("Old temporary files cleaned up!")
            
            # Render editing UI
            render_estimate_meta(data)
            st.markdown("---")
            render_company_info(data)
            st.markdown("---")
            render_client_info(data)
            st.markdown("---")
            render_trade_items(data)
            st.markdown("---")
            render_notes(data)
            
            # Save buttons
            st.markdown("### Save Options")
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if st.button("💾 Save Changes", type="primary", use_container_width=True, key="save_changes_btn"):
                    # Force recalculation when saving changes in edit mode
                    data = calculate_totals(data, force_recalculate=True)
                    
                    # Save to temporary storage
                    success, file_path, message = save_estimate_with_validation(
                        data, st.session_state.session_id, is_permanent=False
                    )
                    
                    if success:
                        st.success(message)
                        st.info(f"📂 Saved to: `{file_path}`")
                    else:
                        st.error(message)
                    
                    st.rerun()
            
            with col2:
                if st.button("📄 Save Permanent", use_container_width=True, key="save_permanent_btn"):
                    # Force recalculation and save as permanent file
                    data = calculate_totals(data, force_recalculate=True)
                    
                    success, file_path, message = save_estimate_with_validation(
                        data, st.session_state.session_id, is_permanent=True
                    )
                    
                    if success:
                        st.success(message)
                        st.info(f"📂 Permanent file: `{file_path}`")
                    else:
                        st.error(message)
            
            with col3:
                if st.button("🔄 Reload", use_container_width=True, key="reload_btn"):
                    st.rerun()
        
        else:  # Preview mode
            # Load saved temporary file if exists
            saved_data = load_temp_json(temp_filename, storage_type="temp")
            if saved_data:
                data = saved_data
                data = initialize_missing_fields(data)
                data = normalize_overhead_profit_structure(data)
                # Use enhanced calculation with validation
                data = calculate_totals(data, force_recalculate=False)
                st.info(f"📁 Loaded from saved changes at: `{get_storage_path('temp')}`")
            else:
                data = initialize_missing_fields(data)
                data = normalize_overhead_profit_structure(data)
                # For new JSON files, always recalculate to ensure accuracy
                data = calculate_totals(data, force_recalculate=True)
                st.info("📊 Fresh calculation from uploaded JSON")

            # Display validation results
            display_validation_results(data)
            st.markdown("---")
            
            # Display preview
            st.subheader("Estimate Preview")
            
            # Summary information with enhanced metrics
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            
            with col1:
                st.metric("Estimate Number", data.get('estimate_number', 'N/A'))
            with col2:
                st.metric("Subtotal", f"${data.get('subtotal', 0):,.2f}")
            with col3:
                overhead_amount = data.get('overhead_amount', 0)
                profit_amount = data.get('profit_amount', 0)
                op_total = overhead_amount + profit_amount
                st.metric("O&P", f"${op_total:,.2f}")
            with col4:
                st.metric("Tax", f"${data.get('sales_tax_amount', 0):,.2f}")
            with col5:
                discount = data.get('discount', 0)
                if discount > 0:
                    st.metric("Discount", f"-${discount:,.2f}")
                else:
                    st.metric("Discount", "None")
            with col6:
                st.metric("Total", f"${data.get('total', 0):,.2f}")
            
            # Debug information (collapsible)
            with st.expander("🔧 Debug Information"):
                st.write("**Calculation Verification:**")
                
                # Manual verification
                manual_subtotal = data.get('subtotal', 0)
                manual_overhead = data.get('overhead_amount', 0)
                manual_profit = data.get('profit_amount', 0)
                manual_tax = data.get('sales_tax_amount', 0)
                manual_discount = data.get('discount', 0)
                manual_total = manual_subtotal + manual_overhead + manual_profit + manual_tax - manual_discount
                
                col_debug1, col_debug2 = st.columns(2)
                
                with col_debug1:
                    st.write("**Stored Values:**")
                    st.write(f"Subtotal: ${data.get('subtotal', 0):,.2f}")
                    st.write(f"Overhead ({data.get('overhead_rate', 0)}%): ${data.get('overhead_amount', 0):,.2f}")
                    st.write(f"Profit ({data.get('profit_rate', 0)}%): ${data.get('profit_amount', 0):,.2f}")
                    st.write(f"Sales Tax: ${data.get('sales_tax_amount', 0):,.2f}")
                    st.write(f"Discount: ${data.get('discount', 0):,.2f}")
                    st.write(f"**Stored Total: ${data.get('total', 0):,.2f}**")
                
                with col_debug2:
                    st.write("**Manual Verification:**")
                    st.write(f"Subtotal: ${manual_subtotal:,.2f}")
                    st.write(f"+ Overhead: ${manual_overhead:,.2f}")
                    st.write(f"+ Profit: ${manual_profit:,.2f}")
                    st.write(f"+ Sales Tax: ${manual_tax:,.2f}")
                    st.write(f"- Discount: ${manual_discount:,.2f}")
                    st.write(f"**Calculated Total: ${manual_total:,.2f}**")
                
                # Show discrepancy if any
                total_discrepancy = abs(data.get('total', 0) - manual_total)
                if total_discrepancy > 0.01:
                    st.error(f"⚠️ Total discrepancy detected: ${total_discrepancy:,.2f}")
                else:
                    st.success("✅ Total calculation verified")
                
                # Show storage paths
                st.write("**Storage Paths:**")
                st.write(f"Base: `{get_storage_path('base')}`")
                st.write(f"Temp: `{get_storage_path('temp')}`")
                st.write(f"JSON: `{get_storage_path('json')}`")
                st.write(f"PDF: `{get_storage_path('pdf')}`")
            
            # Detailed breakdown
            st.subheader("Calculation Breakdown")
            breakdown_data = []
            
            subtotal = data.get('subtotal', 0)
            overhead_rate = data.get('overhead_rate', 0)
            overhead_amount = data.get('overhead_amount', 0)
            profit_rate = data.get('profit_rate', 0)
            profit_amount = data.get('profit_amount', 0)
            sales_tax_amount = data.get('sales_tax_amount', 0)
            discount = data.get('discount', 0)
            total = data.get('total', 0)
            
            breakdown_data.append({'Description': 'Subtotal', 'Rate': '', 'Amount': f"${subtotal:,.2f}"})
            
            if overhead_rate > 0:
                breakdown_data.append({'Description': 'Overhead', 'Rate': f"{overhead_rate}%", 'Amount': f"${overhead_amount:,.2f}"})
            
            if profit_rate > 0:
                breakdown_data.append({'Description': 'Profit', 'Rate': f"{profit_rate}%", 'Amount': f"${profit_amount:,.2f}"})
            
            if sales_tax_amount > 0:
                breakdown_data.append({'Description': 'Sales Tax', 'Rate': '', 'Amount': f"${sales_tax_amount:,.2f}"})
            
            if discount > 0:
                breakdown_data.append({'Description': 'Discount', 'Rate': '', 'Amount': f"-${discount:,.2f}"})
            
            breakdown_data.append({'Description': 'Total', 'Rate': '', 'Amount': f"${total:,.2f}"})
            
            st.dataframe(breakdown_data, use_container_width=True, hide_index=True)
            
            # Trade details
            for trade in data.get('trades', []):
                with st.expander(f"**{trade.get('name')}**", expanded=True):
                    for location in trade.get('locations', []):
                        st.markdown(f"**Location: {location.get('name')}** - Subtotal: ${location.get('subtotal', 0):,.2f}")
                        
                        # Items table
                        items_data = []
                        item_num = 1
                        
                        for category in location.get('categories', []):
                            for item in category.get('items', []):
                                if item.get('name'):
                                    qty = safe_float_conversion(item.get('qty', 0))
                                    price = safe_float_conversion(item.get('price', 0))
                                    total_price = qty * price
                                    
                                    items_data.append({
                                        'No.': item_num,
                                        'Item': item.get('name', ''),
                                        'Qty': f"{qty:,.2f}",
                                        'Unit': item.get('unit', ''),
                                        'Unit Price': f"${price:,.2f}",
                                        'Total Price': f"${total_price:,.2f}",
                                        'Description': item.get('description', '')
                                    })
                                    item_num += 1
                        
                        if items_data:
                            st.dataframe(items_data, use_container_width=True)
            
            # Floor plan data upload section
            with st.expander("📐 Floor Plan Data (Optional)", expanded=False):
                st.info("Upload floor plan data to include room diagrams in the PDF")
                
                col_fp1, col_fp2 = st.columns([1, 1])
                
                with col_fp1:
                    # Upload floor plan JSON
                    floor_plan_file = st.file_uploader(
                        "Upload Floor Plan JSON",
                        type=['json'],
                        key="floor_plan_uploader",
                        help="Upload JSON file with room dimensions and measurements"
                    )
                    
                    if floor_plan_file:
                        try:
                            floor_plan_data = json.load(floor_plan_file)
                            data['floor_plans'] = floor_plan_data.get('floor_plans', floor_plan_data)
                            st.success(f"✅ Loaded {len(data['floor_plans'].get('rooms', []))} rooms")
                        except Exception as e:
                            st.error(f"Error loading floor plan: {e}")
                
                with col_fp2:
                    # Show sample format
                    if st.button("📋 Show Sample Format", key="show_sample_floor_plan"):
                        sample_data = {
                            "floor_plans": {
                                "rooms": [
                                    {
                                        "name": "Living Room",
                                        "dimensions": {"length": 20, "width": 15},
                                        "area": 300,
                                        "perimeter": 70,
                                        "measurements": {"ceiling_height": 9},
                                        "work_items": {
                                            "flooring": {"area": 300, "unit": "sq ft"},
                                            "painting": {"area": 540, "unit": "sq ft"}
                                        }
                                    }
                                ]
                            }
                        }
                        st.json(sample_data)
            
            # PDF generation and download buttons
            col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
            
            with col1:
                if st.button("📄 Generate PDF", type="primary", key="generate_pdf_btn"):
                    try:
                        # Get PDF file path using new storage system
                        pdf_file_path = get_pdf_file_path(
                            st.session_state.session_id, 
                            data.get('estimate_number', 'unknown')
                        )
                        
                        # Generate PDF
                        generate_insurance_estimate_pdf(data, str(pdf_file_path))
                        
                        # Provide PDF download
                        with open(pdf_file_path, 'rb') as pdf_file:
                            st.download_button(
                                label="⬇️ Download PDF",
                                data=pdf_file.read(),
                                file_name=f"estimate_{data.get('estimate_number', 'unknown')}.pdf",
                                mime="application/pdf",
                                key="download_pdf_btn"
                            )
                        
                        st.success(f"✅ PDF generated: `{pdf_file_path}`")
                        
                    except Exception as e:
                        st.error(f"❌ Error generating PDF: {str(e)}")
                        logger.error(f"PDF generation error: {str(e)}")
            
            with col2:
                # Generate PDF with Floor Plans
                if st.button("📐 PDF with Plans", type="secondary", key="generate_pdf_with_plans_btn"):
                    try:
                        from pdf_generator import generate_insurance_estimate_pdf_with_plans
                        
                        if 'floor_plans' not in data or not data.get('floor_plans', {}).get('rooms'):
                            st.warning("⚠️ No floor plan data available. Please upload floor plan JSON first.")
                        else:
                            # Get PDF file path
                            pdf_file_path = get_pdf_file_path(
                                st.session_state.session_id, 
                                data.get('estimate_number', 'unknown') + "_with_plans"
                            )
                            
                            # Generate PDF with floor plans
                            generate_insurance_estimate_pdf_with_plans(data, str(pdf_file_path))
                            
                            # Provide PDF download
                            with open(pdf_file_path, 'rb') as pdf_file:
                                st.download_button(
                                    label="⬇️ Download PDF with Plans",
                                    data=pdf_file.read(),
                                    file_name=f"estimate_{data.get('estimate_number', 'unknown')}_with_plans.pdf",
                                    mime="application/pdf",
                                    key="download_pdf_with_plans_btn"
                                )
                            
                            st.success(f"✅ PDF with floor plans generated!")
                        
                    except Exception as e:
                        st.error(f"❌ Error generating PDF with plans: {str(e)}")
                        logger.error(f"PDF with plans generation error: {str(e)}")
            
            with col3:
                # Download modified JSON
                if st.button("📥 Download JSON", key="download_json_main_btn"):
                    json_str = json.dumps(data, indent=2, ensure_ascii=False)
                    st.download_button(
                        label="⬇️ Download JSON File",
                        data=json_str,
                        file_name=f"estimate_{data.get('estimate_number', 'unknown')}.json",
                        mime="application/json",
                        key="download_json_btn"
                    )
            
            with col4:
                # Save permanent copy
                if st.button("💾 Save Permanent Copy", key="save_permanent_copy_btn"):
                    try:
                        success, file_path, message = save_estimate_with_validation(
                            data, st.session_state.session_id, is_permanent=True
                        )
                        
                        if success:
                            st.success(message)
                            st.info(f"📂 Saved to: `{file_path}`")
                        else:
                            st.error(message)
                            
                    except Exception as e:
                        st.error(f"❌ Error saving permanent copy: {str(e)}")
    
    else:
        st.info("Please upload a JSON estimate file.")
        
        # Display storage information even when no file is uploaded
        st.subheader("📁 Storage Configuration")
        st.write(f"**Data Storage Path:** `{DATA_STORAGE_PATH}`")
        st.write(f"**Temporary Files:** `{TEMP_STORAGE_PATH}`")
        st.write(f"**JSON Files:** `{JSON_STORAGE_PATH}`")
        st.write(f"**PDF Files:** `{PDF_STORAGE_PATH}`")
        
        # Display sample JSON structure
        with st.expander("Sample JSON File Structure"):
            sample_json = {
                "estimate_number": "EST_202507_1234",
                "estimate_date": "2025-07-15",
                "company": {
                    "name": "Restoration Services Inc.",
                    "address": "123 Main Street",
                    "city": "Fairfax",
                    "state": "VA",
                    "zip": "22030",
                    "phone": "703-555-1234",
                    "email": "info@restorationservices.com"
                },
                "client": {
                    "name": "John Smith",
                    "address": "1234 Oak Avenue",
                    "city": "Seattle",
                    "state": "WA",
                    "zip": "98102",
                    "phone": "206-555-0123",
                    "email": "john.smith@email.com"
                },
                "trades": [
                    {
                        "name": "Interior Reconstruction",
                        "locations": [
                            {
                                "name": "Back Double Door Bedroom", 
                                "subtotal": 4721.71,
                                "categories": [
                                    {
                                        "name": "Construction & Installation",
                                        "items": [
                                            {
                                                "name": "Wall Drywall",
                                                "qty": 115.43,
                                                "unit": "SF",
                                                "price": 5.25,
                                                "description": "Drywall installation"
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ],
                "subtotal": 43122.38,
                "overhead_rate": 15,
                "profit_rate": 5,
                "sales_tax_amount": 2587.34,
                "discount": 0.0,
                "total": 54334.20
            }
            st.json(sample_json)

if __name__ == "__main__":
    main()