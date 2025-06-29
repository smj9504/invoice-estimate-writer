import streamlit as st
import json
import tempfile
import os
from pathlib import Path
import copy
from datetime import datetime
from pdf_generator import generate_insurance_estimate_pdf
from modules.company_module import get_all_companies

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

def safe_float_conversion(value, default=0.0):
    """Safely convert value to float, handling empty strings and None"""
    if value is None or value == '' or value == 'None':
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def calculate_totals(data):
    """Calculate all totals for the estimate data"""
    subtotal = 0.0
    
    for trade in data.get('trades', []):
        for location in trade.get('locations', []):
            location_total = 0.0
            
            for category in location.get('categories', []):
                for item in category.get('items', []):
                    if all(key in item for key in ['qty', 'price']):
                        qty = safe_float_conversion(item.get('qty', 0))
                        price = safe_float_conversion(item.get('price', 0))
                        item_total = qty * price
                        location_total += item_total
            
            location['subtotal'] = location_total
            subtotal += location_total
    
    data['subtotal'] = subtotal
    
    # Apply discount
    discount = safe_float_conversion(data.get('discount', 0))
    after_discount = subtotal - discount
    
    # Calculate tax
    tax_rate = safe_float_conversion(data.get('tax_rate', 0))
    sales_tax = after_discount * (tax_rate / 100)
    data['sales_tax'] = sales_tax
    
    # Final total
    total = after_discount + sales_tax
    data['total'] = total
    
    return data

def save_temp_json(data, filename="temp_estimate.json"):
    """Save temporary JSON file"""
    temp_dir = Path(tempfile.gettempdir()) / "estimate_editor"
    temp_dir.mkdir(exist_ok=True)
    file_path = temp_dir / filename
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return file_path

def load_temp_json(filename="temp_estimate.json"):
    """Load temporary JSON file"""
    temp_dir = Path(tempfile.gettempdir()) / "estimate_editor"
    file_path = temp_dir / filename
    
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

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
        current_tax_rate = safe_float_conversion(data.get('tax_rate', 0))
        
        data['discount'] = st.number_input("Discount", value=current_discount, min_value=0.0, step=0.01)
        data['tax_rate'] = st.number_input("Tax Rate", value=current_tax_rate, min_value=0.0, step=0.1)

