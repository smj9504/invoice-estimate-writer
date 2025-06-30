import streamlit as st
import json
from datetime import datetime
from typing import Dict, Any, Optional
import base64

# Import utility functions
from utils.intake_utils import (
    create_empty_project, create_empty_room, create_continuity_zone,
    get_damage_source_options, get_contractor_types, get_content_manipulation_options,
    get_building_level_options, get_access_condition_options, get_standard_work_packages,
    get_room_input_methods, get_mitigation_status_options, get_structural_issue_options,
    calculate_room_quantities, calculate_debris_weight, validate_project_data,
    validate_room_data, export_to_json, import_from_json, generate_filename,
    generate_auto_justifications
)
from utils.ai_utils import init_openai_client, ImprovedAIImageAnalyzer

# Page configuration
st.set_page_config(
    page_title="Reconstruction Intake Form v3.0",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
def initialize_session_state():
    """Initialize session state with empty project"""
    if "project_data" not in st.session_state:
        st.session_state.project_data = create_empty_project()
    if "current_room_index" not in st.session_state:
        st.session_state.current_room_index = 0
    if "ai_analyzer" not in st.session_state:
        openai_client = init_openai_client()
        if openai_client:
            st.session_state.ai_analyzer = ImprovedAIImageAnalyzer(openai_client)
        else:
            st.session_state.ai_analyzer = None

def sidebar_navigation():
    """Create sidebar navigation"""
    st.sidebar.title("🏠 Reconstruction Intake v3.0")
    
    # File operations
    st.sidebar.header("📁 File Operations")
    
    # Upload JSON file
    uploaded_file = st.sidebar.file_uploader(
        "Upload existing project JSON",
        type=['json'],
        help="Load a previously saved project"
    )
    
    if uploaded_file is not None:
        try:
            json_str = uploaded_file.read().decode('utf-8')
            imported_data = import_from_json(json_str)
            if imported_data:
                st.session_state.project_data = imported_data
                st.sidebar.success("✅ Project loaded successfully!")
                st.rerun()
            else:
                st.sidebar.error("❌ Invalid JSON file format")
        except Exception as e:
            st.sidebar.error(f"❌ Error loading file: {str(e)}")
    
    # Download JSON file
    if st.sidebar.button("💾 Download Project JSON"):
        json_str = export_to_json(st.session_state.project_data)
        filename = generate_filename(st.session_state.project_data)
        
        st.sidebar.download_button(
            label="📥 Download JSON File",
            data=json_str,
            file_name=filename,
            mime="application/json"
        )
    
    # Navigation menu
    st.sidebar.header("📋 Navigation")
    pages = [
        "🏠 Property & Project Basics",
        "🎯 Work Zone Management", 
        "🔧 Project Standards",
        "📦 Work Packages",
        "🏠 Room Data Entry",
        "🔗 Room Connectivity",
        "🛡️ Protection Matrix",
        "📊 Summary & Export"
    ]
    
    selected_page = st.sidebar.selectbox("Select Section", pages)
    
    # Project validation status
    st.sidebar.header("✅ Validation Status")
    errors = validate_project_data(st.session_state.project_data)
    if errors:
        st.sidebar.error(f"❌ {len(errors)} validation errors")
        with st.sidebar.expander("View Errors"):
            for error in errors:
                st.write(f"• {error}")
    else:
        st.sidebar.success("✅ All validations passed")
    
    return selected_page

def property_basics_page():
    """Property & Project Basics page"""
    st.header("🏠 Property & Project Basics")
    
    property_info = st.session_state.project_data["property_info"]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📍 Property Information")
        property_info["property_address"] = st.text_input(
            "Property Address", 
            value=property_info.get("property_address", "")
        )
        
        property_info["contractor_address"] = st.text_input(
            "Contractor Address",
            value=property_info.get("contractor_address", "")
        )
        
        property_info["photos_url"] = st.text_input(
            "Photos URL/Folder",
            value=property_info.get("photos_url", "")
        )
    
    with col2:
        st.subheader("📋 Claim Information")
        property_info["claim_number"] = st.text_input(
            "Claim Number",
            value=property_info.get("claim_number", "")
        )
        
        property_info["adjuster"] = st.text_input(
            "Adjuster",
            value=property_info.get("adjuster", "")
        )
        
        property_info["construction_year"] = st.text_input(
            "Construction Year",
            value=property_info.get("construction_year", ""),
            help="Auto-flags lead/asbestos if pre-1978/1980"
        )
    
    st.subheader("💥 Damage Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Primary damage source
        damage_options = get_damage_source_options()
        current_damage_source = property_info.get("primary_damage_source", "")
        damage_index = 0
        for i, opt in enumerate(damage_options):
            if opt[0] == current_damage_source:
                damage_index = i
                break
                
        property_info["primary_damage_source"] = st.selectbox(
            "Primary Damage Source",
            options=[opt[0] for opt in damage_options],
            format_func=lambda x: next(opt[1] for opt in damage_options if opt[0] == x),
            index=damage_index
        )
        
        property_info["primary_impact_rooms"] = st.text_input(
            "Primary Impact Room(s)",
            value=property_info.get("primary_impact_rooms", "")
        )
    
    with col2:
        property_info["secondary_impact_areas"] = st.text_input(
            "Secondary Impact Areas",
            value=property_info.get("secondary_impact_areas", "")
        )
    
    # Project coordination
    st.subheader("🤝 Project Coordination")
    
    contractor_types = get_contractor_types()
    selected_contractors = st.multiselect(
        "Other Contractors Involved",
        options=[ct[0] for ct in contractor_types],
        format_func=lambda x: next(ct[1] for ct in contractor_types if ct[0] == x),
        default=st.session_state.project_data["project_coordination"].get("other_contractors", [])
    )
    st.session_state.project_data["project_coordination"]["other_contractors"] = selected_contractors
    
    work_dependencies = st.text_area(
        "Work Sequence Dependencies",
        value="\n".join(st.session_state.project_data["project_coordination"].get("work_sequence_dependencies", [])),
        help="Enter each dependency on a new line"
    )
    st.session_state.project_data["project_coordination"]["work_sequence_dependencies"] = work_dependencies.split('\n') if work_dependencies else []

def work_zone_management_page():
    """Work Zone Management page"""
    st.header("🎯 Work Zone Management")
    
    # Explanation section
    st.info("""
    **🔍 Work Zone Management** helps organize your project by grouping related rooms together.
    This ensures material continuity, efficient scheduling, and professional results.
    """)
    
    with st.expander("📚 How Work Zones Work"):
        st.write("""
        **Real-world example:**
        Your kitchen flooring was damaged by water, but it's connected to your living room in an open floor plan.
        
        **Without zones:** Replace only kitchen flooring → Color/pattern mismatch with living room
        **With zones:** Group kitchen + living room in Zone A → Replace both for seamless appearance
        
        **Benefits:**
        • **Insurance approval**: Justifies replacing connected areas for continuity
        • **Professional finish**: Avoids mismatched materials in visible areas  
        • **Cost efficiency**: Bulk installation is often more economical
        • **Work coordination**: Prevents conflicts between different trades
        """)
    
    work_zones = st.session_state.project_data["work_zones"]
    
    # Content manipulation strategy
    st.subheader("📦 Content Manipulation Strategy")
    
    content_options = get_content_manipulation_options()
    work_zones["content_manipulation_strategy"] = st.selectbox(
        "Content Handling Strategy",
        options=[opt[0] for opt in content_options],
        format_func=lambda x: next(opt[1] for opt in content_options if opt[0] == x),
        index=next((i for i, opt in enumerate(content_options) 
                  if opt[0] == work_zones.get("content_manipulation_strategy", "")), 0)
    )
    
    # Continuity zones
    st.subheader("🔗 Continuity Zones")
    st.write("""
    **Continuity zones define which rooms need matching materials.**
    For example, if your living room and dining room share an open space,
    they should have the same flooring installed at the same time.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Floor Continuity Zones**")
        
        # Add new floor zone
        if st.button("➕ Add Floor Zone"):
            new_zone = create_continuity_zone("floor", "", [], "")
            work_zones["floor_continuity_zones"].append(new_zone)
        
        # Display existing floor zones
        for i, zone in enumerate(work_zones.get("floor_continuity_zones", [])):
            with st.expander(f"Floor Zone {i+1}"):
                zone["primary_room"] = st.text_input(
                    "Primary Room", 
                    value=zone.get("primary_room", ""),
                    key=f"floor_zone_{i}_primary"
                )
                
                connected_rooms = st.text_input(
                    "Connected Rooms (comma-separated)",
                    value=", ".join(zone.get("connected_rooms", [])),
                    key=f"floor_zone_{i}_connected"
                )
                zone["connected_rooms"] = [room.strip() for room in connected_rooms.split(',') if room.strip()]
                
                zone["reason"] = st.text_input(
                    "Reason for Continuity",
                    value=zone.get("reason", ""),
                    key=f"floor_zone_{i}_reason"
                )
                
                if st.button("🗑️ Remove Zone", key=f"remove_floor_zone_{i}"):
                    work_zones["floor_continuity_zones"].pop(i)
                    st.rerun()
    
    with col2:
        st.write("**Paint Continuity Zones**")
        
        # Add new paint zone
        if st.button("➕ Add Paint Zone"):
            new_zone = create_continuity_zone("paint", "", [], "")
            work_zones["paint_continuity_zones"].append(new_zone)
        
        # Display existing paint zones
        for i, zone in enumerate(work_zones.get("paint_continuity_zones", [])):
            with st.expander(f"Paint Zone {i+1}"):
                zone["primary_room"] = st.text_input(
                    "Primary Room",
                    value=zone.get("primary_room", ""),
                    key=f"paint_zone_{i}_primary"
                )
                
                connected_rooms = st.text_input(
                    "Connected Rooms (comma-separated)",
                    value=", ".join(zone.get("connected_rooms", [])),
                    key=f"paint_zone_{i}_connected"
                )
                zone["connected_rooms"] = [room.strip() for room in connected_rooms.split(',') if room.strip()]
                
                zone["reason"] = st.text_input(
                    "Reason for Continuity",
                    value=zone.get("reason", ""),
                    key=f"paint_zone_{i}_reason"
                )
                
                if st.button("🗑️ Remove Zone", key=f"remove_paint_zone_{i}"):
                    work_zones["paint_continuity_zones"].pop(i)
                    st.rerun()

def project_standards_page():
    """Project Standards page"""
    st.header("🔧 Project-Wide Standards")
    
    standards = st.session_state.project_data["project_standards"]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏗️ Building Specifications")
        
        standards["standard_ceiling_height"] = st.number_input(
            "Standard Ceiling Height (ft)",
            min_value=7.0,
            max_value=20.0,
            value=float(standards.get("standard_ceiling_height", 8.0)),
            step=0.5
        )
        
        building_options = get_building_level_options()
        standards["building_level"] = st.selectbox(
            "Building Level",
            options=[opt[0] for opt in building_options],
            format_func=lambda x: next(opt[1] for opt in building_options if opt[0] == x),
            index=next((i for i, opt in enumerate(building_options) 
                      if opt[0] == standards.get("building_level", "ground")), 0)
        )
        
        access_options = get_access_condition_options()
        standards["access_conditions"] = st.selectbox(
            "Access Conditions",
            options=[opt[0] for opt in access_options],
            format_func=lambda x: next(opt[1] for opt in access_options if opt[0] == x),
            index=next((i for i, opt in enumerate(access_options) 
                      if opt[0] == standards.get("access_conditions", "normal")), 0)
        )
    
    with col2:
        st.subheader("🎨 Standard Materials")
        
        drywall_options = ["1/2\"", "5/8\"", "moisture-resistant", "match_existing"]
        standards["standard_drywall"] = st.selectbox(
            "Standard Drywall",
            options=drywall_options,
            index=drywall_options.index(standards.get("standard_drywall", "1/2\""))
        )
        
        flooring_options = ["hardwood", "laminate", "carpet", "tile", "lvp", "match_existing"]
        standards["flooring_default"] = st.selectbox(
            "Flooring Default",
            options=flooring_options,
            index=flooring_options.index(standards.get("flooring_default", "match_existing"))
        )
        
        baseboard_options = ["3.5\"", "5.25\"", "7.25\"", "none", "match_existing"]
        standards["standard_baseboard"] = st.selectbox(
            "Standard Baseboard",
            options=baseboard_options,
            index=baseboard_options.index(standards.get("standard_baseboard", "3.5\""))
        )
        
        standards["quarter_round"] = st.checkbox(
            "Include Quarter Round",
            value=standards.get("quarter_round", True)
        )
        
        paint_scope_options = ["walls_and_ceiling", "walls_only", "ceiling_only"]
        standards["paint_scope_default"] = st.selectbox(
            "Paint Scope Default",
            options=paint_scope_options,
            index=paint_scope_options.index(standards.get("paint_scope_default", "walls_and_ceiling"))
        )

def work_packages_page():
    """Work Packages page - Project level templates and standards"""
    st.header("📦 Work Package Templates & Standards")
    
    st.info("💡 Work packages are now configured per room in the Room Data Entry section. This page defines project-wide standards and templates.")
    
    work_packages = st.session_state.project_data["work_packages"]
    
    st.subheader("📋 Project-Wide Templates")
    st.write("Define standard work package templates that will be available for each room:")
    
    # Define available work package templates (for reference)
    template_info = {
        "full_room_restoration": "Complete water damage restoration with demo, dry, rebuild, and finish",
        "floor_replacement": "Complete floor replacement including removal, prep, installation, and finishing",
        "paint_refresh": "Complete paint system with prep, prime, and 2-coat application",
        "trim_restoration": "Trim removal, replacement, priming, and painting",
        "bathroom_restoration": "Bathroom-specific restoration with moisture-resistant materials",
        "kitchen_prep": "Kitchen preparation work for cabinet installation",
        "basement_finishing": "Basement finishing with moisture control and insulation",
        "minor_structural": "Minor structural repairs with code compliance"
    }
    
    st.subheader("📚 Available Work Package Templates")
    
    for template_id, description in template_info.items():
        with st.expander(f"📦 {template_id.replace('_', ' ').title()}"):
            st.write(f"**Description:** {description}")
            st.write("**Included Work:**")
            
            if template_id == "full_room_restoration":
                st.write("• Demo and removal of damaged materials")
                st.write("• Drying and moisture control")
                st.write("• Structural repairs as needed")
                st.write("• Insulation replacement")
                st.write("• Drywall installation and finishing")
                st.write("• Flooring installation")
                st.write("• Trim and baseboard installation")
                st.write("• Prime and paint system")
            
            elif template_id == "bathroom_restoration":
                st.write("• Moisture-resistant drywall")
                st.write("• Proper ventilation requirements")
                st.write("• Waterproofing behind fixtures")
                st.write("• Moisture-resistant flooring")
                st.write("• Proper trim and baseboard exclusions")
    
    st.subheader("🔧 Project Standards Integration")
    st.write("Work packages will automatically apply the project standards defined in the Project Standards section:")
    
    standards = st.session_state.project_data["project_standards"]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Current Project Standards:**")
        st.write(f"• Ceiling Height: {standards.get('standard_ceiling_height', 8)} ft")
        st.write(f"• Drywall: {standards.get('standard_drywall', '1/2\"')}")
        st.write(f"• Flooring: {standards.get('flooring_default', 'match_existing')}")
    
    with col2:
        st.write(f"• Baseboard: {standards.get('standard_baseboard', '3.5\"')}")
        st.write(f"• Quarter Round: {'Yes' if standards.get('quarter_round', True) else 'No'}")
        st.write(f"• Paint Scope: {standards.get('paint_scope_default', 'walls_and_ceiling')}")
    
    st.info("🏠 **To apply work packages to specific rooms, go to the Room Data Entry section.**")

def room_data_entry_page():
    """Room Data Entry page"""
    st.header("🏠 Room Data Entry")
    
    rooms = st.session_state.project_data["rooms"]
    
    # Room management
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.subheader("📋 Room Management")
    
    with col2:
        if st.button("➕ Add New Room"):
            rooms.append(create_empty_room())
            st.session_state.current_room_index = len(rooms) - 1
            st.rerun()
    
    with col3:
        if rooms and st.button("🗑️ Delete Current Room"):
            if len(rooms) > 0:
                rooms.pop(st.session_state.current_room_index)
                st.session_state.current_room_index = max(0, min(st.session_state.current_room_index, len(rooms) - 1))
                st.rerun()
    
    if not rooms:
        st.info("No rooms added yet. Click 'Add New Room' to start.")
        return
    
    # Room selector
    room_names = [f"Room {i+1}: {room.get('room_name', 'Unnamed')}" for i, room in enumerate(rooms)]
    selected_room_index = st.selectbox(
        "Select Room to Edit",
        options=range(len(rooms)),
        format_func=lambda i: room_names[i],
        index=st.session_state.current_room_index
    )
    st.session_state.current_room_index = selected_room_index
    
    current_room = rooms[selected_room_index]
    
    # Room details form
    st.subheader(f"📐 Room #{selected_room_index + 1} Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        current_room["room_name"] = st.text_input(
            "Room Name",
            value=current_room.get("room_name", ""),
            key=f"room_name_{selected_room_index}",
            help="Enter a descriptive name like 'Master Bathroom' or 'Living Room'"
        )
        
        # Zone Assignment with explanation
        st.write("**Zone Assignment** 🔗")
        with st.expander("ℹ️ What is Zone Assignment?"):
            st.write("""
            **Zone Assignment groups connected rooms for work continuity:**
            
            **🏠 Zone A**: Main living areas (Living Room, Kitchen, Dining)
            - Same flooring installed together for seamless appearance
            - Coordinated paint colors and timing
            
            **🛏️ Zone B**: Master suite (Master Bedroom, Master Bath)
            - Private area with consistent materials
            - Work scheduled together for minimal disruption
            
            **👥 Zone C**: Guest areas (Guest bedrooms, shared bathrooms)
            - Secondary spaces with coordinated finishes
            
            **🔧 Independent**: Standalone spaces (Basement, Garage, Utility)
            - Work independently without affecting other areas
            
            **💡 Why use zones?**
            • Ensures material matching across connected spaces
            • Optimizes work scheduling and efficiency  
            • Supports insurance claims for continuity requirements
            • Prevents color/pattern mismatches in open floor plans
            """)
        
        zone_options = ["A", "B", "C", "Independent"]
        current_zone = current_room.get("zone_assignment", "A")
        zone_index = 0  # Default to first option
        if current_zone in zone_options:
            zone_index = zone_options.index(current_zone)
        
        current_room["zone_assignment"] = st.selectbox(
            "Select Zone",
            options=zone_options,
            index=zone_index,
            key=f"zone_{selected_room_index}",
            help="Group this room with others that need coordinated work"
        )
    
    # Room Input Method selection with enhanced options
    with col2:
        input_methods = get_room_input_methods()
        current_input_method = current_room.get("input_method", "simple_rectangular")
        input_method_index = 0  # Default to first option
        for i, method in enumerate(input_methods):
            if method[0] == current_input_method:
                input_method_index = i
                break
        
        current_room["input_method"] = st.selectbox(
            "Room Input Method",
            options=[method[0] for method in input_methods],
            format_func=lambda x: next(method[1] for method in input_methods if method[0] == x),
            index=input_method_index,
            key=f"input_method_{selected_room_index}"
        )
        
        # Show method descriptions
        method_descriptions = {
            "ai_image_analysis": "🤖 Best for floor plans - AI reads dimensions automatically",
            "simple_rectangular": "📐 For basic rectangular rooms - Enter length × width",
            "complex_manual": "🔧 For L-shaped, T-shaped, or irregular rooms - Define multiple walls",
            "standard_template": "📋 Use pre-defined room templates"
        }
        
        current_method = current_room["input_method"]
        if current_method in method_descriptions:
            st.info(method_descriptions[current_method])
    
    # AI Analysis Section
    if current_room["input_method"] == "ai_image_analysis":
        st.subheader("🤖 AI Image Analysis")
        
        if st.session_state.ai_analyzer is None:
            st.error("⚠️ OpenAI API key not configured. Please add your API key to secrets.toml")
        else:
            col1, col2 = st.columns(2)
            
            with col1:
                uploaded_image = st.file_uploader(
                    "Upload Floor Plan/Sketch",
                    type=['png', 'jpg', 'jpeg'],
                    key=f"image_upload_{selected_room_index}"
                )
                
                room_type_hint = st.selectbox(
                    "Room Type Hint",
                    options=["", "bathroom", "kitchen", "bedroom", "living", "office", "other"],
                    key=f"room_type_{selected_room_index}"
                )
            
            with col2:
                if uploaded_image is not None:
                    st.image(uploaded_image, caption="Uploaded Image", use_container_width=True)
                    
                    if st.button("🔍 Analyze Image", key=f"analyze_{selected_room_index}"):
                        with st.spinner("Analyzing image..."):
                            result = st.session_state.ai_analyzer.analyze_construction_image(
                                uploaded_image, 
                                current_room.get("room_name", ""),
                                room_type_hint
                            )
                            
                            if "error" in result:
                                st.error(f"Analysis failed: {result['error']}")
                            else:
                                current_room["ai_analysis"]["extracted_results"] = result
                                current_room["ai_analysis"]["confidence_level"] = result.get("confidence_level", "medium")
                                st.success("✅ Analysis complete!")
                                
                                # Auto-populate dimensions if available
                                extracted_dims = result.get("extracted_dimensions", {})
                                room_geo = result.get("room_geometry", {})
                                
                                # Set ceiling height
                                ceiling_height = (extracted_dims.get("ceiling_height_ft") or 
                                                room_geo.get("ceiling_height_ft") or 8.0)
                                current_room["dimensions"]["height"] = max(ceiling_height, 7.0)
                                
                                # Get floor area from multiple possible sources
                                floor_area = (room_geo.get("total_floor_area_sf") or 
                                            extracted_dims.get("floor_area_sf") or 
                                            extracted_dims.get("room_area_sf") or 0)
                                
                                # Get length/width if available
                                length = (extracted_dims.get("room_length_ft") or 
                                        extracted_dims.get("length_ft") or 0)
                                width = (extracted_dims.get("room_width_ft") or 
                                       extracted_dims.get("width_ft") or 0)
                                
                                # If we have wall segments, use complex manual method
                                if "wall_segments" in result and result["wall_segments"]:
                                    # Switch to complex manual for better accuracy
                                    current_room["input_method"] = "complex_manual"
                                    
                                    # Initialize complex geometry
                                    current_room["complex_geometry"] = {
                                        "wall_segments": [],
                                        "room_shape": result.get("room_identification", {}).get("room_shape", "irregular"),
                                        "calculation_method": "ai_extracted"
                                    }
                                    
                                    # Convert AI wall segments to our format
                                    for i, ai_wall in enumerate(result["wall_segments"]):
                                        wall_segment = {
                                            "wall_id": ai_wall.get("wall_id", f"wall_{i+1}"),
                                            "length_ft": ai_wall.get("length_ft", 0),
                                            "orientation": ai_wall.get("orientation", "unknown"),
                                            "doors": [],
                                            "windows": [],
                                            "notes": f"AI extracted: {ai_wall.get('dimension_label', '')}"
                                        }
                                        
                                        # Convert doors with safe type checking
                                        for ai_door in ai_wall.get("doors", []):
                                            if isinstance(ai_door, dict):
                                                door = {
                                                    "width_ft": ai_door.get("width_ft", 3.0),
                                                    "type": ai_door.get("door_type", "interior"),
                                                    "leads_to": ai_door.get("leads_to", "unknown")
                                                }
                                                wall_segment["doors"].append(door)
                                            else:
                                                # Handle string or other types
                                                door = {
                                                    "width_ft": 3.0,
                                                    "type": "interior",
                                                    "leads_to": str(ai_door) if ai_door else "unknown"
                                                }
                                                wall_segment["doors"].append(door)
                                        
                                        # Convert windows with safe type checking
                                        for ai_window in ai_wall.get("windows", []):
                                            if isinstance(ai_window, dict):
                                                window = {
                                                    "width_ft": ai_window.get("width_ft", 3.0),
                                                    "height_ft": ai_window.get("height_ft", 4.0)
                                                }
                                                wall_segment["windows"].append(window)
                                            else:
                                                # Handle string or other types
                                                window = {
                                                    "width_ft": 3.0,
                                                    "height_ft": 4.0
                                                }
                                                wall_segment["windows"].append(window)
                                        
                                        current_room["complex_geometry"]["wall_segments"].append(wall_segment)
                                    
                                    # Use extracted area
                                    if floor_area > 0:
                                        current_room["dimensions"]["floor_area_manual"] = floor_area
                                        current_room["dimensions"]["floor_area"] = floor_area
                                    
                                    st.success("✅ Complex room detected! Switched to Complex Manual mode with AI-extracted wall segments.")
                                
                                else:
                                    # Simple room - populate basic measurements
                                    if length > 0 and width > 0:
                                        # Direct length/width available
                                        current_room["dimensions"]["length"] = length
                                        current_room["dimensions"]["width"] = width
                                        current_room["dimensions"]["floor_area"] = length * width
                                    elif floor_area > 0:
                                        # Only area available - estimate square dimensions
                                        equivalent_side = (floor_area ** 0.5)
                                        current_room["dimensions"]["length"] = equivalent_side
                                        current_room["dimensions"]["width"] = equivalent_side
                                        current_room["dimensions"]["floor_area"] = floor_area
                                    
                                    # Calculate other areas
                                    if current_room["dimensions"].get("floor_area", 0) > 0:
                                        length = current_room["dimensions"]["length"]
                                        width = current_room["dimensions"]["width"]
                                        height = current_room["dimensions"]["height"]
                                        current_room["dimensions"]["wall_area"] = 2 * (length + width) * height
                                        current_room["dimensions"]["ceiling_area"] = floor_area
                                    
                                    # Auto-populate openings from summary
                                    if "openings_summary" in result:
                                        openings_summary = result["openings_summary"]
                                        current_room["openings"]["interior_doors"] = openings_summary.get("total_interior_doors", 0)
                                        current_room["openings"]["exterior_doors"] = openings_summary.get("total_exterior_doors", 0)
                                        current_room["openings"]["windows"] = openings_summary.get("total_windows", 0)
                                    
                                    # Add note about complex shape
                                    room_shape = result.get("room_identification", {}).get("room_shape", "")
                                    if room_shape and room_shape != "rectangular":
                                        current_room["ai_analysis"]["shape_notes"] = room_shape
                                
                                st.rerun()
            
            # Display extracted results
            if current_room["ai_analysis"].get("extracted_results"):
                st.subheader("📊 AI Extracted Results")
                results = current_room["ai_analysis"]["extracted_results"]
                
                # Debug: Show raw results structure
                with st.expander("🔍 Debug: Raw AI Results"):
                    st.json(results)
                
                # Extract data from multiple possible locations
                extracted_dims = results.get("extracted_dimensions", {})
                room_geo = results.get("room_geometry", {})
                room_id = results.get("room_identification", {})
                openings_summary = results.get("openings_summary", {})
                
                # Combine all available dimensional data
                all_data = {**extracted_dims, **room_geo, **room_id}
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**📐 Dimensional Analysis:**")
                    
                    # Show room shape information
                    room_shape = all_data.get("room_shape", "rectangular")
                    detected_room_name = all_data.get("detected_room_name", "Unknown")
                    
                    if room_shape != "rectangular":
                        st.warning(f"⚠️ **Complex Shape**: {room_shape.replace('_', ' ').title()}")
                    
                    # Show all available dimensional data
                    floor_area = (all_data.get("total_floor_area_sf") or 
                                all_data.get("floor_area_sf") or 
                                all_data.get("room_area_sf") or "N/A")
                    
                    perimeter = (all_data.get("perimeter_lf") or 
                               all_data.get("total_perimeter_lf") or "N/A")
                    
                    height = (all_data.get("ceiling_height_ft") or 
                            all_data.get("height_ft") or "N/A")
                    
                    length = (all_data.get("room_length_ft") or 
                            all_data.get("length_ft") or "N/A")
                    
                    width = (all_data.get("room_width_ft") or 
                           all_data.get("width_ft") or "N/A")
                    
                    st.write(f"• **Room Type**: {detected_room_name}")
                    st.write(f"• **Floor Area**: {floor_area} SF")
                    st.write(f"• **Perimeter**: {perimeter} LF")
                    st.write(f"• **Height**: {height} ft")
                    
                    if length != "N/A" and width != "N/A":
                        st.write(f"• **Length**: {length} ft")
                        st.write(f"• **Width**: {width} ft")
                    
                    # Show calculation method
                    dimension_source = all_data.get('dimension_source', 'ai_analysis')
                    st.info(f"📐 **Source**: {dimension_source.replace('_', ' ').title()}")
                
                with col2:
                    st.write("**🚪 Openings & Features:**")
                    
                    # Show wall segments summary if available
                    if "wall_segments" in results and results["wall_segments"]:
                        wall_segments = results["wall_segments"]
                        st.write(f"• **Total Walls**: {len(wall_segments)}")
                        
                        total_doors = sum(len(wall.get("doors", [])) for wall in wall_segments)
                        total_windows = sum(len(wall.get("windows", [])) for wall in wall_segments)
                        st.write(f"• **Total Doors**: {total_doors}")
                        st.write(f"• **Total Windows**: {total_windows}")
                        
                        # Show first few walls as preview
                        st.write("**Wall Preview:**")
                        for i, wall in enumerate(wall_segments[:3]):
                            orientation = wall.get("orientation", "unknown")
                            wall_length = wall.get("length_ft", 0)
                            st.write(f"  • Wall {i+1}: {orientation.title()} - {wall_length:.1f} ft")
                        
                        if len(wall_segments) > 3:
                            st.write(f"  • ... and {len(wall_segments) - 3} more walls")
                    
                    else:
                        # Use openings summary with enhanced display
                        total_doors = openings_summary.get("total_doors", 0)
                        interior_doors = openings_summary.get("total_interior_doors", 0)
                        exterior_doors = openings_summary.get("total_exterior_doors", 0)
                        windows = openings_summary.get("total_windows", 0)
                        open_areas = openings_summary.get("total_open_areas", 0)
                        
                        # Display door information
                        if total_doors > 0:
                            st.write(f"• **Total Doors**: {total_doors}")
                            if interior_doors > 0:
                                st.write(f"  - Interior Doors: {interior_doors}")
                            if exterior_doors > 0:
                                st.write(f"  - Exterior Doors: {exterior_doors}")
                        else:
                            st.write(f"• **Doors**: None")
                        
                        # Display window information
                        if windows > 0:
                            st.write(f"• **Windows**: {windows}")
                            window_area = openings_summary.get("window_area_total_sf", 0)
                            if window_area > 0:
                                st.write(f"  - Total Window Area: {window_area:.1f} SF")
                        else:
                            st.write(f"• **Windows**: None")
                        
                        # Display open areas information
                        if open_areas > 0:
                            st.write(f"• **Open Areas**: {open_areas}")
                            open_width = openings_summary.get("open_area_width_total_ft", 0)
                            if open_width > 0:
                                st.write(f"  - Total Open Width: {open_width:.1f} ft")
                        else:
                            st.write(f"• **Open Areas**: None")
                        
                        # Display door dimensions if available
                        door_width_total = openings_summary.get("door_width_total_ft", 0)
                        if door_width_total > 0:
                            st.write(f"• **Total Door Width**: {door_width_total:.1f} ft")
                        
                        # Show material impact summary
                        if door_width_total > 0 or open_areas > 0:
                            st.write("**📏 Material Impact:**")
                            baseboard_deduction = door_width_total + openings_summary.get("open_area_width_total_ft", 0)
                            if baseboard_deduction > 0:
                                st.write(f"  - Baseboard Reduction: {baseboard_deduction:.1f} ft")
                            
                            open_width_only = openings_summary.get("open_area_width_total_ft", 0)
                            if open_width_only > 0:
                                st.write(f"  - Crown Molding Reduction: {open_width_only:.1f} ft")
                
                # Show detailed analysis in expandable sections
                if "wall_segments" in results and results["wall_segments"]:
                    with st.expander("🔧 Detailed Wall Analysis"):
                        for i, wall in enumerate(results["wall_segments"]):
                            st.write(f"**Wall {i+1} ({wall.get('orientation', 'unknown').title()}):**")
                            st.write(f"• Length: {wall.get('length_ft', 0):.1f} ft")
                            st.write(f"• Label: {wall.get('dimension_label', 'N/A')}")
                            
                            # Show doors on this wall
                            doors = wall.get("doors", [])
                            if doors:
                                st.write("• Doors:")
                                for door in doors:
                                    if isinstance(door, dict):
                                        door_width = door.get('width_ft', 0)
                                        door_height = door.get('height_ft', 6.67)
                                        size = f"{door_width:.1f}' × {door_height:.1f}'"
                                        leads_to = door.get("leads_to", "unknown")
                                        st.write(f"  - {size} → {leads_to}")
                                    else:
                                        # Handle non-dict door entries
                                        st.write(f"  - Door: {str(door)}")
                            
                            # Show windows on this wall
                            windows = wall.get("windows", [])
                            if windows:
                                st.write("• Windows:")
                                for window in windows:
                                    if isinstance(window, dict):
                                        window_width = window.get('width_ft', 0)
                                        window_height = window.get('height_ft', 0)
                                        size = f"{window_width:.1f}' × {window_height:.1f}'"
                                        st.write(f"  - {size}")
                                    else:
                                        # Handle non-dict window entries
                                        st.write(f"  - Window: {str(window)}")
                            
                            st.write("---")
                
                # Show confidence level and analysis notes
                confidence = results.get("confidence_level", "medium")
                if confidence == "high":
                    st.success(f"🎯 **Analysis Confidence: {confidence.title()}**")
                elif confidence == "medium":
                    st.warning(f"⚠️ **Analysis Confidence: {confidence.title()}**")
                else:
                    st.error(f"❌ **Analysis Confidence: {confidence.title()} - Manual verification recommended**")
                
                analysis_notes = results.get("analysis_notes", "")
                if analysis_notes:
                    st.info(f"📝 **Analysis Notes**: {analysis_notes}")
                
                # Show what will be applied
                st.subheader("📋 Data to be Applied")
                apply_summary = []
                
                if floor_area != "N/A":
                    apply_summary.append(f"Floor Area: {floor_area} SF")
                if height != "N/A":
                    apply_summary.append(f"Ceiling Height: {height} ft")
                if length != "N/A" and width != "N/A":
                    apply_summary.append(f"Dimensions: {length} × {width} ft")
                
                if openings_summary:
                    doors_total = openings_summary.get("total_interior_doors", 0) + openings_summary.get("total_exterior_doors", 0)
                    if doors_total > 0:
                        apply_summary.append(f"Doors: {doors_total}")
                    if openings_summary.get("total_windows", 0) > 0:
                        apply_summary.append(f"Windows: {openings_summary['total_windows']}")
                
                if apply_summary:
                    st.info("**Will apply:** " + " | ".join(apply_summary))
                else:
                    st.warning("⚠️ **No dimensional data found to apply**")
                
                # Confirmation buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Confirm and Apply", key=f"confirm_{selected_room_index}"):
                        current_room["ai_analysis"]["user_confirmed"] = True
                        
                        # Force immediate application of measurements
                        results = current_room["ai_analysis"]["extracted_results"]
                        
                        # Apply dimensions immediately using combined data
                        all_data = {**extracted_dims, **room_geo, **room_id}
                        
                        # Set ceiling height
                        ceiling_height = (all_data.get("ceiling_height_ft") or 
                                        all_data.get("height_ft") or 8.0)
                        current_room["dimensions"]["height"] = max(float(ceiling_height), 7.0)
                        
                        # Get floor area from multiple possible sources
                        floor_area = (all_data.get("total_floor_area_sf") or 
                                    all_data.get("floor_area_sf") or 
                                    all_data.get("room_area_sf") or 0)
                        
                        # Get length/width if available
                        length = (all_data.get("room_length_ft") or 
                                all_data.get("length_ft") or 0)
                        width = (all_data.get("room_width_ft") or 
                               all_data.get("width_ft") or 0)
                        
                        if length and width and float(length) > 0 and float(width) > 0:
                            # Direct length/width available
                            current_room["dimensions"]["length"] = float(length)
                            current_room["dimensions"]["width"] = float(width)
                            current_room["dimensions"]["floor_area"] = float(length) * float(width)
                        elif floor_area and float(floor_area) > 0:
                            # Only area available - estimate square dimensions
                            equivalent_side = (float(floor_area) ** 0.5)
                            current_room["dimensions"]["length"] = equivalent_side
                            current_room["dimensions"]["width"] = equivalent_side
                            current_room["dimensions"]["floor_area"] = float(floor_area)
                        
                        # Calculate other areas
                        if current_room["dimensions"].get("floor_area", 0) > 0:
                            length = current_room["dimensions"]["length"]
                            width = current_room["dimensions"]["width"]
                            height = current_room["dimensions"]["height"]
                            current_room["dimensions"]["wall_area"] = 2 * (length + width) * height
                            current_room["dimensions"]["ceiling_area"] = current_room["dimensions"]["floor_area"]
                        
                        # Apply openings
                        if openings_summary:
                            current_room["openings"]["interior_doors"] = openings_summary.get("total_interior_doors", 0)
                            current_room["openings"]["exterior_doors"] = openings_summary.get("total_exterior_doors", 0)
                            current_room["openings"]["windows"] = openings_summary.get("total_windows", 0)
                        
                        st.success("✅ AI results confirmed and applied!")
                        st.rerun()
                
                with col2:
                    if st.button("✏️ Edit and Override", key=f"override_{selected_room_index}"):
                        current_room["ai_analysis"]["user_confirmed"] = False
                        st.info("💡 You can now manually edit the measurements below.")
    
    # Auto-populate room measurements from AI analysis if confirmed
    if (current_room["input_method"] == "ai_image_analysis" and 
        current_room["ai_analysis"].get("user_confirmed") and 
        current_room["ai_analysis"].get("extracted_results")):
        
        results = current_room["ai_analysis"]["extracted_results"]
        
        # Auto-populate openings from AI analysis
        if "openings_summary" in results:
            openings = results["openings_summary"]
            current_room["openings"]["interior_doors"] = openings.get("total_interior_doors", 0)
            current_room["openings"]["exterior_doors"] = openings.get("total_exterior_doors", 0)
            current_room["openings"]["windows"] = openings.get("total_windows", 0)
    
    # Complex Manual Input Method for irregular shapes
    elif current_room["input_method"] == "complex_manual":
        st.subheader("🔧 Complex Room Shape Definition")
        
        st.info("""
        **For L-shaped, T-shaped, or irregular rooms:**
        Define each wall segment with its length and any openings (doors/windows).
        The system will calculate total area and perimeter automatically.
        """)
        
        # Initialize complex geometry if not exists
        if "complex_geometry" not in current_room:
            current_room["complex_geometry"] = {
                "wall_segments": [],
                "room_shape": "irregular",
                "calculation_method": "wall_segments"
            }
        
        complex_geo = current_room["complex_geometry"]
        
        # Wall segments input
        st.write("**Define Wall Segments:**")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("Add each wall segment of your room:")
        with col2:
            if st.button("➕ Add Wall Segment", key=f"add_wall_{selected_room_index}"):
                complex_geo["wall_segments"].append({
                    "wall_id": f"wall_{len(complex_geo['wall_segments']) + 1}",
                    "length_ft": 0.0,
                    "orientation": "north",  # north, south, east, west
                    "doors": [],
                    "windows": [],
                    "notes": ""
                })
        
        # Display wall segments
        wall_segments = complex_geo.get("wall_segments", [])
        
        if not wall_segments:
            st.warning("⚠️ No wall segments defined. Click 'Add Wall Segment' to start.")
        else:
            total_perimeter = 0
            for i, wall in enumerate(wall_segments):
                with st.expander(f"🧱 Wall {i+1}: {wall.get('wall_id', f'wall_{i+1}')}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        wall["length_ft"] = st.number_input(
                            "Wall Length (ft)",
                            min_value=0.0,
                            value=float(wall.get("length_ft", 0)),
                            step=0.1,
                            key=f"wall_{i}_length_{selected_room_index}"
                        )
                        
                        orientations = ["north", "south", "east", "west", "northeast", "northwest", "southeast", "southwest"]
                        current_orientation = wall.get("orientation", "north")
                        orientation_index = 0
                        if current_orientation in orientations:
                            orientation_index = orientations.index(current_orientation)
                        
                        wall["orientation"] = st.selectbox(
                            "Wall Orientation",
                            options=orientations,
                            index=orientation_index,
                            key=f"wall_{i}_orientation_{selected_room_index}"
                        )
                    
                    with col2:
                        # Doors on this wall
                        st.write("**Doors on this wall:**")
                        door_count = st.number_input(
                            "Number of Doors",
                            min_value=0,
                            max_value=5,
                            value=len(wall.get("doors", [])),
                            key=f"wall_{i}_doors_{selected_room_index}"
                        )
                        
                        # Adjust doors list
                        current_doors = wall.get("doors", [])
                        if len(current_doors) != door_count:
                            wall["doors"] = [{"width_ft": 3.0, "type": "interior"} for _ in range(door_count)]
                        
                        # Window count
                        window_count = st.number_input(
                            "Number of Windows",
                            min_value=0,
                            max_value=10,
                            value=len(wall.get("windows", [])),
                            key=f"wall_{i}_windows_{selected_room_index}"
                        )
                        
                        # Adjust windows list
                        current_windows = wall.get("windows", [])
                        if len(current_windows) != window_count:
                            wall["windows"] = [{"width_ft": 3.0, "height_ft": 4.0} for _ in range(window_count)]
                    
                    with col3:
                        wall["notes"] = st.text_area(
                            "Wall Notes",
                            value=wall.get("notes", ""),
                            height=80,
                            key=f"wall_{i}_notes_{selected_room_index}",
                            help="Special features, materials, or conditions"
                        )
                        
                        if st.button(f"🗑️ Remove Wall {i+1}", key=f"remove_wall_{i}_{selected_room_index}"):
                            wall_segments.pop(i)
                            st.rerun()
                    
                    # Show wall details with safe type checking
                    if wall["length_ft"] > 0:
                        door_deduction = 0
                        window_deduction = 0
                        
                        # Calculate door deductions safely
                        for door in wall.get("doors", []):
                            if isinstance(door, dict):
                                door_deduction += door.get("width_ft", 3.0) * 8
                            else:
                                door_deduction += 3.0 * 8  # Default door size
                        
                        # Calculate window deductions safely
                        for window in wall.get("windows", []):
                            if isinstance(window, dict):
                                window_deduction += window.get("width_ft", 3.0) * window.get("height_ft", 4.0)
                            else:
                                window_deduction += 3.0 * 4.0  # Default window size
                        
                        net_wall_area = max(0, wall["length_ft"] * current_room["dimensions"].get("height", 8.0) - door_deduction - window_deduction)
                        
                        st.info(f"📊 **Wall {i+1} Summary**: {wall['length_ft']:.1f} LF | Net Area: {net_wall_area:.1f} SF")
                        total_perimeter += wall["length_ft"]
            
            # Calculate total room metrics from wall segments
            if total_perimeter > 0:
                # Estimate floor area (this is approximate for irregular shapes)
                # For better accuracy, would need actual coordinates
                estimated_area = (total_perimeter / 4) ** 2  # Very rough estimate
                
                st.success(f"📐 **Room Totals**: Perimeter: {total_perimeter:.1f} LF | Estimated Area: {estimated_area:.1f} SF")
                
                # Update room dimensions with calculated values
                current_room["dimensions"]["perimeter_actual"] = total_perimeter
                current_room["dimensions"]["floor_area_estimated"] = estimated_area
                
                # For UI compatibility, set equivalent rectangular dimensions
                equivalent_side = (estimated_area ** 0.5)
                current_room["dimensions"]["length"] = equivalent_side
                current_room["dimensions"]["width"] = equivalent_side
                current_room["dimensions"]["floor_area"] = estimated_area
        
        # Area override for accurate input
        st.subheader("🎯 Accurate Area Input")
        st.write("If you know the exact floor area (from blueprints), enter it here:")
        
        manual_area = st.number_input(
            "Actual Floor Area (SF)",
            min_value=0.0,
            value=float(current_room["dimensions"].get("floor_area_manual", 0)),
            step=0.1,
            key=f"manual_area_{selected_room_index}",
            help="Override estimated area with known accurate measurement"
        )
        
        if manual_area > 0:
            current_room["dimensions"]["floor_area_manual"] = manual_area
            current_room["dimensions"]["floor_area"] = manual_area
            st.success(f"✅ Using manual area: {manual_area:.1f} SF")
    
    # Standard Template Method
    elif current_room["input_method"] == "standard_template":
        st.subheader("📋 Standard Room Templates")
        
        room_templates = {
            "small_bathroom": {"length": 5.0, "width": 8.0, "height": 8.0, "doors": 1, "windows": 1},
            "master_bathroom": {"length": 10.0, "width": 12.0, "height": 9.0, "doors": 1, "windows": 1},
            "kitchen": {"length": 10.0, "width": 14.0, "height": 9.0, "doors": 2, "windows": 2},
            "living_room": {"length": 14.0, "width": 20.0, "height": 9.0, "doors": 2, "windows": 3},
            "bedroom": {"length": 10.0, "width": 12.0, "height": 8.0, "doors": 1, "windows": 2},
            "master_bedroom": {"length": 14.0, "width": 16.0, "height": 9.0, "doors": 2, "windows": 2}
        }
        
        template_names = list(room_templates.keys())
        template_labels = [name.replace("_", " ").title() for name in template_names]
        
        selected_template = st.selectbox(
            "Choose Room Template",
            options=template_names,
            format_func=lambda x: x.replace("_", " ").title(),
            key=f"template_{selected_room_index}"
        )
        
        if st.button("📋 Apply Template", key=f"apply_template_{selected_room_index}"):
            template = room_templates[selected_template]
            current_room["dimensions"]["length"] = template["length"]
            current_room["dimensions"]["width"] = template["width"]
            current_room["dimensions"]["height"] = template["height"]
            current_room["openings"]["interior_doors"] = template["doors"]
            current_room["openings"]["windows"] = template["windows"]
            
            # Set room name if empty
            if not current_room.get("room_name"):
                current_room["room_name"] = selected_template.replace("_", " ").title()
            
            st.success(f"✅ Applied {selected_template.replace('_', ' ').title()} template!")
            st.rerun()
        
        # Show template preview
        if selected_template:
            template = room_templates[selected_template]
            st.info(f"""
            **{selected_template.replace('_', ' ').title()} Template:**
            • Dimensions: {template['length']}' × {template['width']}' × {template['height']}'
            • Floor Area: {template['length'] * template['width']:.1f} SF
            • Doors: {template['doors']} | Windows: {template['windows']}
            """)
    
    # Manual Measurements Section - Hide completely for AI confirmed cases
    show_manual_measurements = (
        current_room["input_method"] in ["simple_rectangular", "standard_template"] or
        (current_room["input_method"] == "ai_image_analysis" and 
         not current_room["ai_analysis"].get("extracted_results") and
         not current_room["ai_analysis"].get("user_confirmed"))
    )
    
    if show_manual_measurements:
        st.subheader("📏 Room Measurements")
        
        # Show AI override info if AI was used but not confirmed
        if (current_room["input_method"] == "ai_image_analysis" and 
            not current_room["ai_analysis"].get("extracted_results")):
            st.info("💡 Upload an image above for AI analysis, or enter measurements manually.")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Ensure length has a valid default value
            current_length = current_room["dimensions"].get("length", 0.0)
            
            current_room["dimensions"]["length"] = st.number_input(
                "Length (ft)",
                min_value=0.0,
                max_value=100.0,
                value=float(current_length),
                step=0.1,
                key=f"length_{selected_room_index}",
                help="Enter 0 if unknown, or use AI image analysis"
            )
        
        with col2:
            # Ensure width has a valid default value
            current_width = current_room["dimensions"].get("width", 0.0)
            
            current_room["dimensions"]["width"] = st.number_input(
                "Width (ft)",
                min_value=0.0,
                max_value=100.0,
                value=float(current_width),
                step=0.1,
                key=f"width_{selected_room_index}",
                help="Enter 0 if unknown, or use AI image analysis"
            )
        
        with col3:
            # Ensure height has a valid default value
            current_height = current_room["dimensions"].get("height", 8.0)
            if current_height < 7.0:
                current_height = 8.0
                current_room["dimensions"]["height"] = current_height
                
            current_room["dimensions"]["height"] = st.number_input(
                "Height (ft)",
                min_value=7.0,
                max_value=20.0,
                value=float(current_height),
                step=0.1,
                key=f"height_{selected_room_index}"
            )
        
        # Get dimensions from current room with safe defaults
        length = current_room["dimensions"].get("length", 0.0)
        width = current_room["dimensions"].get("width", 0.0)
        height = max(current_room["dimensions"].get("height", 8.0), 7.0)  # Ensure minimum height
        
        # Calculate areas automatically if dimensions are valid
        if length > 0 and width > 0:
            current_room["dimensions"]["floor_area"] = length * width
            current_room["dimensions"]["wall_area"] = 2 * (length + width) * height
            current_room["dimensions"]["ceiling_area"] = length * width
        
        # Show calculated areas in real-time (only if dimensions are valid)
        if length > 0 and width > 0 and height >= 7.0:
            floor_area = length * width
            perimeter = 2 * (length + width)
            wall_area = perimeter * height
            st.info(f"📐 **Calculated Areas:** Floor: {floor_area:.1f} SF | Perimeter: {perimeter:.1f} LF | Wall Area: {wall_area:.1f} SF")
        elif length > 0 or width > 0:
            st.warning("⚠️ **Incomplete measurements** - Enter both length and width to see calculated areas")
    
    # AI Confirmed measurements display - Show this for confirmed AI analysis
        elif (current_room["input_method"] == "ai_image_analysis" and current_room["ai_analysis"].get("user_confirmed")):
        
            st.subheader("🤖 AI-Extracted Measurements (Applied)")
            
            # Get AI analysis results to check room shape
            ai_results = current_room["ai_analysis"].get("extracted_results", {})
            room_shape = ai_results.get("room_identification", {}).get("room_shape", "rectangular")
            
            # Display the confirmed measurements based on room shape
            length = current_room["dimensions"].get("length", 0.0)
            width = current_room["dimensions"].get("width", 0.0) 
            height = current_room["dimensions"].get("height", 8.0)
            floor_area = current_room["dimensions"].get("floor_area", 0.0)
            
            # Only show Length/Width for rectangular rooms
            if room_shape == "rectangular" and length > 0 and width > 0:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Length", f"{length:.1f} ft")
                with col2:
                    st.metric("Width", f"{width:.1f} ft") 
                with col3:
                    st.metric("Height", f"{height:.1f} ft")
                
                # Show calculated areas for rectangular rooms
                if floor_area > 0:
                    perimeter = 2 * (length + width)
                    wall_area = perimeter * height
                    st.success(f"✅ **AI Measurements Applied:** Floor: {floor_area:.1f} SF | Perimeter: {perimeter:.1f} LF | Wall Area: {wall_area:.1f} SF")
            
            else:
                # For non-rectangular rooms, only show area-based measurements
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Height", f"{height:.1f} ft")
                    if floor_area > 0:
                        st.metric("Floor Area", f"{floor_area:.1f} SF")
                
                with col2:
                    # Get additional AI-extracted measurements
                    extracted_dims = ai_results.get("extracted_dimensions", {})
                    wall_area = extracted_dims.get("wall_area_sf", 0)
                    perimeter = extracted_dims.get("perimeter_lf", 0)
                    ceiling_area = extracted_dims.get("ceiling_area_sf", 0)
                    
                    if wall_area > 0:
                        st.metric("Wall Area", f"{wall_area:.1f} SF")
                    if perimeter > 0:
                        st.metric("Perimeter", f"{perimeter:.1f} LF")
                
                # Show room shape warning and measurements summary
                shape_display = room_shape.replace("_", "-").title()
                st.warning(f"⚠️ **{shape_display} Room** - Length/Width not applicable for complex shapes")
                
                if floor_area > 0:
                    measurements_summary = [f"Floor: {floor_area:.1f} SF"]
                    if wall_area > 0:
                        measurements_summary.append(f"Wall: {wall_area:.1f} SF")
                    if perimeter > 0:
                        measurements_summary.append(f"Perimeter: {perimeter:.1f} LF")
                    
                    st.success(f"✅ **AI Measurements Applied:** {' | '.join(measurements_summary)}")
                else:
                    st.info("📐 **AI Analysis Applied** - Complex room geometry detected")
            
            # Option to edit/override
            if st.button("✏️ Edit Measurements", key=f"edit_measurements_{selected_room_index}"):
                current_room["ai_analysis"]["user_confirmed"] = False
                st.info("💡 You can now edit measurements manually.")
                st.rerun()
    
    # Openings section (for non-AI confirmed methods)
    if (current_room["input_method"] in ["simple_rectangular", "standard_template"] and 
        not (current_room["ai_analysis"].get("user_confirmed") and current_room["ai_analysis"].get("extracted_results"))):
        
        st.subheader("🚪 Openings")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            current_room["openings"]["interior_doors"] = st.number_input(
                "Interior Doors",
                min_value=0,
                value=current_room["openings"].get("interior_doors", 1),
                key=f"int_doors_{selected_room_index}"
            )
        
        with col2:
            current_room["openings"]["exterior_doors"] = st.number_input(
                "Exterior Doors",
                min_value=0,
                value=current_room["openings"].get("exterior_doors", 0),
                key=f"ext_doors_{selected_room_index}"
            )
        
        with col3:
            current_room["openings"]["windows"] = st.number_input(
                "Windows",
                min_value=0,
                value=current_room["openings"].get("windows", 1),
                key=f"windows_{selected_room_index}"
            )
        
        # Show opening impact on calculations (only for simple rectangular)
        if (current_room["input_method"] == "simple_rectangular" and 
            not (current_room["ai_analysis"].get("user_confirmed") and current_room["ai_analysis"].get("extracted_results"))):
            
            length = current_room["dimensions"].get("length", 0.0)
            width = current_room["dimensions"].get("width", 0.0)
            height = max(current_room["dimensions"].get("height", 8.0), 7.0)
            
            if length > 0 and width > 0 and height >= 7.0:
                # Calculate deductions
                door_deduction = (current_room["openings"]["interior_doors"] * 20) + (current_room["openings"]["exterior_doors"] * 20)
                window_deduction = current_room["openings"]["windows"] * 15
                baseboard_deduction = (current_room["openings"]["interior_doors"] + current_room["openings"]["exterior_doors"]) * 3
                
                gross_wall_area = 2 * (length + width) * height
                net_wall_area = max(0, gross_wall_area - door_deduction - window_deduction)
                gross_perimeter = 2 * (length + width)
                net_baseboard = max(0, gross_perimeter - baseboard_deduction)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Net Wall Area", f"{net_wall_area:.1f} SF", f"-{door_deduction + window_deduction:.0f} SF")
                with col2:
                    st.metric("Net Baseboard Length", f"{net_baseboard:.1f} LF", f"-{baseboard_deduction:.0f} LF")
    
    elif current_room["input_method"] == "complex_manual":
        st.info("🔧 **Openings are defined per wall segment above.** Total counts will be calculated automatically.")
        
        # Calculate total openings from wall segments with safe type checking
        complex_geo = current_room.get("complex_geometry", {})
        wall_segments = complex_geo.get("wall_segments", [])
        
        total_doors = 0
        total_windows = 0
        for wall in wall_segments:
            # Safely count doors
            doors = wall.get("doors", [])
            for door in doors:
                if isinstance(door, dict):
                    total_doors += 1
                elif door:  # Non-empty string or other truthy value
                    total_doors += 1
            
            # Safely count windows
            windows = wall.get("windows", [])
            for window in windows:
                if isinstance(window, dict):
                    total_windows += 1
                elif window:  # Non-empty string or other truthy value
                    total_windows += 1
        
        # Update openings count for compatibility
        current_room["openings"]["interior_doors"] = total_doors  # Simplified - could separate interior/exterior
        current_room["openings"]["windows"] = total_windows
        
        if total_doors > 0 or total_windows > 0:
            st.success(f"📊 **Total Openings**: {total_doors} doors, {total_windows} windows (from wall segments)")
    
    # Current Conditions
    st.subheader("🔄 Current Conditions")
    
    mitigation_options = get_mitigation_status_options()
    current_mitigation = current_room["current_conditions"].get("mitigation_status", "no_demo")
    mitigation_index = 0  # Default to first option
    for i, opt in enumerate(mitigation_options):
        if opt[0] == current_mitigation:
            mitigation_index = i
            break
    
    current_room["current_conditions"]["mitigation_status"] = st.selectbox(
        "Mitigation Status",
        options=[opt[0] for opt in mitigation_options],
        format_func=lambda x: next(opt[1] for opt in mitigation_options if opt[0] == x),
        index=mitigation_index,
        key=f"mitigation_{selected_room_index}"
    )
    
    # Work Packages for this room
    st.subheader("📦 Work Package Templates")
    st.write("Select applicable work packages for this room:")
    
    # Initialize room work packages if not exists
    if "selected_packages" not in current_room:
        current_room["selected_packages"] = []
    
    package_options = get_standard_work_packages()
    
    # Auto-suggest work packages based on AI analysis
    if (current_room["input_method"] == "ai_image_analysis" and 
        current_room["ai_analysis"].get("extracted_results")):
        
        results = current_room["ai_analysis"]["extracted_results"]
        room_type = results.get("room_identification", {}).get("detected_room_name", "")
        
        if room_type == "bathroom":
            st.info("💡 **AI detected bathroom - Consider:** Bathroom Restoration, Moisture-resistant materials")
        elif room_type == "kitchen":
            st.info("💡 **AI detected kitchen - Consider:** Kitchen Prep Package, Cabinet coordination")
        elif "water" in current_room.get("room_name", "").lower():
            st.info("💡 **Water damage detected - Consider:** Full Room Restoration Package")
    
    # Group packages by category for better organization
    full_packages = [pkg for pkg in package_options if "Package" in pkg[1] and not any(word in pkg[1] for word in ["Bathroom", "Kitchen", "Basement", "Stairway", "Structural", "Subfloor", "Drywall"])]
    specialty_packages = [pkg for pkg in package_options if any(word in pkg[1] for word in ["Bathroom", "Kitchen", "Basement", "Stairway"])]
    structural_packages = [pkg for pkg in package_options if any(word in pkg[1] for word in ["Structural", "Subfloor", "Drywall"])]
    
    # Display packages in expandable sections
    with st.expander("📦 Standard Room Packages"):
        for pkg in full_packages:
            selected = st.checkbox(
                f"{pkg[1]}",
                value=pkg[0] in current_room.get("selected_packages", []),
                key=f"room_{selected_room_index}_pkg_{pkg[0]}",
                help=pkg[2]
            )
            if selected and pkg[0] not in current_room.get("selected_packages", []):
                current_room.setdefault("selected_packages", []).append(pkg[0])
            elif not selected and pkg[0] in current_room.get("selected_packages", []):
                current_room["selected_packages"].remove(pkg[0])
    
    with st.expander("🏠 Specialty Room Packages"):
        for pkg in specialty_packages:
            selected = st.checkbox(
                f"{pkg[1]}",
                value=pkg[0] in current_room.get("selected_packages", []),
                key=f"room_{selected_room_index}_pkg_{pkg[0]}",
                help=pkg[2]
            )
            if selected and pkg[0] not in current_room.get("selected_packages", []):
                current_room.setdefault("selected_packages", []).append(pkg[0])
            elif not selected and pkg[0] in current_room.get("selected_packages", []):
                current_room["selected_packages"].remove(pkg[0])
    
    with st.expander("🔧 Structural & Specialty Packages"):
        for pkg in structural_packages:
            selected = st.checkbox(
                f"{pkg[1]}",
                value=pkg[0] in current_room.get("selected_packages", []),
                key=f"room_{selected_room_index}_pkg_{pkg[0]}",
                help=pkg[2]
            )
            if selected and pkg[0] not in current_room.get("selected_packages", []):
                current_room.setdefault("selected_packages", []).append(pkg[0])
            elif not selected and pkg[0] in current_room.get("selected_packages", []):
                current_room["selected_packages"].remove(pkg[0])
    
    # Show selected packages for this room
    if current_room.get("selected_packages"):
        st.info(f"✅ **Selected packages for this room:** {', '.join(current_room['selected_packages'])}")
    
    # Work Scope Selection
    st.subheader("🏗️ Work Scope Selection")
    
    work_scope = current_room["work_scope"]
    
    # Auto-suggest work scope based on work packages
    selected_packages = current_room.get("selected_packages", [])
    if selected_packages:
        st.subheader("🤖 Auto-Suggested Work Scope")
        st.write("Based on selected work packages, the following work scope is recommended:")
        
        # Auto-populate based on packages
        if "full_room_restoration" in selected_packages:
            work_scope["flooring"]["required"] = True
            work_scope["drywall"]["required"] = True
            work_scope["paint"]["required"] = True
            work_scope["trim_baseboard"]["required"] = True
            work_scope["insulation"]["required"] = True
            st.info("✅ Full restoration scope auto-applied: Flooring, Drywall, Paint, Trim, Insulation")
        
        if "bathroom_restoration" in selected_packages:
            work_scope["flooring"]["required"] = True
            work_scope["drywall"]["required"] = True
            work_scope["paint"]["required"] = True
            st.info("✅ Bathroom restoration scope auto-applied with moisture-resistant requirements")
        
        if "floor_replacement" in selected_packages:
            work_scope["flooring"]["required"] = True
            work_scope["trim_baseboard"]["required"] = True
            st.info("✅ Floor replacement scope auto-applied: Flooring and Trim")
        
        if "paint_refresh" in selected_packages:
            work_scope["paint"]["required"] = True
            st.info("✅ Paint refresh scope auto-applied")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Flooring
        work_scope["flooring"]["required"] = st.checkbox(
            "Flooring Work Required",
            value=work_scope["flooring"].get("required", False),
            key=f"flooring_req_{selected_room_index}"
        )
        
        if work_scope["flooring"]["required"]:
            flooring_types = ["hardwood", "laminate", "luxury_vinyl_plank", "carpet", "tile", "sheet_vinyl"]
            current_flooring_type = work_scope["flooring"].get("type", "hardwood")
            flooring_type_index = 0
            if current_flooring_type in flooring_types:
                flooring_type_index = flooring_types.index(current_flooring_type)
                
            work_scope["flooring"]["type"] = st.selectbox(
                "Flooring Type",
                options=flooring_types,
                index=flooring_type_index,
                key=f"flooring_type_{selected_room_index}"
            )
            
            # Auto-suggest flooring based on room type and AI analysis
            ai_analysis = current_room.get("ai_analysis", {})
            if ai_analysis.get("extracted_results"):
                room_type = ai_analysis["extracted_results"].get("room_identification", {}).get("detected_room_name", "")
                if room_type == "bathroom":
                    st.info("💡 Recommended: Luxury Vinyl Plank or Tile for moisture resistance")
                elif room_type == "kitchen":
                    st.info("💡 Recommended: Tile or Luxury Vinyl Plank for durability")
                elif room_type in ["bedroom", "living_room"]:
                    st.info("💡 Recommended: Hardwood or Laminate for comfort")
        
        # Drywall
        work_scope["drywall"]["required"] = st.checkbox(
            "Drywall Work Required",
            value=work_scope["drywall"].get("required", False),
            key=f"drywall_req_{selected_room_index}"
        )
        
        if work_scope["drywall"]["required"]:
            drywall_extents = ["full_room", "repair_blend", "patches_only"]
            current_drywall_extent = work_scope["drywall"].get("extent", "full_room")
            drywall_extent_index = 0
            if current_drywall_extent in drywall_extents:
                drywall_extent_index = drywall_extents.index(current_drywall_extent)
                
            work_scope["drywall"]["extent"] = st.selectbox(
                "Drywall Extent",
                options=drywall_extents,
                index=drywall_extent_index,
                key=f"drywall_extent_{selected_room_index}"
            )
        
        # Paint
        work_scope["paint"]["required"] = st.checkbox(
            "Paint Work Required",
            value=work_scope["paint"].get("required", False),
            key=f"paint_req_{selected_room_index}"
        )
        
        if work_scope["paint"]["required"]:
            paint_scopes = ["walls_and_ceiling", "walls_only", "ceiling_only", "touch_up"]
            current_paint_scope = work_scope["paint"].get("scope", "walls_and_ceiling")
            paint_scope_index = 0
            if current_paint_scope in paint_scopes:
                paint_scope_index = paint_scopes.index(current_paint_scope)
                
            work_scope["paint"]["scope"] = st.selectbox(
                "Paint Scope",
                options=paint_scopes,
                index=paint_scope_index,
                key=f"paint_scope_{selected_room_index}"
            )
    
    with col2:
        # Trim/Baseboard
        work_scope["trim_baseboard"]["required"] = st.checkbox(
            "Trim/Baseboard Work Required",
            value=work_scope["trim_baseboard"].get("required", False),
            key=f"trim_req_{selected_room_index}"
        )
        
        # Insulation
        work_scope["insulation"]["required"] = st.checkbox(
            "Insulation Work Required",
            value=work_scope["insulation"].get("required", False),
            key=f"insulation_req_{selected_room_index}"
        )
        
        if work_scope["insulation"]["required"]:
            insulation_types = ["fiberglass", "cellulose", "spray_foam", "rigid_foam"]
            current_insulation_type = work_scope["insulation"].get("type", "fiberglass")
            insulation_type_index = 0
            if current_insulation_type in insulation_types:
                insulation_type_index = insulation_types.index(current_insulation_type)
                
            work_scope["insulation"]["type"] = st.selectbox(
                "Insulation Type",
                options=insulation_types,
                index=insulation_type_index,
                key=f"insulation_type_{selected_room_index}"
            )
            
            work_scope["insulation"]["r_value"] = st.text_input(
                "R-Value",
                value=work_scope["insulation"].get("r_value", ""),
                key=f"r_value_{selected_room_index}"
            )
    
    # Specialty Work
    st.subheader("🔧 Specialty Work")
    
    col1, col2 = st.columns(2)
    
    with col1:
        work_scope["electrical"]["required"] = st.checkbox(
            "Electrical Work Required",
            value=work_scope["electrical"].get("required", False),
            key=f"electrical_req_{selected_room_index}"
        )
        
        if work_scope["electrical"]["required"]:
            work_scope["electrical"]["details"] = st.text_area(
                "Electrical Details",
                value=work_scope["electrical"].get("details", ""),
                key=f"electrical_details_{selected_room_index}"
            )
        
        work_scope["plumbing"]["required"] = st.checkbox(
            "Plumbing Work Required",
            value=work_scope["plumbing"].get("required", False),
            key=f"plumbing_req_{selected_room_index}"
        )
        
        if work_scope["plumbing"]["required"]:
            work_scope["plumbing"]["details"] = st.text_area(
                "Plumbing Details",
                value=work_scope["plumbing"].get("details", ""),
                key=f"plumbing_details_{selected_room_index}"
            )
    
    with col2:
        work_scope["hvac"]["required"] = st.checkbox(
            "HVAC Work Required",
            value=work_scope["hvac"].get("required", False),
            key=f"hvac_req_{selected_room_index}"
        )
        
        if work_scope["hvac"]["required"]:
            work_scope["hvac"]["details"] = st.text_area(
                "HVAC Details",
                value=work_scope["hvac"].get("details", ""),
                key=f"hvac_details_{selected_room_index}"
            )
        
        builtin_actions = ["none", "work_around", "remove_replace", "protect"]
        current_builtin_action = work_scope["built_ins"].get("action", "none")
        builtin_action_index = 0
        if current_builtin_action in builtin_actions:
            builtin_action_index = builtin_actions.index(current_builtin_action)
            
        work_scope["built_ins"]["action"] = st.selectbox(
            "Built-ins Action",
            options=builtin_actions,
            index=builtin_action_index,
            key=f"builtin_action_{selected_room_index}"
        )
        
        if work_scope["built_ins"]["action"] != "none":
            work_scope["built_ins"]["details"] = st.text_area(
                "Built-ins Details",
                value=work_scope["built_ins"].get("details", ""),
                key=f"builtin_details_{selected_room_index}"
            )
    
    # Special Conditions
    st.subheader("⚠️ Special Conditions")
    
    special_conditions = current_room["special_conditions"]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Access & Protection:**")
        
        access_protection = special_conditions["access_protection"]
        
        access_protection["heavy_furniture"] = st.checkbox(
            "Heavy furniture - Moving required",
            value=access_protection.get("heavy_furniture", False),
            key=f"heavy_furniture_{selected_room_index}"
        )
        
        access_protection["delicate_items"] = st.checkbox(
            "Delicate items - Extra protection needed",
            value=access_protection.get("delicate_items", False),
            key=f"delicate_items_{selected_room_index}"
        )
        
        access_protection["limited_access"] = st.checkbox(
            "Limited access - Narrow doorways, stairs",
            value=access_protection.get("limited_access", False),
            key=f"limited_access_{selected_room_index}"
        )
        
        access_protection["work_around_items"] = st.text_input(
            "Work around items (specify)",
            value=access_protection.get("work_around_items", ""),
            key=f"work_around_{selected_room_index}"
        )
    
    with col2:
        st.write("**Room-Specific Features:**")
        
        room_features = special_conditions["room_features"]
        
        # Stairs
        stairs = room_features["stairs"]
        stairs["present"] = st.checkbox(
            "Stairs present",
            value=stairs.get("present", False),
            key=f"stairs_present_{selected_room_index}"
        )
        
        if stairs["present"]:
            stair_types = ["straight", "l_turn", "u_turn", "spiral"]
            current_stair_type = stairs.get("type", "straight")
            stair_type_index = 0
            if current_stair_type in stair_types:
                stair_type_index = stair_types.index(current_stair_type)
                
            stairs["type"] = st.selectbox(
                "Stair Type",
                options=stair_types,
                index=stair_type_index,
                key=f"stair_type_{selected_room_index}"
            )
        
        # High ceilings
        high_ceilings = room_features["high_ceilings"]
        high_ceilings["present"] = st.checkbox(
            "High ceilings (>10 ft)",
            value=high_ceilings.get("present", False),
            key=f"high_ceiling_{selected_room_index}"
        )
        
        if high_ceilings["present"]:
            high_ceilings["height"] = st.number_input(
                "Ceiling Height",
                min_value=10.0,
                max_value=30.0,
                value=float(high_ceilings.get("height", 12.0)),
                key=f"ceiling_height_{selected_room_index}"
            )
        
        # Skylights
        skylights = room_features["skylights"]
        skylights["present"] = st.checkbox(
            "Skylights present",
            value=skylights.get("present", False),
            key=f"skylights_{selected_room_index}"
        )
        
        if skylights["present"]:
            skylights["quantity"] = st.number_input(
                "Number of Skylights",
                min_value=1,
                value=skylights.get("quantity", 1),
                key=f"skylight_qty_{selected_room_index}"
            )
        
        # Fireplace
        fireplace = room_features["fireplace"]
        fireplace["present"] = st.checkbox(
            "Fireplace present",
            value=fireplace.get("present", False),
            key=f"fireplace_{selected_room_index}"
        )
        
        if fireplace["present"]:
            fireplace_actions = ["work_around", "protect", "modify"]
            current_fireplace_action = fireplace.get("action", "work_around")
            fireplace_action_index = 0
            if current_fireplace_action in fireplace_actions:
                fireplace_action_index = fireplace_actions.index(current_fireplace_action)
                
            fireplace["action"] = st.selectbox(
                "Fireplace Action",
                options=fireplace_actions,
                index=fireplace_action_index,
                key=f"fireplace_action_{selected_room_index}"
            )
    
    # Room-specific Protection Requirements
    st.subheader("🛡️ Room Protection Requirements")
    
    # Initialize room protection if not exists
    if "protection_requirements" not in current_room:
        current_room["protection_requirements"] = {}
    
    protection_req = current_room["protection_requirements"]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**🔄 Work Phase Protection**")
        
        protection_req["dust_containment"] = st.selectbox(
            "Dust Containment Level",
            options=["none", "basic_plastic", "zipwall_system", "negative_pressure"],
            index=["none", "basic_plastic", "zipwall_system", "negative_pressure"].index(
                protection_req.get("dust_containment", "basic_plastic")
            ),
            key=f"dust_containment_{selected_room_index}",
            help="Level of dust protection needed for this room"
        )
        
        protection_req["floor_protection"] = st.selectbox(
            "Floor Protection",
            options=["none", "cardboard", "ram_board", "plywood"],
            index=["none", "cardboard", "ram_board", "plywood"].index(
                protection_req.get("floor_protection", "ram_board")
            ),
            key=f"floor_protection_{selected_room_index}",
            help="Floor protection material for this room"
        )
        
        protection_req["wall_protection"] = st.checkbox(
            "Wall protection required",
            value=protection_req.get("wall_protection", False),
            key=f"wall_protection_{selected_room_index}",
            help="Protect walls during work in this room"
        )
    
    with col2:
        st.write("**🚚 Access & Coordination**")
        
        protection_req["access_route_protection"] = st.checkbox(
            "Access route protection needed",
            value=protection_req.get("access_route_protection", False),
            key=f"access_route_{selected_room_index}",
            help="Protect path to this room during work"
        )
        
        protection_req["climate_control"] = st.checkbox(
            "Climate control required",
            value=protection_req.get("climate_control", False),
            key=f"climate_control_{selected_room_index}",
            help="Maintain temperature/humidity during work"
        )
        
        protection_req["work_sequence_critical"] = st.checkbox(
            "Work sequence critical",
            value=protection_req.get("work_sequence_critical", False),
            key=f"work_sequence_{selected_room_index}",
            help="This room has specific work sequence requirements"
        )
        
        if protection_req.get("work_sequence_critical"):
            protection_req["sequence_notes"] = st.text_area(
                "Sequence Requirements",
                value=protection_req.get("sequence_notes", ""),
                key=f"sequence_notes_{selected_room_index}",
                help="Describe specific sequence requirements"
            )
    
    # Phase-specific requirements
    st.write("**📅 Phase-Specific Requirements**")
    
    phases = ["demo", "rough_work", "finish_work", "final"]
    phase_requirements = protection_req.setdefault("phase_requirements", {})
    
    for phase in phases:
        phase_req = phase_requirements.setdefault(phase, {})
        
        with st.expander(f"{phase.replace('_', ' ').title()} Phase"):
            col1, col2 = st.columns(2)
            
            with col1:
                phase_req["special_protection"] = st.checkbox(
                    "Special protection needed",
                    value=phase_req.get("special_protection", False),
                    key=f"{phase}_protection_{selected_room_index}"
                )
                
                phase_req["coordination_required"] = st.checkbox(
                    "Trade coordination required",
                    value=phase_req.get("coordination_required", False),
                    key=f"{phase}_coordination_{selected_room_index}"
                )
            
            with col2:
                phase_req["inspection_required"] = st.checkbox(
                    "Inspection required",
                    value=phase_req.get("inspection_required", False),
                    key=f"{phase}_inspection_{selected_room_index}"
                )
                
                if phase_req.get("special_protection") or phase_req.get("coordination_required"):
                    phase_req["notes"] = st.text_input(
                        "Phase Notes",
                        value=phase_req.get("notes", ""),
                        key=f"{phase}_notes_{selected_room_index}"
                    )
    
    # Calculate quantities automatically when dimensions change
    if st.button("🔢 Calculate Quantities", key=f"calculate_{selected_room_index}"):
        project_standards = st.session_state.project_data["project_standards"]
        quantities = calculate_room_quantities(current_room, project_standards)
        current_room["calculated_quantities"] = quantities
        
        # Generate auto-justifications
        justifications = generate_auto_justifications(current_room, work_scope)
        current_room["auto_justifications"] = justifications
        
        st.success("✅ Quantities calculated!")
        
        # Display calculated quantities with better formatting
        if quantities:
            st.subheader("📊 Calculated Quantities")
            
            # Show in tabs for better organization
            tab1, tab2, tab3 = st.tabs(["📐 Base Areas", "🔧 Work Quantities", "📋 Material Summary"])
            
            with tab1:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Floor Area", f"{quantities.get('floor_area', 0):.1f} SF")
                    st.metric("Wall Area (Gross)", f"{quantities.get('wall_area_gross', 0):.1f} SF")
                    st.metric("Wall Area (Net)", f"{quantities.get('wall_area_net', 0):.1f} SF")
                with col2:
                    st.metric("Ceiling Area", f"{quantities.get('ceiling_area', 0):.1f} SF")
                    st.metric("Perimeter (Gross)", f"{quantities.get('perimeter_gross', 0):.1f} LF")
                    st.metric("Baseboard Length", f"{quantities.get('baseboard_length_net', 0):.1f} LF")
            
            with tab2:
                col1, col2 = st.columns(2)
                with col1:
                    if "flooring_install_sf" in quantities:
                        waste_factor = quantities.get('flooring_waste_factor', 0.10) * 100
                        st.metric("Flooring Install", f"{quantities['flooring_install_sf']:.1f} SF", f"{waste_factor:.0f}% waste")
                    if "drywall_install_sf" in quantities:
                        st.metric("Drywall Install", f"{quantities['drywall_install_sf']:.1f} SF", "10% waste")
                with col2:
                    if "paint_sf" in quantities:
                        st.metric("Paint Area", f"{quantities['paint_sf']:.1f} SF", "5% waste")
                    if "baseboard_install_lf" in quantities:
                        st.metric("Baseboard Install", f"{quantities['baseboard_install_lf']:.1f} LF", "10% waste")
            
            with tab3:
                st.write("**📋 Material Summary:**")
                materials = []
                if work_scope["flooring"]["required"]:
                    materials.append(f"• {work_scope['flooring']['type'].title()}: {quantities.get('flooring_install_sf', 0):.1f} SF")
                if work_scope["drywall"]["required"]:
                    materials.append(f"• Drywall: {quantities.get('drywall_install_sf', 0):.1f} SF")
                if work_scope["paint"]["required"]:
                    materials.append(f"• Paint: {quantities.get('paint_sf', 0):.1f} SF")
                if work_scope["trim_baseboard"]["required"]:
                    materials.append(f"• Baseboard: {quantities.get('baseboard_install_lf', 0):.1f} LF")
                
                if materials:
                    for material in materials:
                        st.write(material)
                else:
                    st.write("• No materials calculated yet")
    
    # Auto-calculate when dimensions change (only if valid)
    if current_room["input_method"] == "simple_rectangular":
        length = current_room["dimensions"].get("length", 0.0)
        width = current_room["dimensions"].get("width", 0.0)
        height = max(current_room["dimensions"].get("height", 8.0), 7.0)
        
        if length > 0 and width > 0 and height >= 7.0:
            # Store basic calculations for immediate display
            current_room["dimensions"]["floor_area"] = length * width
            current_room["dimensions"]["wall_area"] = 2 * (length + width) * height
            current_room["dimensions"]["ceiling_area"] = length * width
    
    elif current_room["input_method"] == "complex_manual":
        # For complex rooms, calculations are handled in the wall segments section
        complex_geo = current_room.get("complex_geometry", {})
        if complex_geo.get("wall_segments"):
            total_perimeter = sum(wall.get("length_ft", 0) for wall in complex_geo["wall_segments"])
            current_room["dimensions"]["perimeter_actual"] = total_perimeter
            
            # Use manual area if provided, otherwise estimated
            if current_room["dimensions"].get("floor_area_manual", 0) > 0:
                floor_area = current_room["dimensions"]["floor_area_manual"]
            else:
                floor_area = current_room["dimensions"].get("floor_area_estimated", 0)
            
            if floor_area > 0:
                height = max(current_room["dimensions"].get("height", 8.0), 7.0)
                current_room["dimensions"]["ceiling_area"] = floor_area
                # Wall area calculated from actual perimeter
                current_room["dimensions"]["wall_area"] = total_perimeter * height
    
    # Room validation with enhanced feedback
    errors = validate_room_data(current_room)
    current_room["validation_status"]["errors"] = errors
    current_room["validation_status"]["is_valid"] = len(errors) == 0
    
    if errors:
        st.error("❌ Room validation errors:")
        for error in errors:
            st.write(f"• {error}")
        
        # Provide helpful suggestions
        if "Length must be greater than 0" in str(errors):
            st.info("💡 Tip: Try using AI image analysis or enter manual measurements above")
        if "Room name is required" in str(errors):
            st.info("💡 Tip: Enter a descriptive room name like 'Master Bathroom' or 'Kitchen'")
    else:
        st.success("✅ Room validation passed!")
        
        # Show completion status
        completion_items = []
        if current_room.get("room_name"):
            completion_items.append("Name")
        if current_room["dimensions"].get("floor_area", 0) > 0:
            completion_items.append("Measurements")
        if any(scope.get("required") for scope in current_room["work_scope"].values()):
            completion_items.append("Work Scope")
        if current_room.get("selected_packages"):
            completion_items.append("Work Packages")
        
        if completion_items:
            st.info(f"✅ **Completed:** {', '.join(completion_items)}")
        
        # Show total room value if quantities calculated
        quantities = current_room.get("calculated_quantities", {})
        if quantities:
            total_materials = 0
            material_count = 0
            for work_type in ["flooring_install_sf", "drywall_install_sf", "paint_sf", "baseboard_install_lf"]:
                if work_type in quantities:
                    material_count += 1
            
            if material_count > 0:
                st.success(f"📊 **Room has {material_count} calculated work items ready for pricing**")

def room_connectivity_page():
    """Room Connectivity page"""
    st.header("🔗 Room Connectivity Matrix")
    
    rooms = st.session_state.project_data["rooms"]
    connectivity = st.session_state.project_data.get("room_connectivity", [])
    
    if not rooms:
        st.info("No rooms added yet. Please add rooms first.")
        return
    
    st.subheader("🔄 Room Adjacency Configuration")
    st.write("Define which rooms are connected to prevent work duplication:")
    
    # Add new connection
    if st.button("➕ Add Room Connection"):
        connectivity.append({
            "primary_room": "",
            "connected_room": "",
            "shared_element": "",
            "overlap_prevention": "handle_in_primary_only"
        })
        st.session_state.project_data["room_connectivity"] = connectivity
    
    # Display existing connections
    room_names = [room.get("room_name", f"Room {i+1}") for i, room in enumerate(rooms)]
    
    for i, connection in enumerate(connectivity):
        with st.expander(f"Connection {i+1}"):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                primary_idx = 0
                if connection.get("primary_room") in room_names:
                    primary_idx = room_names.index(connection["primary_room"])
                
                selected_primary = st.selectbox(
                    "Primary Room",
                    options=room_names,
                    index=primary_idx,
                    key=f"primary_{i}"
                )
                connection["primary_room"] = selected_primary
            
            with col2:
                connected_idx = 0
                if connection.get("connected_room") in room_names:
                    connected_idx = room_names.index(connection["connected_room"])
                
                selected_connected = st.selectbox(
                    "Connected Room",
                    options=room_names,
                    index=connected_idx,
                    key=f"connected_{i}"
                )
                connection["connected_room"] = selected_connected
            
            with col3:
                shared_elements = ["door", "wall", "opening", "flooring_transition"]
                element_idx = 0
                if connection.get("shared_element") in shared_elements:
                    element_idx = shared_elements.index(connection["shared_element"])
                
                connection["shared_element"] = st.selectbox(
                    "Shared Element",
                    options=shared_elements,
                    index=element_idx,
                    key=f"element_{i}"
                )
            
            with col4:
                prevention_options = ["handle_in_primary_only", "split_evenly", "custom"]
                prevention_idx = 0
                if connection.get("overlap_prevention") in prevention_options:
                    prevention_idx = prevention_options.index(connection["overlap_prevention"])
                
                connection["overlap_prevention"] = st.selectbox(
                    "Overlap Prevention",
                    options=prevention_options,
                    index=prevention_idx,
                    key=f"prevention_{i}"
                )
            
            if st.button(f"🗑️ Remove Connection {i+1}", key=f"remove_conn_{i}"):
                connectivity.pop(i)
                st.rerun()
    
    # Auto-detect connections (placeholder for future enhancement)
    st.subheader("🤖 Auto-Detection")
    if st.button("🔍 Auto-Detect Room Connections"):
        st.info("Auto-detection feature will be available with floor plan uploads.")

def protection_matrix_page():
    """Protection Matrix page - Project-level coordination"""
    st.header("🛡️ Project-Wide Protection & Coordination")
    
    st.info("💡 Room-specific protection requirements are now configured in the Room Data Entry section. This page handles project-wide coordination.")
    
    protection_matrix = st.session_state.project_data.get("protection_matrix", {})
    
    st.subheader("🔄 Project-Wide Work Phase Coordination")
    st.write("Define overall project coordination requirements:")
    
    # Project-wide coordination settings
    project_coordination = protection_matrix.setdefault("project_coordination", {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**🔧 Multi-Trade Coordination**")
        
        project_coordination["electrical_rough_in"] = st.checkbox(
            "Electrical rough-in required before drywall",
            value=project_coordination.get("electrical_rough_in", False),
            help="Coordinate electrical work across all rooms"
        )
        
        project_coordination["plumbing_rough_in"] = st.checkbox(
            "Plumbing rough-in required before flooring",
            value=project_coordination.get("plumbing_rough_in", False),
            help="Coordinate plumbing work across all rooms"
        )
        
        project_coordination["hvac_coordination"] = st.checkbox(
            "HVAC coordination for register/vent work",
            value=project_coordination.get("hvac_coordination", False),
            help="Coordinate HVAC work across all rooms"
        )
    
    with col2:
        st.write("**📋 Project Inspections**")
        
        project_coordination["rough_inspection"] = st.checkbox(
            "Rough inspection required",
            value=project_coordination.get("rough_inspection", False),
            help="Schedule inspections for rough work phase"
        )
        
        project_coordination["final_inspection"] = st.checkbox(
            "Final inspection preparation required",
            value=project_coordination.get("final_inspection", False),
            help="Coordinate final inspections across all work"
        )
        
        project_coordination["permit_coordination"] = st.checkbox(
            "Permit coordination required",
            value=project_coordination.get("permit_coordination", False),
            help="Manage permits across multiple trades"
        )
    
    # Work sequence dependencies
    st.subheader("📅 Work Sequence Dependencies")
    
    sequence_dependencies = protection_matrix.setdefault("sequence_dependencies", {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        sequence_dependencies["structural_first"] = st.checkbox(
            "Structural repairs must be completed first",
            value=sequence_dependencies.get("structural_first", False),
            help="All structural work before other trades"
        )
        
        sequence_dependencies["roofing_completion"] = st.checkbox(
            "Roofing completion required before interior work",
            value=sequence_dependencies.get("roofing_completion", False),
            help="Ensure building is weather-tight"
        )
    
    with col2:
        sequence_dependencies["utilities_rough"] = st.checkbox(
            "All utility rough-in before drywall",
            value=sequence_dependencies.get("utilities_rough", False),
            help="Electrical, plumbing, HVAC rough-in coordination"
        )
        
        sequence_dependencies["flooring_continuity"] = st.checkbox(
            "Flooring installation in continuity zones together",
            value=sequence_dependencies.get("flooring_continuity", False),
            help="Install connected flooring areas simultaneously"
        )
    
    # Project-wide protection standards
    st.subheader("🛡️ Project Protection Standards")
    
    protection_standards = protection_matrix.setdefault("protection_standards", {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**🏠 Occupied Area Protection**")
        
        protection_standards["dust_containment"] = st.selectbox(
            "Dust Containment Level",
            options=["none", "basic_plastic", "zipwall_system", "negative_pressure"],
            index=["none", "basic_plastic", "zipwall_system", "negative_pressure"].index(
                protection_standards.get("dust_containment", "basic_plastic")
            ),
            help="Level of dust protection for occupied areas"
        )
        
        protection_standards["floor_protection"] = st.selectbox(
            "Floor Protection Standard",
            options=["none", "cardboard", "ram_board", "plywood"],
            index=["none", "cardboard", "ram_board", "plywood"].index(
                protection_standards.get("floor_protection", "ram_board")
            ),
            help="Standard floor protection material"
        )
    
    with col2:
        st.write("**🚚 Access & Material Handling**")
        
        protection_standards["access_protection"] = st.selectbox(
            "Access Route Protection",
            options=["none", "basic", "full_coverage", "temporary_flooring"],
            index=["none", "basic", "full_coverage", "temporary_flooring"].index(
                protection_standards.get("access_protection", "basic")
            ),
            help="Protection level for access routes"
        )
        
        protection_standards["material_staging"] = st.text_input(
            "Material Staging Area",
            value=protection_standards.get("material_staging", ""),
            help="Designated area for material storage"
        )
    
    st.info("🏠 **For room-specific protection requirements, configure them in the Room Data Entry section.**")

def summary_export_page():
    """Summary & Export page"""
    st.header("📊 Project Summary & Export")
    
    project_data = st.session_state.project_data
    
    # Project overview
    st.subheader("📋 Project Overview")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        property_address = project_data["property_info"].get("property_address", "Not specified")
        st.metric("Property", property_address)
        
        rooms_count = len(project_data["rooms"])
        st.metric("Total Rooms", rooms_count)
    
    with col2:
        claim_number = project_data["property_info"].get("claim_number", "Not specified")
        st.metric("Claim Number", claim_number)
        
        work_packages = len(project_data["work_packages"].get("selected_packages", []))
        st.metric("Work Packages", work_packages)
    
    with col3:
        damage_source = project_data["property_info"].get("primary_damage_source", "Not specified")
        st.metric("Damage Source", damage_source.replace("_", " ").title())
        
        # Calculate total floor area
        total_area = sum(room["dimensions"].get("floor_area", 0) for room in project_data["rooms"])
        st.metric("Total Floor Area", f"{total_area:.1f} SF")
    
    # Validation status
    st.subheader("✅ Validation Status")
    
    errors = validate_project_data(project_data)
    
    if errors:
        st.error(f"❌ {len(errors)} validation errors found:")
        for error in errors:
            st.write(f"• {error}")
    else:
        st.success("✅ All validations passed! Project is ready for export.")
    
    # Room summary
    if project_data["rooms"]:
        st.subheader("🏠 Room Summary")
        
        room_summary_data = []
        for i, room in enumerate(project_data["rooms"]):
            room_summary_data.append({
                "Room": room.get("room_name", f"Room {i+1}"),
                "Zone": room.get("zone_assignment", ""),
                "Area (SF)": f"{room['dimensions'].get('floor_area', 0):.1f}",
                "Flooring": "✅" if room["work_scope"]["flooring"].get("required", False) else "❌",
                "Drywall": "✅" if room["work_scope"]["drywall"].get("required", False) else "❌",
                "Paint": "✅" if room["work_scope"]["paint"].get("required", False) else "❌",
                "Status": "✅ Valid" if room["validation_status"].get("is_valid", False) else "❌ Invalid"
            })
        
        st.table(room_summary_data)
    
    # Export options
    st.subheader("📤 Export Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**📁 JSON Export**")
        st.write("Complete project data for future editing")
        
        if st.button("💾 Generate JSON Export"):
            json_str = export_to_json(project_data)
            filename = generate_filename(project_data)
            
            st.download_button(
                label="📥 Download JSON File",
                data=json_str,
                file_name=filename,
                mime="application/json"
            )
    
    with col2:
        st.write("**📊 Report Exports**")
        st.write("Formatted reports for different purposes")
        
        export_formats = [
            "Professional Estimate",
            "Insurance Supplement",
            "Work Order Package",
            "Material List",
            "Timeline Schedule"
        ]
        
        selected_format = st.selectbox("Select Export Format", export_formats)
        
        if st.button("📋 Generate Report"):
            st.info(f"🔄 Generating {selected_format}... (Feature coming soon)")
    
    # Project statistics
    st.subheader("📈 Project Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Count rooms with each work type
        flooring_rooms = sum(1 for room in project_data["rooms"] if room["work_scope"]["flooring"].get("required", False))
        st.metric("Flooring Rooms", flooring_rooms)
    
    with col2:
        drywall_rooms = sum(1 for room in project_data["rooms"] if room["work_scope"]["drywall"].get("required", False))
        st.metric("Drywall Rooms", drywall_rooms)
    
    with col3:
        paint_rooms = sum(1 for room in project_data["rooms"] if room["work_scope"]["paint"].get("required", False))
        st.metric("Paint Rooms", paint_rooms)
    
    with col4:
        # Calculate total quantities
        total_flooring = sum(
            room.get("calculated_quantities", {}).get("flooring_install_sf", 0) 
            for room in project_data["rooms"]
        )
        st.metric("Total Flooring", f"{total_flooring:.1f} SF")
    
    # Auto-justifications summary
    if any(room.get("auto_justifications") for room in project_data["rooms"]):
        st.subheader("📝 Auto-Generated Justifications")
        
        with st.expander("View Code References"):
            for i, room in enumerate(project_data["rooms"]):
                justifications = room.get("auto_justifications", {})
                if justifications:
                    st.write(f"**{room.get('room_name', f'Room {i+1}')}:**")
                    for work_type, justification in justifications.items():
                        st.write(f"• {work_type.title()}: {justification}")

# Main application
def main():
    """Main application function"""
    initialize_session_state()
    
    # Sidebar navigation
    selected_page = sidebar_navigation()
    
    # Route to appropriate page
    if selected_page == "🏠 Property & Project Basics":
        property_basics_page()
    elif selected_page == "🎯 Work Zone Management":
        work_zone_management_page()
    elif selected_page == "🔧 Project Standards":
        project_standards_page()
    elif selected_page == "📦 Work Packages":
        work_packages_page()
    elif selected_page == "🏠 Room Data Entry":
        room_data_entry_page()
    elif selected_page == "🔗 Room Connectivity":
        room_connectivity_page()
    elif selected_page == "🛡️ Protection Matrix":
        protection_matrix_page()
    elif selected_page == "📊 Summary & Export":
        summary_export_page()
    
    # Footer
    st.markdown("---")
    st.markdown("**Reconstruction Intake Form v3.0** | Enhanced with AI Image Analysis")

if __name__ == "__main__":
    main()