def render_trade_items(data):
    """Trade items editing UI"""
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
                
                # Categories and Items
                for cat_idx, category in enumerate(location.get('categories', [])):
                    if category.get('name'):
                        st.markdown(f"*{category.get('name')}*")
                    
                    # Items table
                    for item_idx, item in enumerate(category.get('items', [])):
                        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1.5, 3])
                        
                        with col1:
                            item['name'] = st.text_input("Item Name", item.get('name', ''), key=f"item_name_{trade_idx}_{loc_idx}_{cat_idx}_{item_idx}")
                        with col2:
                            current_qty = safe_float_conversion(item.get('qty', 0))
                            item['qty'] = st.number_input("Qty", value=current_qty, key=f"item_qty_{trade_idx}_{loc_idx}_{cat_idx}_{item_idx}", step=0.01)
                        with col3:
                            item['unit'] = st.text_input("Unit", item.get('unit', ''), key=f"item_unit_{trade_idx}_{loc_idx}_{cat_idx}_{item_idx}")
                        with col4:
                            current_price = safe_float_conversion(item.get('price', 0))
                            item['price'] = st.number_input("Price", value=current_price, key=f"item_price_{trade_idx}_{loc_idx}_{cat_idx}_{item_idx}", step=0.01)
                        with col5:
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
    st.set_page_config(page_title="Estimate Editor", page_icon="📋", layout="wide")
    st.title("Estimate Editor")
    
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
        # Load JSON file
        try:
            data = json.load(uploaded_file)
            # --- ADD THIS DEBUG PRINT AFTER INITIAL JSON LOAD ---
            print(f"DEBUG_EDITOR: After initial JSON load, 'trades' length: {len(data.get('trades', []))}")
            if data.get('trades'):
                print(f"DEBUG_EDITOR: First trade name after initial load: {data['trades'][0].get('name')}")
            # --- END DEBUG PRINT ---
            
            # Set default values
            if 'company' not in data:
                data['company'] = {}
            if 'client' not in data:
                data['client'] = {}
            
            # Set default estimate number and date
            if not data.get('estimate_number'):
                client_address = data.get('client', {}).get('address', '')
                data['estimate_number'] = generate_estimate_number(client_address)
            
            if not data.get('estimate_date'):
                data['estimate_date'] = get_default_estimate_date()
            
            # Save as temporary file (session-based filename)
            if 'session_id' not in st.session_state:
                st.session_state.session_id = str(hash(uploaded_file.name + str(uploaded_file.size)))
            
            temp_filename = f"estimate_{st.session_state.session_id}.json"
            
        except json.JSONDecodeError:
            st.error("Invalid JSON file.")
            return
        
        # Mode selection
        mode = st.radio("Select Mode", ["Edit", "Preview"], horizontal=True)
        
        if mode == "Edit":
            # Auto-generate estimate number button
            col_btn1, col_btn2 = st.columns([1, 3])
            with col_btn1:
                if st.button("Generate Estimate Number"):
                    client_address = data.get('client', {}).get('address', '')
                    new_estimate_number = generate_estimate_number(client_address)
                    data['estimate_number'] = new_estimate_number
                    st.success(f"Estimate number generated: '{new_estimate_number}'")
                    st.rerun()
            
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
            col1, col2 = st.columns([1, 1])
            
            with col1:
                if st.button("Save Changes", type="primary", use_container_width=True):
                    # Perform calculations
                    data = calculate_totals(data)
                    
                    # Save to temporary file
                    temp_path = save_temp_json(data, temp_filename)
                    st.success("Changes saved successfully!")
                    st.rerun()
            
            with col2:
                if st.button("Reload", use_container_width=True):
                    st.rerun()
        
        else:  # Preview mode
            # Load saved temporary file if exists
            saved_data = load_temp_json(temp_filename)
            if saved_data:
                data = saved_data
            else:
                # Perform calculations
                data = calculate_totals(data)
            
            # --- ADD THIS DEBUG PRINT BEFORE PDF GENERATION ---
            print(f"DEBUG_EDITOR: BEFORE PDF Generation, 'trades' length: {len(data.get('trades', []))}")
            if data.get('trades'):
                print(f"DEBUG_EDITOR: First trade name BEFORE PDF Generation: {data['trades'][0].get('name')}")
            # --- END DEBUG PRINT ---

            # Display preview
            st.subheader("Estimate Preview")
            
            # Summary information
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Estimate Number", data.get('estimate_number', 'N/A'))
            with col2:
                st.metric("Subtotal", f"${data.get('subtotal', 0):,.2f}")
            with col3:
                st.metric("Tax", f"${data.get('sales_tax', 0):,.2f}")
            with col4:
                st.metric("Total", f"${data.get('total', 0):,.2f}")
            
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
                                    items_data.append({
                                        'No.': item_num,
                                        'Item': item.get('name', ''),
                                        'Qty': f"{item.get('qty', 0):,.2f}",
                                        'Unit': item.get('unit', ''),
                                        'Price': f"${item.get('price', 0):,.2f}",
                                        'Description': item.get('description', '')
                                    })
                                    item_num += 1
                        
                        if items_data:
                            st.dataframe(items_data, use_container_width=True)
            
            # PDF generation and download buttons
            col1, col2 = st.columns([1, 1])
            
            with col1:
                if st.button("Generate PDF", type="primary"):
                    try:
                        # Create temporary PDF file
                        temp_pdf_path = Path(tempfile.gettempdir()) / f"estimate_{st.session_state.session_id}.pdf"
                        
                        # Generate PDF
                        generate_insurance_estimate_pdf(data, str(temp_pdf_path))
                        
                        # Provide PDF download
                        with open(temp_pdf_path, 'rb') as pdf_file:
                            st.download_button(
                                label="Download PDF",
                                data=pdf_file.read(),
                                file_name=f"estimate_{data.get('estimate_number', 'unknown')}.pdf",
                                mime="application/pdf"
                            )
                        
                        st.success("PDF generated successfully!")
                        
                    except Exception as e:
                        st.error(f"Error generating PDF: {str(e)}")
            
            with col2:
                # Download modified JSON
                if st.button("Download JSON"):
                    json_str = json.dumps(data, indent=2, ensure_ascii=False)
                    st.download_button(
                        label="Download JSON File",
                        data=json_str,
                        file_name=f"estimate_{data.get('estimate_number', 'unknown')}.json",
                        mime="application/json"
                    )
    
    else:
        st.info("Please upload a JSON estimate file.")
        
        # Display sample JSON structure
        with st.expander("Sample JSON File Structure"):
            sample_json = {
                "estimate_number": "EST_202506_1234",
                "estimate_date": "2025-06-18",
                "company": {
                    "name": "ABC Construction",
                    "address": "123 Main St",
                    "city": "Seattle",
                    "state": "WA",
                    "zip": "98101",
                    "phone": "(206) 555-0123",
                    "email": "info@abc.com"
                },
                "client": {
                    "name": "John Smith",
                    "address": "1234 Oak Avenue",
                    "city": "Seattle",
                    "state": "WA",
                    "zip": "98102"
                },
                "trades": [
                    {
                        "name": "Roofing",
                        "note": "Optional trade note",
                        "locations": [
                            {
                                "name": "Main House",
                                "note": "Optional location note",
                                "showSubtotal": True,
                                "categories": [
                                    {
                                        "name": "Installation",
                                        "items": [
                                            {
                                                "name": "Install shingles",
                                                "qty": 25,
                                                "unit": "squares",
                                                "price": 180.00,
                                                "description": "Architectural shingles"
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ],
                "discount": 0.0,
                "tax_rate": 8.5
            }
            st.json(sample_json)

if __name__ == "__main__":
    main()