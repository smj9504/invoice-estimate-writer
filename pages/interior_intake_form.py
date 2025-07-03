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
    generate_auto_justifications, initialize_room_data_structures
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
    """Create sidebar navigation - Updated with new sections"""
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
    
    # Navigation menu - Updated
    st.sidebar.header("📋 Navigation")
    pages = [
        "🏠 Property & Project Basics",
        "🎯 Work Zone Management", 
        "🔧 Project Standards",
        "📏 Room Measurements",  # New: Measurement only
        "🔨 Work Data Entry",    # New: Work scope only
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
    
    # Room status summary
    st.sidebar.header("🏠 Room Status")
    rooms = st.session_state.project_data.get("rooms", [])
    if rooms:
        measured_rooms = sum(1 for room in rooms if room["dimensions"].get("floor_area", 0) > 0)
        st.sidebar.info(f"📏 **Measured Rooms**: {measured_rooms}/{len(rooms)}")
    else:
        st.sidebar.info("📏 **No rooms created yet**")
    
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
    
    # Project inspections and permits - Enhanced
    st.subheader("📋 Inspections & Permits")
    
    project_coordination = st.session_state.project_data["project_coordination"]
    
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

def work_zone_management_page():
    """Work Zone Management page - Simplified"""
    st.header("🎯 Work Zone Management")
    
    work_zones = st.session_state.project_data["work_zones"]
    
    # Content manipulation strategy
    st.subheader("📦 Content Manipulation Strategy")
    
    content_options = get_content_manipulation_options()
    work_zones["content_manipulation_strategy"] = st.selectbox(
        "How will contents be handled?",
        options=[opt[0] for opt in content_options],
        format_func=lambda x: next(opt[1] for opt in content_options if opt[0] == x),
        index=next((i for i, opt in enumerate(content_options) 
                  if opt[0] == work_zones.get("content_manipulation_strategy", "")), 0)
    )
    
    # Simplified Material Continuity
    st.subheader("🔗 Material Continuity")
    st.write("**Ensure matching materials across connected rooms:**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**🏠 Flooring Continuity**")
        
        flooring_continuity = work_zones.setdefault("flooring_continuity", "auto")
        work_zones["flooring_continuity"] = st.radio(
            "Flooring approach:",
            options=["auto", "room_by_room", "manual"],
            format_func=lambda x: {
                "auto": "🤖 Keep consistent throughout project",
                "room_by_room": "🏠 Each room independent", 
                "manual": "✋ I'll specify in each room"
            }[x],
            index=["auto", "room_by_room", "manual"].index(flooring_continuity),
            key="flooring_continuity"
        )
        
        if work_zones["flooring_continuity"] == "auto":
            st.info("✅ All rooms will use the same flooring type for consistency")
        elif work_zones["flooring_continuity"] == "manual":
            st.info("💡 Use Room Data Entry overrides to specify different flooring per room")
    
    with col2:
        st.write("**🎨 Paint Continuity**")
        
        paint_continuity = work_zones.setdefault("paint_continuity", "coordinated")
        work_zones["paint_continuity"] = st.radio(
            "Paint approach:",
            options=["coordinated", "room_by_room", "manual"],
            format_func=lambda x: {
                "coordinated": "🎨 Coordinated colors throughout",
                "room_by_room": "🏠 Each room independent",
                "manual": "✋ I'll specify in each room"
            }[x],
            index=["coordinated", "room_by_room", "manual"].index(paint_continuity),
            key="paint_continuity"
        )
        
        if work_zones["paint_continuity"] == "coordinated":
            st.info("✅ Paint colors will be coordinated across connected areas")
        elif work_zones["paint_continuity"] == "manual":
            st.info("💡 Use Room Data Entry overrides to specify different paint per room")
    
    # Simplified Work Sequence
    st.subheader("📅 Work Sequence")
    st.write("**Project coordination requirements:**")
    
    work_sequence = work_zones.setdefault("work_sequence", "standard")
    work_zones["work_sequence"] = st.radio(
        "Work sequence approach:",
        options=["standard", "custom"],
        format_func=lambda x: {
            "standard": "📋 Standard sequence (Demo → Rough trades → Drywall → Paint → Flooring → Trim)",
            "custom": "🔧 Custom sequence required"
        }[x],
        index=["standard", "custom"].index(work_sequence),
        key="work_sequence"
    )
    
    if work_zones["work_sequence"] == "custom":
        work_zones["custom_sequence_notes"] = st.text_area(
            "Custom sequence requirements:",
            value=work_zones.get("custom_sequence_notes", ""),
            height=100,
            placeholder="e.g., Must complete all electrical before any drywall, flooring in Zone A before Zone B, etc."
        )
    else:
        st.success("✅ Standard work sequence will be followed")
    
    # Multi-trade coordination (simplified)
    st.subheader("🔧 Trade Coordination")
    st.write("**Check any that apply to your project:**")
    
    coordination = work_zones.setdefault("coordination_requirements", {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        coordination["electrical_coordination"] = st.checkbox(
            "🔌 Electrical work coordination needed",
            value=coordination.get("electrical_coordination", False),
            help="Electrical rough-in, outlets, switches, fixtures"
        )
        
        coordination["plumbing_coordination"] = st.checkbox(
            "🚿 Plumbing work coordination needed", 
            value=coordination.get("plumbing_coordination", False),
            help="Plumbing rough-in, fixture installation"
        )
    
    with col2:
        coordination["hvac_coordination"] = st.checkbox(
            "❄️ HVAC work coordination needed",
            value=coordination.get("hvac_coordination", False),
            help="Ductwork, vents, register coordination"
        )
        
        coordination["inspection_coordination"] = st.checkbox(
            "📋 Inspections required",
            value=coordination.get("inspection_coordination", False),
            help="Building inspections during project"
        )
    
    # Show active coordination requirements
    active_coordination = []
    if coordination.get("electrical_coordination"):
        active_coordination.append("Electrical")
    if coordination.get("plumbing_coordination"):
        active_coordination.append("Plumbing")
    if coordination.get("hvac_coordination"):
        active_coordination.append("HVAC")
    if coordination.get("inspection_coordination"):
        active_coordination.append("Inspections")
    
    if active_coordination:
        st.info(f"🔧 **Active Coordination**: {', '.join(active_coordination)}")
    
    # Project summary
    st.subheader("📊 Work Zone Summary")
    
    summary_items = []
    
    if work_zones.get("flooring_continuity") == "auto":
        summary_items.append("✅ Consistent flooring throughout")
    elif work_zones.get("flooring_continuity") == "room_by_room":
        summary_items.append("🏠 Independent flooring per room")
    
    if work_zones.get("paint_continuity") == "coordinated":
        summary_items.append("✅ Coordinated paint colors")
    elif work_zones.get("paint_continuity") == "room_by_room":
        summary_items.append("🏠 Independent paint per room")
    
    if work_zones.get("work_sequence") == "standard":
        summary_items.append("📋 Standard work sequence")
    else:
        summary_items.append("🔧 Custom work sequence")
    
    if active_coordination:
        summary_items.append(f"🔧 {len(active_coordination)} trade coordination(s)")
    
    if summary_items:
        st.success("**Project Configuration:**")
        for item in summary_items:
            st.write(f"• {item}")
    
    # Auto-suggestions
    st.subheader("💡 Smart Suggestions")
    
    # Get rooms data for suggestions
    rooms = st.session_state.project_data.get("rooms", [])
    
    if len(rooms) > 1:
        st.info("**Based on your rooms, consider:**")
        
        # Check for bathroom patterns
        bathroom_rooms = [room for room in rooms if 'bathroom' in room.get('room_name', '').lower()]
        if len(bathroom_rooms) > 1:
            st.write("• 🚿 Multiple bathrooms detected - Consider plumbing coordination")
        
        # Check for open areas
        open_areas = [room for room in rooms if any(keyword in room.get('room_name', '').lower() 
                     for keyword in ['living', 'dining', 'kitchen', 'family'])]
        if len(open_areas) > 1:
            st.write("• 🏠 Open living areas detected - Recommend consistent flooring")
        
        # Check for bedrooms
        bedrooms = [room for room in rooms if 'bedroom' in room.get('room_name', '').lower()]
        if len(bedrooms) > 1:
            st.write("• 🛏️ Multiple bedrooms detected - Consider coordinated paint scheme")
    
    else:
        st.info("💡 Add more rooms in Room Data Entry to see smart suggestions")

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
        st.subheader("🎨 Standard Materials & Finishes")
        
        # Flooring
        flooring_options = ["hardwood", "laminate", "carpet", "tile", "vinyl", "mixed", "custom"]
        current_flooring = standards.get("flooring_default", "hardwood")
        # Safe index handling
        flooring_index = 0
        if current_flooring in flooring_options:
            flooring_index = flooring_options.index(current_flooring)
        elif current_flooring and current_flooring not in flooring_options:
            flooring_index = flooring_options.index("custom")       
        
        selected_flooring = st.selectbox(
            "Flooring",
            options=flooring_options,
            format_func=lambda x: x.replace("_", " ").title() if x != "custom" else "Custom (Enter Below)",
            index=flooring_index
        )

        if selected_flooring == "custom":
            custom_flooring = st.text_input(
                "Custom Flooring Type",
                value=standards.get("flooring_custom", ""),
                placeholder="e.g., Luxury Vinyl Tile, Polished Concrete, etc."
            )
            standards["flooring_default"] = custom_flooring
            standards["flooring_custom"] = custom_flooring
        else:
            standards["flooring_default"] = selected_flooring
        
        # Carpet pad option when carpet is selected
        if selected_flooring == "carpet" or (selected_flooring == "custom" and "carpet" in standards.get("flooring_custom", "").lower()):
            standards["include_carpet_pad"] = st.checkbox(
                "Include Carpet Pad",
                value=standards.get("include_carpet_pad", True),
                help="Check if carpet pad installation is standard for carpet flooring"
            )
        
        # Wall Finish
        wall_finish_options = ["painted_drywall", "textured_drywall", "tile", "wallpaper", "wood", "brick", "custom"]
        current_wall_finish = standards.get("wall_finish", "painted_drywall")
        # Safe index handling
        wall_finish_index = 0
        if current_wall_finish in wall_finish_options:
            wall_finish_index = wall_finish_options.index(current_wall_finish)
        
        selected_wall_finish = st.selectbox(
            "Wall Finish",
            options=wall_finish_options,
            format_func=lambda x: x.replace("_", " ").title() if x != "custom" else "Custom (Enter Below)",
            index=wall_finish_index
        )

        if selected_wall_finish == "custom":
            custom_wall_finish = st.text_input(
                "Custom Wall Finish",
                value=standards.get("wall_finish_custom", ""),
                placeholder="e.g., Venetian Plaster, Shiplap, etc."
            )
            standards["wall_finish"] = custom_wall_finish
            standards["wall_finish_custom"] = custom_wall_finish
        else:
            standards["wall_finish"] = selected_wall_finish
        
        # Ceiling Finish
        ceiling_finish_options = ["painted_drywall", "textured_drywall", "tile", "wood", "drop_ceiling", "custom"]
        current_ceiling_finish = standards.get("ceiling_finish", "painted_drywall")
        # Safe index handling
        ceiling_finish_index = 0
        if current_ceiling_finish in ceiling_finish_options:
            ceiling_finish_index = ceiling_finish_options.index(current_ceiling_finish)
        
        selected_ceiling_finish = st.selectbox(
            "Ceiling Finish",
            options=ceiling_finish_options,
            format_func=lambda x: x.replace("_", " ").title() if x != "custom" else "Custom (Enter Below)",
            index=ceiling_finish_index
        )

        if selected_ceiling_finish == "custom":
            custom_ceiling_finish = st.text_input(
                "Custom Ceiling Finish",
                value=standards.get("ceiling_finish_custom", ""),
                placeholder="e.g., Coffered, Beadboard, Exposed Beam, etc."
            )
            standards["ceiling_finish"] = custom_ceiling_finish
            standards["ceiling_finish_custom"] = custom_ceiling_finish
        else:
            standards["ceiling_finish"] = selected_ceiling_finish
    
    # Second row for trim options
    st.subheader("🪵 Trim & Molding Standards")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Trim Material
        trim_material_options = ["painted_wood", "stained_wood", "mdf"]
        current_trim_material = standards.get("trim_material", "painted_wood")
        # Safe index handling
        trim_material_index = 0
        if current_trim_material in trim_material_options:
            trim_material_index = trim_material_options.index(current_trim_material)
        
        standards["trim_material"] = st.selectbox(
            "Trim Material",
            options=trim_material_options,
            format_func=lambda x: x.replace("_", " ").title(),
            index=trim_material_index
        )
        
        # Baseboard
        baseboard_options = ["standard_3_4", "medium_5_6", "tall_7_plus", "decorative", "none"]
        current_baseboard = standards.get("standard_baseboard", "standard_3_4")
        # Safe index handling
        baseboard_index = 0
        if current_baseboard in baseboard_options:
            baseboard_index = baseboard_options.index(current_baseboard)
        
        standards["standard_baseboard"] = st.selectbox(
            "Baseboard",
            options=baseboard_options,
            format_func=lambda x: {
                "standard_3_4": "Standard (3-4\")",
                "medium_5_6": "Medium (5-6\")", 
                "tall_7_plus": "Tall (7\"+)",
                "decorative": "Decorative",
                "none": "None"
            }[x],
            index=baseboard_index
        )
    
    with col2:
        # Quarter Round
        quarter_round_options = ["yes", "no"]
        current_quarter_round = standards.get("quarter_round", "yes")
        # Safe index handling
        quarter_round_index = 0
        if current_quarter_round in quarter_round_options:
            quarter_round_index = quarter_round_options.index(current_quarter_round)
        
        standards["quarter_round"] = st.selectbox(
            "Quarter Round",
            options=quarter_round_options,
            format_func=lambda x: x.title(),
            index=quarter_round_index
        )
        
        # Crown Molding
        crown_molding_options = ["none", "standard", "decorative", "contemporary"]
        current_crown_molding = standards.get("crown_molding", "none")
        # Safe index handling
        crown_molding_index = 0
        if current_crown_molding in crown_molding_options:
            crown_molding_index = crown_molding_options.index(current_crown_molding)
        
        standards["crown_molding"] = st.selectbox(
            "Crown Molding",
            options=crown_molding_options,
            format_func=lambda x: x.replace("_", " ").title(),
            index=crown_molding_index
        )
    
    with col3:
        # Paint Scope Default
        paint_scope_options = ["walls_and_ceiling", "walls_only", "ceiling_only"]
        current_paint_scope = standards.get("paint_scope_default", "walls_and_ceiling")
        # Safe index handling
        paint_scope_index = 0
        if current_paint_scope in paint_scope_options:
            paint_scope_index = paint_scope_options.index(current_paint_scope)
        
        standards["paint_scope_default"] = st.selectbox(
            "Paint Scope Default",
            options=paint_scope_options,
            format_func=lambda x: x.replace("_", " ").title(),
            index=paint_scope_index
        )

def work_data_entry_page():
    """Work Data Entry page - Work scope and demolition status - ENHANCED WITH PRESETS"""
    st.header("🔨 Work Data Entry")
    st.write("**Define work scope, demolition status, and special conditions for each room**")
    
    rooms = st.session_state.project_data["rooms"]
    
    if not rooms:
        st.warning("⚠️ No rooms available. Please create rooms in the 'Room Measurements' section first.")
        return
    
    # Filter rooms that have measurements
    measured_rooms = [room for room in rooms if room["dimensions"].get("floor_area", 0) > 0]
    
    if not measured_rooms:
        st.warning("⚠️ No rooms have been measured yet. Please complete room measurements first.")
        
        # Show unmeasured rooms
        st.write("**Unmeasured Rooms:**")
        for i, room in enumerate(rooms):
            room_name = room.get("room_name", f"Room {i+1}")
            st.write(f"• {room_name}")
        
        return
    
    # Room selector - only show measured rooms
    room_options = []
    room_indices = []
    
    for i, room in enumerate(rooms):
        if room["dimensions"].get("floor_area", 0) > 0:
            room_name = room.get("room_name", f"Room {i+1}")
            area = room["dimensions"]["floor_area"]
            room_options.append(f"{room_name} ({area:.1f} SF)")
            room_indices.append(i)
    
    if not room_options:
        st.error("No measured rooms available for work data entry.")
        return
    
    # Initialize work room index if not exists
    if "current_work_room_index" not in st.session_state:
        st.session_state.current_work_room_index = 0
    
    # Ensure index is valid
    if st.session_state.current_work_room_index >= len(room_indices):
        st.session_state.current_work_room_index = 0
    
    selected_work_room_display_index = st.selectbox(
        "Select Room for Work Data Entry",
        options=range(len(room_options)),
        format_func=lambda i: room_options[i],
        index=st.session_state.current_work_room_index
    )
    
    st.session_state.current_work_room_index = selected_work_room_display_index
    actual_room_index = room_indices[selected_work_room_display_index]
    current_room = rooms[actual_room_index]
    
    # Get project standards for presets
    project_standards = st.session_state.project_data.get("project_standards", {})
    
    # Room information header
    room_name = current_room.get("room_name", f"Room {actual_room_index + 1}")
    floor_area = current_room["dimensions"]["floor_area"]
    
    st.subheader(f"🔨 Work Data for: {room_name}")
    st.info(f"📐 **Room Size**: {floor_area:.1f} SF | **Zone**: {current_room.get('zone_assignment', 'A')}")
    
    # Initialize room data structures using utils function
    initialize_room_data_structures(current_room)
    
    # Initialize enhanced demolition status if not exist
    if "demolition_status" not in current_room:
        current_room["demolition_status"] = {
            "ceiling_drywall": {"demolished": False, "demolished_area": 0, "total_area": 0, "notes": ""},
            "wall_drywall": {"demolished": False, "demolished_area": 0, "total_area": 0, "notes": ""},
            "ceiling_insulation": {"demolished": False, "demolished_area": 0, "total_area": 0, "notes": ""},
            "wall_insulation": {"demolished": False, "demolished_area": 0, "total_area": 0, "notes": ""},
            "flooring": {"demolished": False, "demolished_area": 0, "total_area": 0, "notes": ""},
            "door_trim": {"demolished": False, "demolished_length": 0, "total_length": 0, "notes": ""},
            "window_trim": {"demolished": False, "demolished_length": 0, "total_length": 0, "notes": ""},
            "baseboard": {"demolished": False, "demolished_length": 0, "total_length": 0, "notes": ""},
            "quarter_round": {"demolished": False, "demolished_length": 0, "total_length": 0, "notes": ""},
            "general_notes": ""
        }
    
    # Enhanced work scope initialization with project standards presets
    if "work_scope" not in current_room:
        current_room["work_scope"] = {
            "drywall_walls": {"required": False, "extent": "full_room", "material": project_standards.get("wall_finish", "painted_drywall"), "notes": ""},
            "drywall_ceiling": {"required": False, "extent": "full_room", "material": project_standards.get("ceiling_finish", "painted_drywall"), "notes": ""},
            "insulation": {"required": False, "type": "fiberglass", "notes": ""},
            "flooring": {"required": False, "type": project_standards.get("flooring_default", "hardwood"), "include_pad": False, "notes": ""},
            "paint": {"required": False, "scope": project_standards.get("paint_scope_default", "walls_and_ceiling"), "notes": ""},
            "trim_baseboard": {"required": False, "notes": ""},
            "trim_door": {"required": False, "notes": ""},
            "trim_window": {"required": False, "notes": ""},
            "other_work": {"items": [], "notes": ""}
        }
    
    # Ensure all required keys exist in work_scope (for backward compatibility)
    work_scope_defaults = {
        "drywall_walls": {"required": False, "extent": "full_room", "material": project_standards.get("wall_finish", "painted_drywall"), "notes": ""},
        "drywall_ceiling": {"required": False, "extent": "full_room", "material": project_standards.get("ceiling_finish", "painted_drywall"), "notes": ""},
        "insulation": {"required": False, "type": "fiberglass", "notes": ""},
        "flooring": {"required": False, "type": project_standards.get("flooring_default", "hardwood"), "include_pad": False, "notes": ""},
        "paint": {"required": False, "scope": project_standards.get("paint_scope_default", "walls_and_ceiling"), "notes": ""},
        "trim_baseboard": {"required": False, "notes": ""},
        "trim_door": {"required": False, "notes": ""},
        "trim_window": {"required": False, "notes": ""},
        "other_work": {"items": [], "notes": ""}
    }
    
    # Migrate old drywall to new structure if exists
    if "drywall" in current_room["work_scope"]:
        old_drywall = current_room["work_scope"]["drywall"]
        current_room["work_scope"]["drywall_walls"] = {
            "required": old_drywall.get("required", False),
            "extent": old_drywall.get("extent", "full_room"),
            "material": old_drywall.get("material", project_standards.get("wall_finish", "painted_drywall")),
            "notes": old_drywall.get("notes", "")
        }
        current_room["work_scope"]["drywall_ceiling"] = {
            "required": old_drywall.get("required", False),
            "extent": "full_room",
            "material": project_standards.get("ceiling_finish", "painted_drywall"),
            "notes": ""
        }
        del current_room["work_scope"]["drywall"]
    
    # Migrate old ceiling to new structure if exists
    if "ceiling" in current_room["work_scope"]:
        old_ceiling = current_room["work_scope"]["ceiling"]
        current_room["work_scope"]["drywall_ceiling"]["material"] = old_ceiling.get("material", project_standards.get("ceiling_finish", "painted_drywall"))
        if old_ceiling.get("required", False):
            current_room["work_scope"]["drywall_ceiling"]["required"] = True
        del current_room["work_scope"]["ceiling"]
    
    # Add missing keys to existing work_scope
    for key, default_value in work_scope_defaults.items():
        if key not in current_room["work_scope"]:
            current_room["work_scope"][key] = default_value
        else:
            # Ensure material presets are applied if not already set
            if key == "drywall_walls" and "material" not in current_room["work_scope"][key]:
                current_room["work_scope"][key]["material"] = project_standards.get("wall_finish", "painted_drywall")
            elif key == "drywall_ceiling" and "material" not in current_room["work_scope"][key]:
                current_room["work_scope"][key]["material"] = project_standards.get("ceiling_finish", "painted_drywall")
            elif key == "flooring":
                if current_room["work_scope"][key].get("type") == "hardwood":
                    # Update to project standard if still default
                    current_room["work_scope"][key]["type"] = project_standards.get("flooring_default", "hardwood")
                # Apply carpet pad default if carpet
                if current_room["work_scope"][key].get("type") == "carpet" and "include_pad" not in current_room["work_scope"][key]:
                    current_room["work_scope"][key]["include_pad"] = project_standards.get("include_carpet_pad", True)
    
    # DEMOLITION STATUS SECTION
    st.subheader("🔨 Current Demolition Status")
    st.write("**What has already been demolished by water mitigation crews?**")
    
    demo_status = current_room["demolition_status"]
    
    # Auto-populate total areas from room measurements
    room_dimensions = current_room.get("dimensions", {})
    floor_area = room_dimensions.get("floor_area", 0)
    wall_area = room_dimensions.get("wall_area", 0)
    ceiling_area = room_dimensions.get("ceiling_area", 0)
    perimeter = room_dimensions.get("perimeter_gross", 0)
    
    # Auto-set total areas if they're 0
    if floor_area > 0:
        if demo_status["ceiling_drywall"]["total_area"] == 0:
            demo_status["ceiling_drywall"]["total_area"] = ceiling_area
        if demo_status["ceiling_insulation"]["total_area"] == 0:
            demo_status["ceiling_insulation"]["total_area"] = ceiling_area
        if demo_status["wall_drywall"]["total_area"] == 0:
            demo_status["wall_drywall"]["total_area"] = wall_area
        if demo_status["wall_insulation"]["total_area"] == 0:
            demo_status["wall_insulation"]["total_area"] = wall_area
        if demo_status["flooring"]["total_area"] == 0:
            demo_status["flooring"]["total_area"] = floor_area
    
    # Demolition input tabs
    tab1, tab2, tab3 = st.tabs(["🏠 Structural Elements", "🎨 Finish Elements", "📝 Notes"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Ceiling Work**")
            
            # Ceiling Drywall
            demo_status["ceiling_drywall"]["demolished"] = st.checkbox(
                "Ceiling Drywall Demolished",
                value=demo_status["ceiling_drywall"].get("demolished", False),
                key=f"ceiling_drywall_demo_{actual_room_index}"
            )
            
            if demo_status["ceiling_drywall"]["demolished"]:
                demo_status["ceiling_drywall"]["demolished_area"] = st.number_input(
                    "Demolished Area (SF)",
                    min_value=0.0,
                    value=float(demo_status["ceiling_drywall"].get("demolished_area", 0)),
                    step=0.1,
                    key=f"ceiling_drywall_demo_area_{actual_room_index}"
                )
            
            # Ceiling Insulation
            demo_status["ceiling_insulation"]["demolished"] = st.checkbox(
                "Ceiling Insulation Demolished",
                value=demo_status["ceiling_insulation"].get("demolished", False),
                key=f"ceiling_insulation_demo_{actual_room_index}"
            )
            
            if demo_status["ceiling_insulation"]["demolished"]:
                demo_status["ceiling_insulation"]["demolished_area"] = st.number_input(
                    "Insulation Demolished Area (SF)",
                    min_value=0.0,
                    value=float(demo_status["ceiling_insulation"].get("demolished_area", 0)),
                    step=0.1,
                    key=f"ceiling_insulation_demo_area_{actual_room_index}"
                )
        
        with col2:
            st.write("**Wall Work**")
            
            # Wall Drywall
            demo_status["wall_drywall"]["demolished"] = st.checkbox(
                "Wall Drywall Demolished",
                value=demo_status["wall_drywall"].get("demolished", False),
                key=f"wall_drywall_demo_{actual_room_index}"
            )
            
            if demo_status["wall_drywall"]["demolished"]:
                demo_status["wall_drywall"]["demolished_area"] = st.number_input(
                    "Wall Demo Area (SF)",
                    min_value=0.0,
                    value=float(demo_status["wall_drywall"].get("demolished_area", 0)),
                    step=0.1,
                    key=f"wall_drywall_demo_area_{actual_room_index}"
                )
            
            # Wall Insulation
            demo_status["wall_insulation"]["demolished"] = st.checkbox(
                "Wall Insulation Demolished",
                value=demo_status["wall_insulation"].get("demolished", False),
                key=f"wall_insulation_demo_{actual_room_index}"
            )
            
            if demo_status["wall_insulation"]["demolished"]:
                demo_status["wall_insulation"]["demolished_area"] = st.number_input(
                    "Wall Insulation Demo Area (SF)",
                    min_value=0.0,
                    value=float(demo_status["wall_insulation"].get("demolished_area", 0)),
                    step=0.1,
                    key=f"wall_insulation_demo_area_{actual_room_index}"
                )
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Flooring**")
            
            # Flooring
            demo_status["flooring"]["demolished"] = st.checkbox(
                "Flooring Demolished",
                value=demo_status["flooring"].get("demolished", False),
                key=f"flooring_demo_{actual_room_index}"
            )
            
            if demo_status["flooring"]["demolished"]:
                demo_status["flooring"]["demolished_area"] = st.number_input(
                    "Flooring Demo Area (SF)",
                    min_value=0.0,
                    value=float(demo_status["flooring"].get("demolished_area", 0)),
                    step=0.1,
                    key=f"flooring_demo_area_{actual_room_index}"
                )
            
            st.write("**Trim Work**")
            
            # Baseboard
            demo_status["baseboard"]["demolished"] = st.checkbox(
                "Baseboard Demolished",
                value=demo_status["baseboard"].get("demolished", False),
                key=f"baseboard_demo_{actual_room_index}"
            )
            
            if demo_status["baseboard"]["demolished"]:
                demo_status["baseboard"]["demolished_length"] = st.number_input(
                    "Baseboard Demo Length (LF)",
                    min_value=0.0,
                    value=float(demo_status["baseboard"].get("demolished_length", 0)),
                    step=0.1,
                    key=f"baseboard_demo_length_{actual_room_index}"
                )
        
        with col2:
            st.write("**Door & Window Trim**")
            
            # Door Trim
            demo_status["door_trim"]["demolished"] = st.checkbox(
                "Door Trim Demolished",
                value=demo_status["door_trim"].get("demolished", False),
                key=f"door_trim_demo_{actual_room_index}"
            )
            
            if demo_status["door_trim"]["demolished"]:
                demo_status["door_trim"]["demolished_length"] = st.number_input(
                    "Door Trim Demo Length (LF)",
                    min_value=0.0,
                    value=float(demo_status["door_trim"].get("demolished_length", 0)),
                    step=0.1,
                    key=f"door_trim_demo_length_{actual_room_index}"
                )
            
            # Window Trim
            demo_status["window_trim"]["demolished"] = st.checkbox(
                "Window Trim Demolished",
                value=demo_status["window_trim"].get("demolished", False),
                key=f"window_trim_demo_{actual_room_index}"
            )
            
            if demo_status["window_trim"]["demolished"]:
                demo_status["window_trim"]["demolished_length"] = st.number_input(
                    "Window Trim Demo Length (LF)",
                    min_value=0.0,
                    value=float(demo_status["window_trim"].get("demolished_length", 0)),
                    step=0.1,
                    key=f"window_trim_demo_length_{actual_room_index}"
                )
    
    with tab3:
        demo_status["general_notes"] = st.text_area(
            "General Demolition Notes",
            value=demo_status.get("general_notes", ""),
            key=f"demo_general_notes_{actual_room_index}",
            height=100,
            placeholder="e.g., Built-in cabinets removed, electrical fixtures down, special conditions..."
        )
    
    # WORK SCOPE SECTION
    st.subheader("🔧 Required Work Scope")
    st.write("**Define what work needs to be completed based on demolition status**")
    
    work_scope = current_room["work_scope"]
    
    # Auto-calculate work scope button
    if st.button("🤖 Auto-Calculate Work Scope", key=f"auto_calc_work_{actual_room_index}"):
        # Auto-determine work scope based on demolition status
        if demo_status["wall_drywall"]["demolished"]:
            work_scope["drywall_walls"]["required"] = True
            work_scope["paint"]["required"] = True
        
        if demo_status["ceiling_drywall"]["demolished"]:
            work_scope["drywall_ceiling"]["required"] = True
            work_scope["paint"]["required"] = True
        
        if demo_status["wall_insulation"]["demolished"] or demo_status["ceiling_insulation"]["demolished"]:
            work_scope["insulation"]["required"] = True
        
        if demo_status["flooring"]["demolished"]:
            work_scope["flooring"]["required"] = True
        
        if demo_status["baseboard"]["demolished"]:
            work_scope["trim_baseboard"]["required"] = True
        
        if demo_status["door_trim"]["demolished"]:
            work_scope["trim_door"]["required"] = True
        
        if demo_status["window_trim"]["demolished"]:
            work_scope["trim_window"]["required"] = True
        
        st.success("✅ Work scope auto-calculated based on demolition status!")
        st.rerun()
    
    # Work scope input tabs
    tab1, tab2, tab3 = st.tabs(["🏠 Structural Work", "🎨 Finishes", "📋 Additional Work"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            # Wall drywall work with material selection
            work_scope["drywall_walls"]["required"] = st.checkbox(
                "Wall Drywall Work Required",
                value=work_scope["drywall_walls"].get("required", False),
                key=f"drywall_walls_required_{actual_room_index}"
            )
            
            if work_scope["drywall_walls"]["required"]:
                work_scope["drywall_walls"]["extent"] = st.selectbox(
                    "Wall Work Extent",
                    options=["patch_repair", "partial_walls", "full_room"],
                    format_func=lambda x: {
                        "patch_repair": "Patch & Repair Only",
                        "partial_walls": "Partial Walls",
                        "full_room": "Full Room"
                    }[x],
                    key=f"drywall_walls_extent_{actual_room_index}"
                )
                
                # Wall material with custom option
                wall_material_options = ["painted_drywall", "textured_drywall", "tile", "wallpaper", "wood", "brick", "custom"]
                current_wall_material = work_scope["drywall_walls"].get("material", project_standards.get("wall_finish", "painted_drywall"))
                
                # Handle custom materials
                if current_wall_material not in wall_material_options:
                    wall_material_index = wall_material_options.index("custom")
                else:
                    wall_material_index = wall_material_options.index(current_wall_material)
                
                selected_wall_material = st.selectbox(
                    "Wall Material/Finish",
                    options=wall_material_options,
                    format_func=lambda x: x.replace("_", " ").title() if x != "custom" else "Custom (Enter Below)",
                    index=wall_material_index,
                    key=f"wall_material_{actual_room_index}"
                )
                
                if selected_wall_material == "custom":
                    custom_wall_material = st.text_input(
                        "Custom Wall Material",
                        value=current_wall_material if current_wall_material not in wall_material_options else "",
                        key=f"custom_wall_material_{actual_room_index}",
                        placeholder="e.g., Venetian Plaster, Shiplap, etc."
                    )
                    work_scope["drywall_walls"]["material"] = custom_wall_material
                else:
                    work_scope["drywall_walls"]["material"] = selected_wall_material
            
            # Ceiling drywall work with material selection
            work_scope["drywall_ceiling"]["required"] = st.checkbox(
                "Ceiling Drywall Work Required",
                value=work_scope["drywall_ceiling"].get("required", False),
                key=f"drywall_ceiling_required_{actual_room_index}"
            )
            
            if work_scope["drywall_ceiling"]["required"]:
                work_scope["drywall_ceiling"]["extent"] = st.selectbox(
                    "Ceiling Work Extent",
                    options=["patch_repair", "partial_ceiling", "full_ceiling"],
                    format_func=lambda x: {
                        "patch_repair": "Patch & Repair Only",
                        "partial_ceiling": "Partial Ceiling",
                        "full_ceiling": "Full Ceiling"
                    }[x],
                    key=f"drywall_ceiling_extent_{actual_room_index}"
                )
                
                # Ceiling material with custom option
                ceiling_material_options = ["painted_drywall", "textured_drywall", "tile", "wood", "drop_ceiling", "custom"]
                current_ceiling_material = work_scope["drywall_ceiling"].get("material", project_standards.get("ceiling_finish", "painted_drywall"))
                
                # Handle custom materials
                if current_ceiling_material not in ceiling_material_options:
                    ceiling_material_index = ceiling_material_options.index("custom")
                else:
                    ceiling_material_index = ceiling_material_options.index(current_ceiling_material)
                
                selected_ceiling_material = st.selectbox(
                    "Ceiling Material/Finish",
                    options=ceiling_material_options,
                    format_func=lambda x: x.replace("_", " ").title() if x != "custom" else "Custom (Enter Below)",
                    index=ceiling_material_index,
                    key=f"ceiling_material_{actual_room_index}"
                )
                
                if selected_ceiling_material == "custom":
                    custom_ceiling_material = st.text_input(
                        "Custom Ceiling Material",
                        value=current_ceiling_material if current_ceiling_material not in ceiling_material_options else "",
                        key=f"custom_ceiling_material_{actual_room_index}",
                        placeholder="e.g., Coffered, Beadboard, Exposed Beam, etc."
                    )
                    work_scope["drywall_ceiling"]["material"] = custom_ceiling_material
                else:
                    work_scope["drywall_ceiling"]["material"] = selected_ceiling_material
        
        with col2:
            # Insulation work
            work_scope["insulation"]["required"] = st.checkbox(
                "Insulation Work Required",
                value=work_scope["insulation"].get("required", False),
                key=f"insulation_required_{actual_room_index}"
            )
            
            if work_scope["insulation"]["required"]:
                insulation_options = ["fiberglass", "foam", "cellulose", "rockwool", "custom"]
                current_insulation = work_scope["insulation"].get("type", "fiberglass")
                
                if current_insulation not in insulation_options:
                    insulation_index = insulation_options.index("custom")
                else:
                    insulation_index = insulation_options.index(current_insulation)
                
                selected_insulation = st.selectbox(
                    "Insulation Type",
                    options=insulation_options,
                    format_func=lambda x: x.title() if x != "custom" else "Custom (Enter Below)",
                    index=insulation_index,
                    key=f"insulation_type_{actual_room_index}"
                )
                
                if selected_insulation == "custom":
                    custom_insulation = st.text_input(
                        "Custom Insulation Type",
                        value=current_insulation if current_insulation not in insulation_options else "",
                        key=f"custom_insulation_{actual_room_index}",
                        placeholder="e.g., Spray Foam, Reflective, etc."
                    )
                    work_scope["insulation"]["type"] = custom_insulation
                else:
                    work_scope["insulation"]["type"] = selected_insulation
            
            # Paint work
            work_scope["paint"]["required"] = st.checkbox(
                "Paint Work Required",
                value=work_scope["paint"].get("required", False),
                key=f"paint_required_{actual_room_index}"
            )
            
            if work_scope["paint"]["required"]:
                work_scope["paint"]["scope"] = st.selectbox(
                    "Paint Scope",
                    options=["walls_only", "ceiling_only", "walls_and_ceiling"],
                    format_func=lambda x: x.replace("_", " ").title(),
                    key=f"paint_scope_{actual_room_index}",
                    index=["walls_only", "ceiling_only", "walls_and_ceiling"].index(
                        work_scope["paint"].get("scope", project_standards.get("paint_scope_default", "walls_and_ceiling"))
                    )
                )
                
                # Paint calculation info (no waste factor)
                st.info("ℹ️ Paint quantities calculated without waste factor per updated standards")
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            # Flooring work with enhanced options
            work_scope["flooring"]["required"] = st.checkbox(
                "Flooring Work Required",
                value=work_scope["flooring"].get("required", False),
                key=f"flooring_required_{actual_room_index}"
            )
            
            if work_scope["flooring"]["required"]:
                flooring_options = ["hardwood", "laminate", "carpet", "tile", "vinyl", "lvt", "custom"]
                current_flooring = work_scope["flooring"].get("type", project_standards.get("flooring_default", "hardwood"))
                
                if current_flooring not in flooring_options:
                    flooring_index = flooring_options.index("custom")
                else:
                    flooring_index = flooring_options.index(current_flooring)
                
                selected_flooring = st.selectbox(
                    "Flooring Type",
                    options=flooring_options,
                    format_func=lambda x: {
                        "hardwood": "Hardwood",
                        "laminate": "Laminate",
                        "carpet": "Carpet",
                        "tile": "Tile",
                        "vinyl": "Vinyl",
                        "lvt": "Luxury Vinyl Tile (LVT)",
                        "custom": "Custom (Enter Below)"
                    }.get(x, x.title()),
                    index=flooring_index,
                    key=f"flooring_type_{actual_room_index}"
                )
                
                if selected_flooring == "custom":
                    custom_flooring = st.text_input(
                        "Custom Flooring Type",
                        value=current_flooring if current_flooring not in flooring_options else "",
                        key=f"custom_flooring_{actual_room_index}",
                        placeholder="e.g., Polished Concrete, Cork, Bamboo, etc."
                    )
                    work_scope["flooring"]["type"] = custom_flooring
                else:
                    work_scope["flooring"]["type"] = selected_flooring
                
                # Carpet pad option
                if selected_flooring == "carpet" or (selected_flooring == "custom" and "carpet" in current_flooring.lower()):
                    work_scope["flooring"]["include_pad"] = st.checkbox(
                        "Include Carpet Pad",
                        value=work_scope["flooring"].get("include_pad", True),
                        key=f"carpet_pad_{actual_room_index}",
                        help="Check if carpet pad installation is required"
                    )
                else:
                    # Reset pad option if not carpet
                    work_scope["flooring"]["include_pad"] = False
        
        with col2:
            # Trim work
            work_scope["trim_baseboard"]["required"] = st.checkbox(
                "Baseboard Trim Required",
                value=work_scope["trim_baseboard"].get("required", False),
                key=f"trim_baseboard_required_{actual_room_index}"
            )
            
            work_scope["trim_door"]["required"] = st.checkbox(
                "Door Trim Required",
                value=work_scope["trim_door"].get("required", False),
                key=f"trim_door_required_{actual_room_index}"
            )
            
            work_scope["trim_window"]["required"] = st.checkbox(
                "Window Trim Required",
                value=work_scope["trim_window"].get("required", False),
                key=f"trim_window_required_{actual_room_index}"
            )
    
    with tab3:
        # Enhanced Additional work items with new structure
        st.write("**Additional Work Items**")
        
        if "other_work" not in work_scope:
            work_scope["other_work"] = {"items": [], "notes": ""}
        
        # Add work item
        new_work_item = st.text_input(
            "Add Work Item",
            key=f"new_work_item_{actual_room_index}",
            placeholder="e.g., Electrical work, plumbing repair, HVAC modification"
        )
        
        if st.button("➕ Add Work Item", key=f"add_work_item_{actual_room_index}"):
            if new_work_item:
                work_scope["other_work"]["items"].append(new_work_item)
                st.success(f"✅ Added: {new_work_item}")
                st.rerun()
        
        # Show existing work items
        if work_scope["other_work"]["items"]:
            st.write("**Current Additional Work Items:**")
            for i, item in enumerate(work_scope["other_work"]["items"]):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"• {item}")
                with col2:
                    if st.button("🗑️", key=f"remove_work_item_{actual_room_index}_{i}"):
                        work_scope["other_work"]["items"].pop(i)
                        st.rerun()
        
        # General work notes
        work_scope["other_work"]["notes"] = st.text_area(
            "General Work Notes",
            value=work_scope["other_work"].get("notes", ""),
            key=f"work_general_notes_{actual_room_index}",
            height=100,
            placeholder="Special conditions, coordination requirements, material specifications..."
        )
    
    # ENHANCED QUANTITY CALCULATIONS
    st.subheader("📊 Calculated Quantities")
    
    if st.button("🔢 Calculate Quantities", key=f"calc_quantities_{actual_room_index}"):
        try:
            quantities = calculate_room_quantities(current_room, project_standards)
            
            if quantities:
                current_room["calculated_quantities"] = quantities
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Material Quantities:**")
                    if quantities.get("flooring_install_sf"):
                        waste_factor = quantities.get("flooring_waste_factor", 0) * 100
                        st.write(f"• Flooring: {quantities['flooring_install_sf']:.1f} SF (includes {waste_factor:.0f}% waste)")
                        
                        # Show carpet pad if applicable
                        if work_scope["flooring"]["required"] and work_scope["flooring"].get("include_pad"):
                            st.write(f"  - Carpet Pad: {quantities['flooring_install_sf']:.1f} SF")
                    
                    if quantities.get("drywall_install_sf"):
                        st.write(f"• Drywall: {quantities['drywall_install_sf']:.1f} SF (includes 10% waste)")
                    if quantities.get("primer_sf"):
                        st.write(f"• Primer: {quantities['primer_sf']:.1f} SF (no waste factor)")
                    if quantities.get("paint_sf"):
                        st.write(f"• Paint: {quantities['paint_sf']:.1f} SF (no waste factor)")
                
                with col2:
                    st.write("**Linear Quantities:**")
                    if quantities.get("baseboard_install_lf"):
                        st.write(f"• Baseboard: {quantities['baseboard_install_lf']:.1f} LF")
                    if quantities.get("quarter_round_install_lf"):
                        st.write(f"• Quarter Round: {quantities['quarter_round_install_lf']:.1f} LF")
                    if quantities.get("insulation_sf"):
                        st.write(f"• Insulation: {quantities['insulation_sf']:.1f} SF")
                
                st.success("✅ Quantities calculated successfully!")
            else:
                st.warning("⚠️ Could not calculate quantities. Check room measurements.")
                
        except Exception as e:
            st.error(f"❌ Error calculating quantities: {str(e)}")
    
    # Show existing quantities if available
    if current_room.get("calculated_quantities"):
        quantities = current_room["calculated_quantities"]
        with st.expander("📊 Current Calculated Quantities"):
            for key, value in quantities.items():
                if isinstance(value, (int, float)) and value > 0:
                    formatted_key = key.replace("_", " ").title()
                    st.write(f"• **{formatted_key}**: {value:.2f}")
    
    # WORK SUMMARY
    st.subheader("📋 Work Summary")
    
    # Calculate required work
    required_work = []
    
    # Wall work
    if work_scope["drywall_walls"]["required"]:
        extent = work_scope["drywall_walls"]["extent"].replace("_", " ").title()
        material = work_scope["drywall_walls"]["material"].replace("_", " ").title()
        required_work.append(f"Wall Drywall Work ({extent}) - {material}")
    
    # Ceiling work
    if work_scope["drywall_ceiling"]["required"]:
        extent = work_scope["drywall_ceiling"]["extent"].replace("_", " ").title()
        material = work_scope["drywall_ceiling"]["material"].replace("_", " ").title()
        required_work.append(f"Ceiling Drywall Work ({extent}) - {material}")
    
    if work_scope["insulation"]["required"]:
        ins_type = work_scope["insulation"]["type"].title()
        required_work.append(f"Insulation ({ins_type})")
    
    if work_scope["paint"]["required"]:
        paint_scope = work_scope["paint"]["scope"].replace("_", " ").title()
        required_work.append(f"Paint ({paint_scope}) - No waste factor applied")
    
    if work_scope["flooring"]["required"]:
        floor_type = work_scope["flooring"]["type"].title()
        floor_desc = f"Flooring ({floor_type})"
        if work_scope["flooring"].get("include_pad"):
            floor_desc += " with Carpet Pad"
        required_work.append(floor_desc)
    
    trim_work = []
    if work_scope["trim_baseboard"]["required"]:
        trim_work.append("Baseboard")
    if work_scope["trim_door"]["required"]:
        trim_work.append("Door Trim")
    if work_scope["trim_window"]["required"]:
        trim_work.append("Window Trim")
    
    if trim_work:
        required_work.append(f"Trim ({', '.join(trim_work)})")
    
    if work_scope["other_work"]["items"]:
        required_work.extend(work_scope["other_work"]["items"])
    
    if required_work:
        st.success("**Required Work:**")
        for work in required_work:
            st.write(f"• {work}")
    else:
        st.info("No work scope defined yet.")
    
    # Navigation helper
    st.subheader("🔄 Room Navigation")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.session_state.current_work_room_index > 0:
            if st.button("⬅️ Previous Room"):
                st.session_state.current_work_room_index -= 1
                st.rerun()
    
    with col2:
        st.write(f"Room {st.session_state.current_work_room_index + 1} of {len(room_options)}")
    
    with col3:
        if st.session_state.current_work_room_index < len(room_options) - 1:
            if st.button("Next Room ➡️"):
                st.session_state.current_work_room_index += 1
                st.rerun()

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
    
    # Enhanced Room Summary
    st.subheader("🏠 Room Details")
    
    rooms = project_data.get("rooms", [])
    if rooms:
        for i, room in enumerate(rooms):
            room_name = room.get("room_name", f"Room {i+1}")
            floor_area = room["dimensions"].get("floor_area", 0)
            zone = room.get("zone_assignment", "Unassigned")
            
            # Work scope summary
            work_scope = room.get("work_scope", {})
            required_work = []
            
            for work_type, work_data in work_scope.items():
                if work_type == "other_work":
                    if isinstance(work_data, dict) and work_data.get("items"):
                        required_work.extend(work_data["items"])
                elif isinstance(work_data, dict) and work_data.get("required"):
                    required_work.append(work_type.replace("_", " ").title())
            
            # Demolition summary
            demo_status = room.get("demolition_status", {})
            demo_items = []
            for demo_type, demo_data in demo_status.items():
                if isinstance(demo_data, dict) and demo_data.get("demolished"):
                    demo_items.append(demo_type.replace("_", " ").title())
            
            with st.expander(f"🏠 {room_name} ({floor_area:.1f} SF, Zone {zone})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    if demo_items:
                        st.write("**🔨 Demolished Items:**")
                        for item in demo_items:
                            st.write(f"• {item}")
                    else:
                        st.write("**🔨 No demolition recorded**")
                
                with col2:
                    if required_work:
                        st.write("**🔧 Required Work:**")
                        for work in required_work:
                            st.write(f"• {work}")
                    else:
                        st.write("**🔧 No work scope defined**")
                
                # Show calculated quantities if available
                if room.get("calculated_quantities"):
                    quantities = room["calculated_quantities"]
                    st.write("**📊 Calculated Quantities:**")
                    
                    quantity_items = []
                    for key, value in quantities.items():
                        if isinstance(value, (int, float)) and value > 0:
                            formatted_key = key.replace("_", " ").title()
                            if "sf" in key.lower():
                                quantity_items.append(f"{formatted_key}: {value:.1f} SF")
                            elif "lf" in key.lower():
                                quantity_items.append(f"{formatted_key}: {value:.1f} LF")
                            else:
                                quantity_items.append(f"{formatted_key}: {value:.2f}")
                    
                    if quantity_items:
                        for item in quantity_items[:5]:  # Show first 5 items
                            st.write(f"• {item}")
                        if len(quantity_items) > 5:
                            st.write(f"• ... and {len(quantity_items) - 5} more items")
    else:
        st.info("No rooms created yet.")
    
    # Validation Summary
    st.subheader("✅ Project Validation")
    
    errors = validate_project_data(project_data)
    if errors:
        st.error(f"❌ {len(errors)} validation errors found:")
        for error in errors:
            st.write(f"• {error}")
    else:
        st.success("✅ All project validations passed!")
    
    # Export Options
    st.subheader("📤 Export Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Standard JSON export (clean)
        if st.button("📥 Export Clean JSON", help="Export with only used data - smaller file size"):
            json_str = export_to_json(project_data)
            filename = generate_filename(project_data)
            
            st.download_button(
                label="📥 Download Clean JSON",
                data=json_str,
                file_name=filename,
                mime="application/json"
            )
            
            # Show file size
            file_size_kb = len(json_str.encode('utf-8')) / 1024
            st.info(f"📊 File size: {file_size_kb:.1f} KB")
    
    with col2:
        # Full JSON export (with all fields)
        if st.button("📋 Export Full JSON", help="Export with all fields including defaults"):
            # Use the original JSON export method for full data
            full_json_str = json.dumps(project_data, indent=2, ensure_ascii=False, default=str)
            filename = generate_filename(project_data).replace(".json", "_full.json")
            
            st.download_button(
                label="📋 Download Full JSON",
                data=full_json_str,
                file_name=filename,
                mime="application/json"
            )
            
            # Show file size comparison
            file_size_kb = len(full_json_str.encode('utf-8')) / 1024
            st.info(f"📊 File size: {file_size_kb:.1f} KB")
    
    # Project Statistics
    st.subheader("📈 Project Statistics")
    
    # Calculate project stats
    total_rooms = len(rooms)
    measured_rooms = sum(1 for room in rooms if room["dimensions"].get("floor_area", 0) > 0)
    rooms_with_work = sum(1 for room in rooms if any(
        isinstance(ws, dict) and ws.get("required") for ws in room.get("work_scope", {}).values()
        if ws != room.get("work_scope", {}).get("other_work", {})
    ))
    rooms_with_demo = sum(1 for room in rooms if any(
        isinstance(ds, dict) and ds.get("demolished") for ds in room.get("demolition_status", {}).values()
        if isinstance(ds, dict)
    ))
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Rooms", total_rooms)
    with col2:
        st.metric("Measured Rooms", f"{measured_rooms}/{total_rooms}")
    with col3:
        st.metric("Rooms with Work", rooms_with_work)
    with col4:
        st.metric("Rooms with Demo", rooms_with_demo)
    
    # Zone distribution
    if rooms:
        zone_counts = {}
        for room in rooms:
            zone = room.get("zone_assignment", "Unassigned")
            zone_counts[zone] = zone_counts.get(zone, 0) + 1
        
        if zone_counts:
            st.write("**🎯 Zone Distribution:**")
            zone_info = []
            for zone, count in sorted(zone_counts.items()):
                zone_info.append(f"Zone {zone}: {count} rooms")
            st.write(" | ".join(zone_info))

# Auto-calculation functions for real-time updates
def calculate_net_wall_area(current_room):
    """Calculate net wall area by subtracting openings from gross wall area"""
    wall_area_gross = current_room["dimensions"].get("wall_area_gross", 0)
    opening_sizes = current_room.get("opening_sizes", {})
    openings = current_room.get("openings", {})
    
    # Calculate total opening area that affects walls
    total_opening_area = 0
    
    # Door areas
    door_area = opening_sizes.get("door_width_ft", 3.0) * opening_sizes.get("door_height_ft", 8.0)
    total_opening_area += (openings.get("interior_doors", 0) + openings.get("exterior_doors", 0)) * door_area
    
    # Pocket door areas
    pocket_door_area = opening_sizes.get("pocket_door_width_ft", 3.0) * opening_sizes.get("door_height_ft", 8.0)
    total_opening_area += openings.get("pocket_doors", 0) * pocket_door_area
    
    # Bifold door areas
    bifold_door_area = opening_sizes.get("bifold_door_width_ft", 4.0) * opening_sizes.get("door_height_ft", 8.0)
    total_opening_area += openings.get("bifold_doors", 0) * bifold_door_area
    
    # Window areas
    window_area = opening_sizes.get("window_width_ft", 3.0) * opening_sizes.get("window_height_ft", 4.0)
    total_opening_area += openings.get("windows", 0) * window_area
    
    # Open areas
    open_area = opening_sizes.get("open_area_width_ft", 6.0) * opening_sizes.get("open_area_height_ft", 8.0)
    total_opening_area += openings.get("open_areas", 0) * open_area
    
    # Archway areas
    archway_area = opening_sizes.get("archway_width_ft", 4.0) * opening_sizes.get("archway_height_ft", 8.0)
    total_opening_area += openings.get("archways", 0) * archway_area
    
    # Pass-through areas
    pass_through_area = opening_sizes.get("pass_through_width_ft", 3.0) * opening_sizes.get("pass_through_height_ft", 2.0)
    total_opening_area += openings.get("pass_throughs", 0) * pass_through_area
    
    # Built-in areas
    built_in_area = opening_sizes.get("built_in_width_ft", 3.0) * opening_sizes.get("built_in_height_ft", 8.0)
    total_opening_area += openings.get("built_in_cabinets", 0) * built_in_area
    
    return max(0, wall_area_gross - total_opening_area)

def calculate_net_floor_perimeter(current_room):
    """Calculate net floor perimeter by subtracting door/opening widths"""
    floor_perimeter_gross = current_room["dimensions"].get("floor_perimeter", 0)
    opening_sizes = current_room.get("opening_sizes", {})
    openings = current_room.get("openings", {})
    
    # Calculate total width reduction
    total_width_reduction = 0
    
    # Door widths
    total_width_reduction += (openings.get("interior_doors", 0) + openings.get("exterior_doors", 0)) * opening_sizes.get("door_width_ft", 3.0)
    
    # Pocket door widths
    total_width_reduction += openings.get("pocket_doors", 0) * opening_sizes.get("pocket_door_width_ft", 3.0)
    
    # Bifold door widths
    total_width_reduction += openings.get("bifold_doors", 0) * opening_sizes.get("bifold_door_width_ft", 4.0)
    
    # Open area widths
    total_width_reduction += openings.get("open_areas", 0) * opening_sizes.get("open_area_width_ft", 6.0)
    
    # Archway widths
    total_width_reduction += openings.get("archways", 0) * opening_sizes.get("archway_width_ft", 4.0)
    
    return max(0, floor_perimeter_gross - total_width_reduction)


def calculate_net_ceiling_perimeter(current_room):
    """Calculate net ceiling perimeter by subtracting full-height opening widths"""
    ceiling_perimeter_gross = current_room["dimensions"].get("ceiling_perimeter", 0)
    opening_sizes = current_room.get("opening_sizes", {})
    openings = current_room.get("openings", {})
    room_height = current_room["dimensions"].get("height", 8.0)
    
    # Calculate total width reduction for full-height openings
    total_width_reduction = 0
    
    # Check if open areas are full height
    open_area_height = opening_sizes.get("open_area_height_ft", 8.0)
    if abs(open_area_height - room_height) < 0.5:  # Within 0.5 ft tolerance
        total_width_reduction += openings.get("open_areas", 0) * opening_sizes.get("open_area_width_ft", 6.0)
    
    # Check if archways are full height
    archway_height = opening_sizes.get("archway_height_ft", 8.0)
    if abs(archway_height - room_height) < 0.5:  # Within 0.5 ft tolerance
        total_width_reduction += openings.get("archways", 0) * opening_sizes.get("archway_width_ft", 4.0)
    
    return max(0, ceiling_perimeter_gross - total_width_reduction)

def calculate_net_ceiling_area(current_room):
    """Calculate net ceiling area by subtracting skylight areas"""
    ceiling_area_gross = current_room["dimensions"].get("ceiling_area_gross", 0)
    opening_sizes = current_room.get("opening_sizes", {})
    openings = current_room.get("openings", {})
    
    # Calculate skylight area
    skylight_area = opening_sizes.get("skylight_width_ft", 2.0) * opening_sizes.get("skylight_length_ft", 4.0)
    total_skylight_area = openings.get("skylights", 0) * skylight_area
    
    return max(0, ceiling_area_gross - total_skylight_area)

def room_measurements_page():
    """Room Measurements page - ENHANCED WITH BATCH IMAGE UPLOAD"""
    st.header("📏 Room Measurements")
    st.write("**Create rooms and input their measurements using various methods**")
    
    rooms = st.session_state.project_data["rooms"]
    
    # Add tabs for single vs batch processing
    tab1, tab2 = st.tabs(["📐 Single Room Entry", "📸 Batch Image Upload"])
    
    with tab1:
        # EXISTING SINGLE ROOM ENTRY CODE
        render_single_room_measurement_ui(rooms)
    
    with tab2:
        # NEW BATCH IMAGE UPLOAD FUNCTIONALITY
        render_batch_image_upload_ui(rooms)


def render_batch_image_upload_ui(rooms):
    """Render batch image upload interface"""
    st.subheader("📸 Batch Image Upload")
    st.info("Upload multiple floor plan images at once and process them together")
    
    # Check if AI analyzer is available
    if st.session_state.ai_analyzer is None:
        st.error("⚠️ OpenAI API key not configured. Please add your API key to secrets.toml")
        return
    
    # Initialize batch upload session state
    if "batch_upload_images" not in st.session_state:
        st.session_state.batch_upload_images = []
    if "batch_analysis_results" not in st.session_state:
        st.session_state.batch_analysis_results = {}
    if "batch_room_names" not in st.session_state:
        st.session_state.batch_room_names = {}
    
    # File uploader for multiple images
    uploaded_files = st.file_uploader(
        "Upload Floor Plans/Sketches",
        type=['png', 'jpg', 'jpeg'],
        accept_multiple_files=True,
        key="batch_image_uploader",
        help="Select multiple images at once"
    )
    
    if uploaded_files:
        st.write(f"📁 **{len(uploaded_files)} images uploaded**")
        
        # Process uploaded files
        if st.button("🔍 Analyze All Images", key="batch_analyze_all"):
            with st.spinner(f"Analyzing {len(uploaded_files)} images..."):
                progress_bar = st.progress(0)
                
                for idx, uploaded_file in enumerate(uploaded_files):
                    # Update progress
                    progress = (idx + 1) / len(uploaded_files)
                    progress_bar.progress(progress)
                    
                    # Generate default room name
                    default_room_name = f"Room_{idx + 1}"
                    
                    # Analyze image
                    result = st.session_state.ai_analyzer.analyze_construction_image(
                        uploaded_file,
                        default_room_name,
                        ""  # No room type hint for batch
                    )
                    
                    # Store results
                    file_id = f"{uploaded_file.name}_{idx}"
                    st.session_state.batch_analysis_results[file_id] = {
                        "file": uploaded_file,
                        "result": result,
                        "default_name": default_room_name
                    }
                    
                    # Set initial room name
                    if file_id not in st.session_state.batch_room_names:
                        # Try to extract room name from AI analysis
                        detected_name = result.get("room_identification", {}).get("detected_room_name", "")
                        if detected_name and detected_name != "Unknown":
                            st.session_state.batch_room_names[file_id] = detected_name
                        else:
                            st.session_state.batch_room_names[file_id] = default_room_name
                
                progress_bar.empty()
                st.success(f"✅ Analyzed {len(uploaded_files)} images successfully!")
        
        # Display analysis results
        if st.session_state.batch_analysis_results:
            st.subheader("📊 Analysis Results")
            
            # Create columns for compact display
            for idx, (file_id, data) in enumerate(st.session_state.batch_analysis_results.items()):
                with st.expander(f"🏠 Image {idx + 1}: {data['file'].name}", expanded=True):
                    col1, col2, col3 = st.columns([1, 1, 2])
                    
                    with col1:
                        # Show thumbnail
                        st.image(data['file'], caption="Floor Plan", use_container_width=True)
                    
                    with col2:
                        # Room name input
                        room_name = st.text_input(
                            "Room Name",
                            value=st.session_state.batch_room_names.get(file_id, data['default_name']),
                            key=f"batch_room_name_{file_id}",
                            placeholder="Enter room name"
                        )
                        st.session_state.batch_room_names[file_id] = room_name
                        
                        # Zone assignment
                        zone_options = ["A", "B", "C", "Independent"]
                        zone = st.selectbox(
                            "Zone",
                            options=zone_options,
                            key=f"batch_zone_{file_id}",
                            help="Group rooms for coordinated work"
                        )
                    
                    with col3:
                        # Display key measurements
                        result = data['result']
                        if "error" not in result:
                            st.write("**📐 Detected Measurements:**")
                            
                            # Extract key data
                            extracted_dims = result.get("extracted_dimensions", {})
                            room_geo = result.get("room_geometry", {})
                            openings_summary = result.get("openings_summary", {})
                            detailed_openings = result.get("detailed_openings", [])
                            
                            # Combine data
                            all_data = {**extracted_dims, **room_geo}
                            
                            # Display measurements
                            floor_area = all_data.get("room_area_sf") or all_data.get("floor_area_sf") or "N/A"
                            perimeter = all_data.get("perimeter_lf") or all_data.get("total_perimeter_lf") or "N/A"
                            floor_perimeter = all_data.get("floor_perimeter_lf", "N/A")
                            height = all_data.get("ceiling_height_ft") or "N/A"
                            
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.metric("Floor Area", f"{floor_area} SF")
                                st.metric("Height", f"{height} ft")
                                if floor_perimeter != "N/A" and floor_perimeter != perimeter:
                                    st.metric("Floor Perimeter", f"{floor_perimeter} LF")
                            with col_b:
                                st.metric("Perimeter", f"{perimeter} LF")
                                
                                # Total openings with detailed breakdown
                                total_doors = openings_summary.get("total_doors", 0)
                                total_windows = openings_summary.get("total_windows", 0)
                                total_openings = (
                                    total_doors +
                                    total_windows +
                                    openings_summary.get("total_open_areas", 0)
                                )
                                st.metric("Total Openings", total_openings)
                                
                                # Show detailed door/window breakdown
                                breakdown_items = []
                                int_doors = openings_summary.get("total_interior_doors", 0)
                                ext_doors = openings_summary.get("total_exterior_doors", 0)
                                
                                if int_doors > 0 or ext_doors > 0:
                                    breakdown_items.append(f"D:{int_doors}i/{ext_doors}e")
                                
                                # Count interior/exterior windows from detailed_openings
                                if detailed_openings and total_windows > 0:
                                    int_win = sum(1 for o in detailed_openings if o.get("type", "").lower() == "window" and not o.get("is_exterior", True))
                                    ext_win = sum(1 for o in detailed_openings if o.get("type", "").lower() == "window" and o.get("is_exterior", True))
                                    breakdown_items.append(f"W:{int_win}i/{ext_win}e")
                                elif total_windows > 0:
                                    breakdown_items.append(f"W:{total_windows}")
                                
                                if breakdown_items:
                                    st.caption(" | ".join(breakdown_items))
                            
                            # Confidence indicator
                            confidence = result.get("confidence_level", "medium")
                            if confidence == "high":
                                st.success(f"🎯 Confidence: {confidence}")
                            elif confidence == "medium":
                                st.warning(f"⚠️ Confidence: {confidence}")
                            else:
                                st.error(f"❌ Confidence: {confidence}")
                        else:
                            st.error(f"❌ Analysis failed: {result['error']}")
            
            # Batch actions
            st.subheader("🔧 Batch Actions")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("✅ Create All Rooms", key="batch_create_all", type="primary"):
                    created_count = 0
                    
                    for file_id, data in st.session_state.batch_analysis_results.items():
                        result = data['result']
                        if "error" not in result:
                            # Create new room
                            new_room = create_empty_room()
                            new_room["room_name"] = st.session_state.batch_room_names[file_id]
                            new_room["input_method"] = "ai_image_analysis"
                            new_room["zone_assignment"] = st.session_state.get(f"batch_zone_{file_id}", "A")
                            
                            # Store AI analysis
                            new_room["ai_analysis"] = {
                                "extracted_results": result,
                                "confidence_level": result.get("confidence_level", "medium"),
                                "user_confirmed": False
                            }
                            
                            # Apply AI data
                            extracted_dims = result.get("extracted_dimensions", {})
                            room_geo = result.get("room_geometry", {})
                            openings_summary = result.get("openings_summary", {})
                            all_data = {**extracted_dims, **room_geo}
                            
                            apply_ai_data_to_room_stable(new_room, all_data, openings_summary)
                            
                            # Add to rooms
                            rooms.append(new_room)
                            created_count += 1
                    
                    if created_count > 0:
                        st.success(f"✅ Created {created_count} rooms successfully!")
                        # Clear batch data
                        st.session_state.batch_analysis_results = {}
                        st.session_state.batch_room_names = {}
                        st.rerun()
                    else:
                        st.error("❌ No valid rooms to create")
            
            with col2:
                if st.button("📝 Review & Edit Individual", key="batch_review"):
                    st.info("💡 Rooms will be created. You can then edit each one in the Single Room Entry tab.")
            
            with col3:
                if st.button("🗑️ Clear Batch", key="batch_clear"):
                    st.session_state.batch_analysis_results = {}
                    st.session_state.batch_room_names = {}
                    st.success("✅ Batch data cleared")
                    st.rerun()
            
            # Summary table
            if st.checkbox("📊 Show Summary Table", key="batch_show_summary"):
                summary_data = []
                for file_id, data in st.session_state.batch_analysis_results.items():
                    result = data['result']
                    if "error" not in result:
                        extracted_dims = result.get("extracted_dimensions", {})
                        room_geo = result.get("room_geometry", {})
                        openings_summary = result.get("openings_summary", {})
                        detailed_openings = result.get("detailed_openings", [])
                        all_data = {**extracted_dims, **room_geo}
                        
                        # Count interior/exterior windows from detailed_openings
                        int_windows = 0
                        ext_windows = 0
                        if detailed_openings:
                            for opening in detailed_openings:
                                if opening.get("type", "").lower() == "window":
                                    if opening.get("is_exterior", True):
                                        ext_windows += 1
                                    else:
                                        int_windows += 1
                        
                        summary_data.append({
                            "Room Name": st.session_state.batch_room_names[file_id],
                            "Floor Area (SF)": all_data.get("room_area_sf") or all_data.get("floor_area_sf") or "N/A",
                            "Floor Perimeter (LF)": all_data.get("floor_perimeter_lf") or "N/A",
                            "Total Perimeter (LF)": all_data.get("perimeter_lf") or "N/A",
                            "Height (ft)": all_data.get("ceiling_height_ft") or "N/A",
                            "Int. Doors": openings_summary.get("total_interior_doors", 0),
                            "Ext. Doors": openings_summary.get("total_exterior_doors", 0),
                            "Int. Windows": int_windows,
                            "Ext. Windows": ext_windows,
                            "Confidence": result.get("confidence_level", "medium")
                        })
                
                if summary_data:
                    import pandas as pd
                    df = pd.DataFrame(summary_data)
                    st.dataframe(df, use_container_width=True, height=400)
    else:
        st.info("📸 Select multiple floor plan images to analyze them in batch")

def render_image_reference_panel(current_room, selected_room_index):
    """Helper function to display reference image in any measurement mode"""
    # Check if room has stored image data
    if current_room.get("ai_analysis", {}).get("image_data"):
        with st.expander("📸 Reference Image", expanded=False):
            try:
                import base64
                from io import BytesIO
                from PIL import Image
                
                # Decode stored image
                image_data = base64.b64decode(current_room["ai_analysis"]["image_data"])
                image = Image.open(BytesIO(image_data))
                
                # Create two columns for image and info
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.image(image, 
                            caption=f"Floor Plan: {current_room['ai_analysis'].get('image_name', 'Unknown')}", 
                            use_container_width=True)
                
                with col2:
                    st.write("**Image Info:**")
                    st.write(f"• Name: {current_room['ai_analysis'].get('image_name', 'N/A')}")
                    
                    # Show analysis confidence if available
                    confidence = current_room['ai_analysis'].get('confidence_level', 'N/A')
                    if confidence != 'N/A':
                        if confidence == "high":
                            st.success(f"• Confidence: {confidence}")
                        elif confidence == "medium":
                            st.warning(f"• Confidence: {confidence}")
                        else:
                            st.error(f"• Confidence: {confidence}")
                    
                    # Show if this is AI analyzed
                    if current_room.get("input_method") in ["ai_image_analysis", "ai_manual_edit"]:
                        st.info("🤖 AI Analyzed")
                        
            except Exception as e:
                st.warning(f"Could not display reference image: {str(e)}")
    
    # Also check session state for current image
    elif f"uploaded_image_{selected_room_index}" in st.session_state and st.session_state[f"uploaded_image_{selected_room_index}"] is not None:
        with st.expander("📸 Reference Image", expanded=False):
            st.image(st.session_state[f"uploaded_image_{selected_room_index}"], 
                    caption="Current Upload", 
                    use_container_width=True)

def render_single_room_measurement_ui(rooms):
    """Render single room measurement UI (existing functionality)"""
    # Room management
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.subheader("📋 Room Management")
    
    with col2:
        if st.button("➕ Add New Room", key="add_room_measurements_page"):
            new_room = create_empty_room()
            rooms.append(new_room)
            st.session_state.current_room_index = len(rooms) - 1
            st.success(f"✅ Added Room {len(rooms)}")
            st.rerun()
    
    with col3:
        if rooms and st.button("🗑️ Delete Current Room", key="delete_room_measurements_page"):
            if len(rooms) > 0:
                deleted_room_name = rooms[st.session_state.current_room_index].get("room_name", f"Room {st.session_state.current_room_index + 1}")
                rooms.pop(st.session_state.current_room_index)
                st.session_state.current_room_index = max(0, min(st.session_state.current_room_index, len(rooms) - 1))
                st.success(f"✅ Deleted {deleted_room_name}")
                st.rerun()
    
    if not rooms:
        st.info("📏 No rooms created yet. Click 'Add New Room' to start measuring rooms.")
        return
    
    # Room selector
    room_names = [f"Room {i+1}: {room.get('room_name', 'Unnamed')}" for i, room in enumerate(rooms)]
    selected_room_index = st.selectbox(
        "Select Room to Measure",
        options=range(len(rooms)),
        format_func=lambda i: room_names[i],
        index=st.session_state.current_room_index,
        key="room_selector_measurements"
    )
    st.session_state.current_room_index = selected_room_index
    
    current_room = rooms[selected_room_index]
    
    # Ensure room data structures are initialized
    initialize_room_data_structures(current_room)
    
    # Room basic information
    st.subheader(f"📐 Room #{selected_room_index + 1} Basic Information")
    
    # Show AI measurement info
    is_ai_analyzed = (
        current_room.get("input_method") in ["ai_image_analysis", "ai_manual_edit"] or
        current_room.get("dimensions", {}).get("ai_initialized", False) or
        current_room.get("ai_analysis", {}).get("user_confirmed", False)
    )
    
    if is_ai_analyzed:
        st.info("🤖 **AI Analyzed Room** - Complex shapes supported. Length/width validation skipped.")
    else:
        st.info("📐 **Manual Input Room** - Requires length and width values for validation.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        current_room["room_name"] = st.text_input(
            "Room Name",
            value=current_room.get("room_name", ""),
            key=f"room_name_{selected_room_index}",
            help="Enter a descriptive name like 'Master Bathroom' or 'Living Room'"
        )
        
        # Zone Assignment
        st.write("**Zone Assignment** 🔗")
        with st.expander("ℹ️ What is Zone Assignment?"):
            st.write("""
            **Zone Assignment groups connected rooms for work continuity:**
            
            **🏠 Zone A**: Main living areas (Living Room, Kitchen, Dining)
            **🛏️ Zone B**: Master suite (Master Bedroom, Master Bath)
            **👥 Zone C**: Guest areas (Guest bedrooms, shared bathrooms)
            **🔧 Independent**: Standalone spaces (Basement, Garage, Utility)
            """)
        
        zone_options = ["A", "B", "C", "Independent"]
        current_zone = current_room.get("zone_assignment", "A")
        zone_index = 0
        if current_zone in zone_options:
            zone_index = zone_options.index(current_zone)
        
        current_room["zone_assignment"] = st.selectbox(
            "Select Zone",
            options=zone_options,
            index=zone_index,
            key=f"zone_measurements_{selected_room_index}",
            help="Group this room with others that need coordinated work"
        )
    
    with col2:
        # Input Method Selection - SESSION STATE DRIVEN
        input_methods = get_room_input_methods()
        
        # Ensure ai_manual_edit is available in the options
        method_codes = [method[0] for method in input_methods]
        if "ai_manual_edit" not in method_codes:
            input_methods.append(("ai_manual_edit", "✏️ AI Analysis + Manual Editing"))
        
        current_input_method = current_room.get("input_method", "simple_rectangular")
        
        # Check if we're switching to manual edit mode from session state (BEFORE selectbox)
        edit_mode_key = f"switch_to_manual_edit_{selected_room_index}"
        if edit_mode_key in st.session_state and st.session_state[edit_mode_key]:
            # Force switch to manual edit mode
            current_input_method = "ai_manual_edit"
            current_room["input_method"] = "ai_manual_edit"
            
            # Initialize ai_analysis for manual editing
            if "ai_analysis" not in current_room:
                current_room["ai_analysis"] = {}
            current_room["ai_analysis"]["manual_editing"] = True
            current_room["ai_analysis"]["user_confirmed"] = False
            
            # Initialize all required data structures
            initialize_room_data_structures(current_room)
            
            # Clear the session state flag
            del st.session_state[edit_mode_key]
            
            # Show success message
            st.success("🎯 **Switched to AI Manual Edit Mode!**")
        
        input_method_index = 0
        for i, method in enumerate(input_methods):
            if method[0] == current_input_method:
                input_method_index = i
                break
        
        # Selectbox with current method (will reflect the ai_manual_edit if switched)
        selected_input_method = st.selectbox(
            "Measurement Input Method",
            options=[method[0] for method in input_methods],
            format_func=lambda x: next(method[1] for method in input_methods if method[0] == x),
            index=input_method_index,
            key=f"input_method_measurements_{selected_room_index}"
        )
        
        # Apply the selected method (this will be ai_manual_edit if switched above)
        current_room["input_method"] = selected_input_method
        
        # Show method descriptions
        method_descriptions = {
            "ai_image_analysis": "🤖 Best for floor plans - AI reads dimensions automatically",
            "simple_rectangular": "📐 For basic rectangular rooms - Enter length × width",
            "complex_manual": "🔧 For L-shaped, T-shaped, or irregular rooms",
            "standard_template": "📋 Use pre-defined room templates",
            "ai_manual_edit": "✏️ AI analysis + manual editing"
        }
        
        current_method = current_room["input_method"]
        if current_method in method_descriptions:
            st.info(method_descriptions[current_method])
    
    # Measurement Input Sections - CLEAN ROUTING
    st.subheader("📏 Room Dimensions Input")
    
    if current_room.get("input_method") == "ai_manual_edit":
        render_ai_manual_edit_mode_stable(current_room, selected_room_index)
    elif current_room["input_method"] == "ai_image_analysis":
        render_ai_image_analysis_mode_stable(current_room, selected_room_index)
    elif current_room["input_method"] == "simple_rectangular":
        render_simple_rectangular_mode_stable(current_room, selected_room_index)
    elif current_room["input_method"] == "complex_manual":
        render_complex_manual_mode_stable(current_room, selected_room_index)
    elif current_room["input_method"] == "standard_template":
        render_standard_template_mode_stable(current_room, selected_room_index)
    
    # Measurement Summary
    render_measurement_summary_stable(current_room, rooms)

def render_ai_manual_edit_mode_stable(current_room, selected_room_index):
    """Render AI Manual Edit Mode with Image Reference"""
    st.success("🎯 **AI Manual Edit Mode Active**")
    st.info("🤖 **Started with AI values** - Now you can adjust all measurements and openings")
    
    # DISPLAY REFERENCE IMAGE - NEW ADDITION
    render_image_reference_panel(current_room, selected_room_index)
    
    # Ensure all required data structures exist
    initialize_room_data_structures(current_room)
    
    # Manual dimension editing - REPLACED WITH ROOM DIMENSIONS EDITING
    st.subheader("📐 Room Dimensions Editing")
    st.info("🤖 **Edit the AI-detected room measurements directly**")
    
    # Initialize room dimensions with AI data if available
    ai_results = current_room.get("ai_analysis", {}).get("extracted_results", {})
    if ai_results and not current_room["dimensions"].get("ai_initialized"):
        # Extract comprehensive data from AI analysis
        extracted_dims = ai_results.get("extracted_dimensions", {})
        room_geo = ai_results.get("room_geometry", {})
        room_id = ai_results.get("room_identification", {})
        all_ai_data = {**extracted_dims, **room_geo, **room_id}
        
        # Apply AI data to room dimensions
        if all_ai_data.get("floor_area_sf") or all_ai_data.get("room_area_sf"):
            current_room["dimensions"]["floor_area"] = float(all_ai_data.get("floor_area_sf") or all_ai_data.get("room_area_sf") or 112.0)
        if all_ai_data.get("wall_area_sf"):
            current_room["dimensions"]["wall_area"] = float(all_ai_data.get("wall_area_sf", 0))
            current_room["dimensions"]["wall_area_gross"] = float(all_ai_data.get("wall_area_sf", 0))
        if all_ai_data.get("ceiling_area_sf"):
            current_room["dimensions"]["ceiling_area"] = float(all_ai_data.get("ceiling_area_sf", 0))
            current_room["dimensions"]["ceiling_area_gross"] = float(all_ai_data.get("ceiling_area_sf", 0))
        if all_ai_data.get("perimeter_lf") or all_ai_data.get("total_perimeter_lf"):
            perimeter_val = float(all_ai_data.get("perimeter_lf") or all_ai_data.get("total_perimeter_lf") or 40.0)
            current_room["dimensions"]["perimeter_gross"] = perimeter_val
            current_room["dimensions"]["floor_perimeter"] = perimeter_val
        if all_ai_data.get("ceiling_perimeter_lf"):
            current_room["dimensions"]["ceiling_perimeter"] = float(all_ai_data.get("ceiling_perimeter_lf", 0))
        else:
            # Use floor perimeter as default for ceiling perimeter
            current_room["dimensions"]["ceiling_perimeter"] = current_room["dimensions"].get("floor_perimeter", 40.0)
        if all_ai_data.get("ceiling_height_ft"):
            current_room["dimensions"]["height"] = float(all_ai_data.get("ceiling_height_ft", 8.0))
        
        # Store room shape and type info
        if all_ai_data.get("room_shape"):
            current_room["dimensions"]["room_shape"] = all_ai_data.get("room_shape", "rectangular")
        if all_ai_data.get("detected_room_name"):
            current_room["dimensions"]["room_type"] = all_ai_data.get("detected_room_name", "Unknown")
        
        # Mark as AI initialized to prevent re-initialization
        current_room["dimensions"]["ai_initialized"] = True
    
    # Room Type and Shape (read-only info from AI)
    col1, col2 = st.columns(2)
    with col1:
        room_type = current_room["dimensions"].get("room_type", "Unknown")
        st.info(f"🏠 **Room Type**: {room_type}")
    with col2:
        room_shape = current_room["dimensions"].get("room_shape", "rectangular")
        st.info(f"📐 **Shape**: {room_shape.replace('_', ' ').title()}")
    
    # Editable Room Dimensions
    st.write("**📏 Edit Room Measurements:**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Floor & Ceiling**")
        
        new_floor_area = st.number_input(
            "Floor Area (SF)",
            min_value=0.0,
            max_value=10000.0,
            value=float(current_room["dimensions"].get("floor_area", 112.0)),
            step=0.1,
            key=f"ai_floor_area_{selected_room_index}",
            help="Total floor area in square feet"
        )
        current_room["dimensions"]["floor_area"] = new_floor_area
        
        new_ceiling_area_gross = st.number_input(
            "Ceiling Area (Gross) (SF)",
            min_value=0.0,
            max_value=10000.0,
            value=float(current_room["dimensions"].get("ceiling_area_gross", new_floor_area)),
            step=0.1,
            key=f"ai_ceiling_area_gross_{selected_room_index}",
            help="Total ceiling area before skylight deductions"
        )
        current_room["dimensions"]["ceiling_area_gross"] = new_ceiling_area_gross
        
        new_height = st.number_input(
            "Room Height (ft)",
            min_value=7.0,
            max_value=20.0,
            value=float(current_room["dimensions"].get("height", 9.0)),
            step=0.1,
            key=f"ai_room_height_{selected_room_index}",
            help="Floor to ceiling height"
        )
        current_room["dimensions"]["height"] = new_height
    
    with col2:
        st.write("**Wall Areas**")
        
        new_wall_area_gross = st.number_input(
            "Wall Area (Gross) (SF)",
            min_value=0.0,
            max_value=10000.0,
            value=float(current_room["dimensions"].get("wall_area_gross", 423.0)),
            step=0.1,
            key=f"ai_wall_area_gross_{selected_room_index}",
            help="Total wall area before door/window deductions"
        )
        current_room["dimensions"]["wall_area_gross"] = new_wall_area_gross
        
        # Wall area net will be calculated automatically based on openings
        calculated_wall_net = calculate_net_wall_area(current_room)
        current_room["dimensions"]["wall_area"] = calculated_wall_net
        
        st.metric("Wall Area (Net)", f"{calculated_wall_net:.1f} SF", 
                 help="Gross wall area minus doors, windows, and openings")
    
    with col3:
        st.write("**Perimeters**")
        
        new_floor_perimeter = st.number_input(
            "Floor Perimeter (Gross) (LF)",
            min_value=0.0,
            max_value=1000.0,
            value=float(current_room["dimensions"].get("floor_perimeter", 40.0)),
            step=0.1,
            key=f"ai_floor_perimeter_{selected_room_index}",
            help="Total floor perimeter before opening deductions"
        )
        current_room["dimensions"]["floor_perimeter"] = new_floor_perimeter
        current_room["dimensions"]["perimeter_gross"] = new_floor_perimeter  # Keep compatibility
        
        new_ceiling_perimeter = st.number_input(
            "Ceiling Perimeter (LF)",
            min_value=0.0,
            max_value=1000.0,
            value=float(current_room["dimensions"].get("ceiling_perimeter", new_floor_perimeter)),
            step=0.1,
            key=f"ai_ceiling_perimeter_{selected_room_index}",
            help="Ceiling perimeter (usually same as floor unless vaulted)"
        )
        current_room["dimensions"]["ceiling_perimeter"] = new_ceiling_perimeter
        
        # Net perimeters will be calculated automatically
        calculated_floor_net = calculate_net_floor_perimeter(current_room)
        calculated_ceiling_net = calculate_net_ceiling_perimeter(current_room)
        
        current_room["dimensions"]["floor_perimeter_net"] = calculated_floor_net
        current_room["dimensions"]["ceiling_perimeter_net"] = calculated_ceiling_net
        current_room["dimensions"]["perimeter_net"] = calculated_floor_net  # Keep compatibility
        
        st.metric("Floor Perimeter (Net)", f"{calculated_floor_net:.1f} LF",
                 help="Gross floor perimeter minus door and opening widths")
        st.metric("Ceiling Perimeter (Net)", f"{calculated_ceiling_net:.1f} LF",
                 help="Ceiling perimeter minus full-height openings")
    
    # Manual openings editing - ENHANCED WITH AI CONTEXT
    st.subheader("🚪 Openings & Features Editing")
    
    # Show AI analysis context if available
    ai_results = current_room.get("ai_analysis", {}).get("extracted_results", {})
    if ai_results:
        with st.expander("🤖 AI Analysis Reference"):
            openings_summary = ai_results.get("openings_summary", {})
            detailed_openings = ai_results.get("detailed_openings", [])
            
            if openings_summary:
                st.write("**AI Detected Openings:**")
                for key, value in openings_summary.items():
                    if value > 0:
                        formatted_key = key.replace("total_", "").replace("_", " ").title()
                        st.write(f"• {formatted_key}: {value}")
            
            if detailed_openings:
                st.write("**Detailed Openings:**")
                for i, opening in enumerate(detailed_openings):
                    opening_type = opening.get("type", "Unknown")
                    width = opening.get("width_ft", 0)
                    height = opening.get("height_ft", 0)
                    st.write(f"• {opening_type}: {width:.1f}' × {height:.1f}'")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**🚪 Standard Openings**")
        
        current_room["openings"]["interior_doors"] = st.number_input(
            "Interior Doors",
            min_value=0,
            value=current_room["openings"].get("interior_doors", 1),
            key=f"ai_manual_int_doors_{selected_room_index}",
            help="Doors connecting to other interior rooms"
        )
        
        current_room["openings"]["exterior_doors"] = st.number_input(
            "Exterior Doors",
            min_value=0,
            value=current_room["openings"].get("exterior_doors", 0),
            key=f"ai_manual_ext_doors_{selected_room_index}",
            help="Doors leading outside"
        )
        
        current_room["openings"]["windows"] = st.number_input(
            "Windows",
            min_value=0,
            value=current_room["openings"].get("windows", 1),
            key=f"ai_manual_windows_{selected_room_index}",
            help="Wall-mounted windows"
        )
        
        # Advanced door types
        with st.expander("🔧 Advanced Door Types"):
            current_room["openings"]["pocket_doors"] = st.number_input(
                "Pocket Doors",
                min_value=0,
                value=current_room["openings"].get("pocket_doors", 0),
                key=f"ai_manual_pocket_doors_{selected_room_index}",
                help="Sliding pocket doors"
            )
            
            current_room["openings"]["bifold_doors"] = st.number_input(
                "Bifold Doors",
                min_value=0,
                value=current_room["openings"].get("bifold_doors", 0),
                key=f"ai_manual_bifold_doors_{selected_room_index}",
                help="Folding closet doors"
            )
    
    with col2:
        st.write("**🏠 Special Openings**")
        
        current_room["openings"]["open_areas"] = st.number_input(
            "Open Areas (to other rooms)",
            min_value=0,
            value=current_room["openings"].get("open_areas", 0),
            key=f"ai_manual_open_areas_{selected_room_index}",
            help="Openings without doors/windows (e.g., pass-through to kitchen)"
        )
        
        current_room["openings"]["skylights"] = st.number_input(
            "Skylights (Ceiling Windows)",
            min_value=0,
            value=current_room["openings"].get("skylights", 0),
            key=f"ai_manual_skylights_{selected_room_index}",
            help="Windows in the ceiling"
        )
        
        # Built-in features
        current_room["openings"]["built_in_cabinets"] = st.number_input(
            "Built-in Cabinets/Shelving",
            min_value=0,
            value=current_room["openings"].get("built_in_cabinets", 0),
            key=f"ai_manual_built_ins_{selected_room_index}",
            help="Built-in storage features"
        )
        
        # Specialty openings
        with st.expander("🔧 Specialty Openings"):
            current_room["openings"]["archways"] = st.number_input(
                "Archways",
                min_value=0,
                value=current_room["openings"].get("archways", 0),
                key=f"ai_manual_archways_{selected_room_index}",
                help="Decorative arched openings"
            )
            
            current_room["openings"]["pass_throughs"] = st.number_input(
                "Pass-Through Windows",
                min_value=0,
                value=current_room["openings"].get("pass_throughs", 0),
                key=f"ai_manual_pass_throughs_{selected_room_index}",
                help="Kitchen pass-through windows"
            )
        
        # Calculate and show total openings
        total_openings = (
            current_room["openings"].get("interior_doors", 0) + 
            current_room["openings"].get("exterior_doors", 0) + 
            current_room["openings"].get("windows", 0) + 
            current_room["openings"].get("open_areas", 0) + 
            current_room["openings"].get("skylights", 0) +
            current_room["openings"].get("pocket_doors", 0) +
            current_room["openings"].get("bifold_doors", 0) +
            current_room["openings"].get("built_in_cabinets", 0) +
            current_room["openings"].get("archways", 0) +
            current_room["openings"].get("pass_throughs", 0)
        )
        st.metric("Total Openings", total_openings)
    
    # Enhanced Opening Sizes Section
    st.write("**📐 Opening Sizes (for area calculations)**")
    st.info("📏 Customize the size of each opening type for accurate area calculations")
    
    # Initialize opening sizes with more categories
    if "opening_sizes" not in current_room:
        current_room["opening_sizes"] = {}
    
    opening_sizes = current_room["opening_sizes"]
    
    # Set defaults for all opening types
    size_defaults = {
        "door_width_ft": 3.0, "door_height_ft": 8.0,
        "window_width_ft": 3.0, "window_height_ft": 4.0,
        "open_area_width_ft": 6.0, "open_area_height_ft": 8.0,
        "skylight_width_ft": 2.0, "skylight_length_ft": 4.0,
        "pocket_door_width_ft": 3.0, "pocket_door_height_ft": 8.0,
        "bifold_door_width_ft": 4.0, "bifold_door_height_ft": 8.0,
        "built_in_width_ft": 3.0, "built_in_height_ft": 8.0,
        "archway_width_ft": 4.0, "archway_height_ft": 8.0,
        "pass_through_width_ft": 3.0, "pass_through_height_ft": 2.0
    }
    
    # Apply defaults for missing keys
    for key, default_value in size_defaults.items():
        if key not in opening_sizes:
            opening_sizes[key] = default_value
    
    # Tabbed interface for opening sizes
    tab1, tab2, tab3 = st.tabs(["🚪 Doors & Windows", "🏠 Special Features", "📊 Size Summary"])
    
    with tab1:
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.write("**🚪 Door Sizes**")
            opening_sizes["door_width_ft"] = st.number_input(
                "Standard Door Width (ft)",
                min_value=1.0,
                max_value=10.0,
                value=float(opening_sizes.get("door_width_ft", 3.0)),
                step=0.1,
                key=f"ai_door_width_{selected_room_index}"
            )
            
            opening_sizes["door_height_ft"] = st.number_input(
                "Standard Door Height (ft)",
                min_value=6.0,
                max_value=12.0,
                value=float(opening_sizes.get("door_height_ft", 8.0)),
                step=0.1,
                key=f"ai_door_height_{selected_room_index}"
            )
            
            opening_sizes["pocket_door_width_ft"] = st.number_input(
                "Pocket Door Width (ft)",
                min_value=1.0,
                max_value=10.0,
                value=float(opening_sizes.get("pocket_door_width_ft", 3.0)),
                step=0.1,
                key=f"ai_pocket_door_width_{selected_room_index}"
            )
            
            opening_sizes["bifold_door_width_ft"] = st.number_input(
                "Bifold Door Width (ft)",
                min_value=2.0,
                max_value=12.0,
                value=float(opening_sizes.get("bifold_door_width_ft", 4.0)),
                step=0.1,
                key=f"ai_bifold_door_width_{selected_room_index}"
            )
        
        with col_b:
            st.write("**🪟 Window Sizes**")
            opening_sizes["window_width_ft"] = st.number_input(
                "Window Width (ft)",
                min_value=1.0,
                max_value=15.0,
                value=float(opening_sizes.get("window_width_ft", 3.0)),
                step=0.1,
                key=f"ai_window_width_{selected_room_index}"
            )
            
            opening_sizes["window_height_ft"] = st.number_input(
                "Window Height (ft)",
                min_value=1.0,
                max_value=10.0,
                value=float(opening_sizes.get("window_height_ft", 4.0)),
                step=0.1,
                key=f"ai_window_height_{selected_room_index}"
            )
            
            opening_sizes["skylight_width_ft"] = st.number_input(
                "Skylight Width (ft)",
                min_value=1.0,
                max_value=8.0,
                value=float(opening_sizes.get("skylight_width_ft", 2.0)),
                step=0.1,
                key=f"ai_skylight_width_{selected_room_index}"
            )
            
            opening_sizes["skylight_length_ft"] = st.number_input(
                "Skylight Length (ft)",
                min_value=1.0,
                max_value=10.0,
                value=float(opening_sizes.get("skylight_length_ft", 4.0)),
                step=0.1,
                key=f"ai_skylight_length_{selected_room_index}"
            )
    
    with tab2:
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.write("**🏠 Open Areas**")
            opening_sizes["open_area_width_ft"] = st.number_input(
                "Open Area Width (ft)",
                min_value=1.0,
                max_value=20.0,
                value=float(opening_sizes.get("open_area_width_ft", 6.0)),
                step=0.1,
                key=f"ai_open_area_width_{selected_room_index}"
            )
            
            opening_sizes["open_area_height_ft"] = st.number_input(
                "Open Area Height (ft)",
                min_value=6.0,
                max_value=12.0,
                value=float(opening_sizes.get("open_area_height_ft", 8.0)),
                step=0.1,
                key=f"ai_open_area_height_{selected_room_index}"
            )
            
            opening_sizes["archway_width_ft"] = st.number_input(
                "Archway Width (ft)",
                min_value=2.0,
                max_value=15.0,
                value=float(opening_sizes.get("archway_width_ft", 4.0)),
                step=0.1,
                key=f"ai_archway_width_{selected_room_index}"
            )
            
            opening_sizes["archway_height_ft"] = st.number_input(
                "Archway Height (ft)",
                min_value=6.0,
                max_value=12.0,
                value=float(opening_sizes.get("archway_height_ft", 8.0)),
                step=0.1,
                key=f"ai_archway_height_{selected_room_index}"
            )
        
        with col_b:
            st.write("**🔧 Built-ins & Features**")
            opening_sizes["built_in_width_ft"] = st.number_input(
                "Built-in Width (ft)",
                min_value=1.0,
                max_value=12.0,
                value=float(opening_sizes.get("built_in_width_ft", 3.0)),
                step=0.1,
                key=f"ai_built_in_width_{selected_room_index}"
            )
            
            opening_sizes["built_in_height_ft"] = st.number_input(
                "Built-in Height (ft)",
                min_value=2.0,
                max_value=10.0,
                value=float(opening_sizes.get("built_in_height_ft", 8.0)),
                step=0.1,
                key=f"ai_built_in_height_{selected_room_index}"
            )
            
            opening_sizes["pass_through_width_ft"] = st.number_input(
                "Pass-Through Width (ft)",
                min_value=1.0,
                max_value=8.0,
                value=float(opening_sizes.get("pass_through_width_ft", 3.0)),
                step=0.1,
                key=f"ai_pass_through_width_{selected_room_index}"
            )
            
            opening_sizes["pass_through_height_ft"] = st.number_input(
                "Pass-Through Height (ft)",
                min_value=1.0,
                max_value=6.0,
                value=float(opening_sizes.get("pass_through_height_ft", 2.0)),
                step=0.1,
                key=f"ai_pass_through_height_{selected_room_index}"
            )
    
    with tab3:
        st.write("**📊 Opening Areas Summary**")
        
        # Calculate total areas for each opening type
        opening_areas = {}
        opening_areas["standard_doors"] = (
            (current_room["openings"].get("interior_doors", 0) + 
             current_room["openings"].get("exterior_doors", 0)) *
            opening_sizes["door_width_ft"] * opening_sizes["door_height_ft"]
        )
        
        opening_areas["windows"] = (
            current_room["openings"].get("windows", 0) *
            opening_sizes["window_width_ft"] * opening_sizes["window_height_ft"]
        )
        
        opening_areas["open_areas"] = (
            current_room["openings"].get("open_areas", 0) *
            opening_sizes["open_area_width_ft"] * opening_sizes["open_area_height_ft"]
        )
        
        opening_areas["skylights"] = (
            current_room["openings"].get("skylights", 0) *
            opening_sizes["skylight_width_ft"] * opening_sizes["skylight_length_ft"]
        )
        
        opening_areas["pocket_doors"] = (
            current_room["openings"].get("pocket_doors", 0) *
            opening_sizes["pocket_door_width_ft"] * opening_sizes["door_height_ft"]
        )
        
        opening_areas["bifold_doors"] = (
            current_room["openings"].get("bifold_doors", 0) *
            opening_sizes["bifold_door_width_ft"] * opening_sizes["door_height_ft"]
        )
        
        # Display areas in columns
        col1, col2 = st.columns(2)
        
        with col1:
            for key, area in opening_areas.items():
                if area > 0:
                    display_name = key.replace("_", " ").title()
                    st.metric(f"{display_name} Area", f"{area:.1f} SF")
        
        with col2:
            total_opening_area = sum(opening_areas.values())
            st.metric("Total Opening Area", f"{total_opening_area:.1f} SF")
            
            # Store calculated areas for use in calculations
            current_room["calculated_opening_areas"] = opening_areas
    
    # Control buttons - UPDATED FOR ROOM DIMENSIONS
    st.subheader("🔧 Manual Edit Controls")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Recalculate All Areas", key=f"recalc_all_areas_{selected_room_index}"):
            # Force recalculation of all net values
            current_room["dimensions"]["wall_area"] = calculate_net_wall_area(current_room)
            current_room["dimensions"]["ceiling_area"] = calculate_net_ceiling_area(current_room)
            current_room["dimensions"]["floor_perimeter_net"] = calculate_net_floor_perimeter(current_room)
            current_room["dimensions"]["ceiling_perimeter_net"] = calculate_net_ceiling_perimeter(current_room)
            current_room["dimensions"]["perimeter_net"] = current_room["dimensions"]["floor_perimeter_net"]
            
            # Force save to session state
            st.session_state.project_data["rooms"][selected_room_index] = current_room
            st.success("✅ All areas and perimeters recalculated!")
            st.rerun()
    
    with col2:
        if st.button("🤖 Back to AI Mode", key=f"back_to_ai_{selected_room_index}"):
            current_room["input_method"] = "ai_image_analysis"
            if "ai_analysis" in current_room:
                current_room["ai_analysis"]["manual_editing"] = False
            st.success("✅ Switched back to AI analysis mode")
            st.rerun()
    
    with col3:
        if st.button("✅ Confirm Manual Changes", key=f"ai_confirm_manual_{selected_room_index}"):
            if "ai_analysis" not in current_room:
                current_room["ai_analysis"] = {}
            current_room["ai_analysis"]["manual_editing"] = False
            current_room["ai_analysis"]["user_confirmed"] = True
            current_room["ai_analysis"]["manually_edited"] = True
            
            # Final calculation and save
            current_room["dimensions"]["wall_area"] = calculate_net_wall_area(current_room)
            current_room["dimensions"]["ceiling_area"] = calculate_net_ceiling_area(current_room)
            current_room["dimensions"]["floor_perimeter_net"] = calculate_net_floor_perimeter(current_room)
            current_room["dimensions"]["ceiling_perimeter_net"] = calculate_net_ceiling_perimeter(current_room)
            current_room["dimensions"]["perimeter_net"] = current_room["dimensions"]["floor_perimeter_net"]
            
            # Save the final dimensions to session state
            st.session_state.project_data["rooms"][selected_room_index] = current_room
            
            st.success("✅ Manual changes confirmed and saved!")
            st.rerun()
    
    # Show current measurements - ENHANCED FOR NEW STRUCTURE
    if current_room["dimensions"].get("floor_area", 0) > 0:
        st.subheader("📊 Current Room Measurements")
        
        # Basic info row
        col1, col2, col3 = st.columns(3)
        with col1:
            floor_area = current_room["dimensions"]["floor_area"]
            st.metric("Floor Area", f"{floor_area:.1f} SF")
            
            # Room type and shape
            room_type = current_room["dimensions"].get("room_type", "Unknown")
            room_shape = current_room["dimensions"].get("room_shape", "rectangular")
            st.info(f"🏠 {room_type} | 📐 {room_shape.title()}")
        
        with col2:
            height = current_room["dimensions"].get("height", 8.0)
            st.metric("Room Height", f"{height:.1f} ft")
            
            # Total openings
            total_openings = (
                current_room["openings"].get("interior_doors", 0) + 
                current_room["openings"].get("exterior_doors", 0) + 
                current_room["openings"].get("windows", 0) + 
                current_room["openings"].get("open_areas", 0) + 
                current_room["openings"].get("skylights", 0) +
                current_room["openings"].get("pocket_doors", 0) +
                current_room["openings"].get("bifold_doors", 0) +
                current_room["openings"].get("built_in_cabinets", 0) +
                current_room["openings"].get("archways", 0) +
                current_room["openings"].get("pass_throughs", 0)
            )
            st.metric("Total Openings", total_openings)
        
        with col3:
            # Show confidence level if available
            ai_results = current_room.get("ai_analysis", {}).get("extracted_results", {})
            confidence = ai_results.get("confidence_level", "unknown")
            if confidence != "unknown":
                if confidence == "high":
                    st.success(f"🎯 **Confidence**: {confidence.title()}")
                elif confidence == "medium":
                    st.warning(f"⚠️ **Confidence**: {confidence.title()}")
                else:
                    st.error(f"❌ **Confidence**: {confidence.title()}")
        
        # Detailed measurements
        st.write("**📏 Detailed Measurements:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Wall Information**")
            wall_area_gross = current_room["dimensions"].get("wall_area_gross", 0)
            wall_area_net = current_room["dimensions"].get("wall_area", 0)
            
            if wall_area_gross > 0:
                st.metric("Wall Area (Gross)", f"{wall_area_gross:.1f} SF")
                st.metric("Wall Area (Net)", f"{wall_area_net:.1f} SF", 
                         f"-{wall_area_gross - wall_area_net:.1f} SF from openings")
            
            st.write("**Floor Perimeter**")
            floor_perimeter_gross = current_room["dimensions"].get("floor_perimeter", 0)
            floor_perimeter_net = current_room["dimensions"].get("floor_perimeter_net", 0)
            
            if floor_perimeter_gross > 0:
                st.metric("Floor Perimeter (Gross)", f"{floor_perimeter_gross:.1f} LF")
                st.metric("Floor Perimeter (Net)", f"{floor_perimeter_net:.1f} LF",
                         f"-{floor_perimeter_gross - floor_perimeter_net:.1f} LF from doors/openings")
        
        with col2:
            st.write("**Ceiling Information**")
            ceiling_area_gross = current_room["dimensions"].get("ceiling_area_gross", 0)
            ceiling_area_net = current_room["dimensions"].get("ceiling_area", 0)
            
            if ceiling_area_gross > 0:
                st.metric("Ceiling Area (Gross)", f"{ceiling_area_gross:.1f} SF")
                st.metric("Ceiling Area (Net)", f"{ceiling_area_net:.1f} SF",
                         f"-{ceiling_area_gross - ceiling_area_net:.1f} SF from skylights" if ceiling_area_gross != ceiling_area_net else None)
            
            st.write("**Ceiling Perimeter**")
            ceiling_perimeter_gross = current_room["dimensions"].get("ceiling_perimeter", 0)
            ceiling_perimeter_net = current_room["dimensions"].get("ceiling_perimeter_net", 0)
            
            if ceiling_perimeter_gross > 0:
                st.metric("Ceiling Perimeter (Gross)", f"{ceiling_perimeter_gross:.1f} LF")
                st.metric("Ceiling Perimeter (Net)", f"{ceiling_perimeter_net:.1f} LF",
                         f"-{ceiling_perimeter_gross - ceiling_perimeter_net:.1f} LF from full-height openings" if ceiling_perimeter_gross != ceiling_perimeter_net else None)
        
        st.success("✅ Room measurements complete with real-time calculations!")

def render_ai_image_analysis_mode_stable(current_room, selected_room_index):
    """Render AI Image Analysis Mode - ENHANCED WITH PERSISTENT IMAGE"""
    st.write("**🤖 AI Image Analysis**")
    
    if st.session_state.ai_analyzer is None:
        st.error("⚠️ OpenAI API key not configured. Please add your API key to secrets.toml")
        return
    
    # Initialize session state for uploaded image if not exists
    image_key = f"uploaded_image_{selected_room_index}"
    if image_key not in st.session_state:
        st.session_state[image_key] = None
    
    col1, col2 = st.columns(2)
    
    with col1:
        uploaded_image = st.file_uploader(
            "Upload Floor Plan/Sketch",
            type=['png', 'jpg', 'jpeg'],
            key=f"image_upload_{selected_room_index}"
        )
        
        # Store uploaded image in session state
        if uploaded_image is not None:
            st.session_state[image_key] = uploaded_image
        
        room_type_hint = st.selectbox(
            "Room Type Hint",
            options=["", "bathroom", "kitchen", "bedroom", "living", "office", "other"],
            key=f"room_type_measurements_{selected_room_index}"
        )
    
    with col2:
        # Display image from session state
        if st.session_state[image_key] is not None:
            st.image(st.session_state[image_key], caption="Uploaded Image", use_container_width=True)
            
            if st.button("🔍 Analyze Image", key=f"analyze_{selected_room_index}"):
                with st.spinner("Analyzing image..."):
                    result = st.session_state.ai_analyzer.analyze_construction_image(
                        st.session_state[image_key], 
                        current_room.get("room_name", ""),
                        room_type_hint
                    )
                    
                    if "error" in result:
                        st.error(f"Analysis failed: {result['error']}")
                    else:
                        if "ai_analysis" not in current_room:
                            current_room["ai_analysis"] = {}
                        current_room["ai_analysis"]["extracted_results"] = result
                        current_room["ai_analysis"]["confidence_level"] = result.get("confidence_level", "medium")
                        
                        # Store image data with results for future reference
                        try:
                            import base64
                            from io import BytesIO
                            
                            # Convert uploaded file to base64
                            bytes_data = st.session_state[image_key].getvalue()
                            encoded_image = base64.b64encode(bytes_data).decode()
                            current_room["ai_analysis"]["image_data"] = encoded_image
                            current_room["ai_analysis"]["image_name"] = st.session_state[image_key].name
                        except Exception as e:
                            st.warning(f"Could not store image data: {str(e)}")
                        
                        st.success("✅ Analysis complete!")
            
            # Clear image button
            if st.button("🗑️ Clear Image", key=f"clear_image_{selected_room_index}"):
                st.session_state[image_key] = None
                if "ai_analysis" in current_room and "image_data" in current_room["ai_analysis"]:
                    del current_room["ai_analysis"]["image_data"]
                    del current_room["ai_analysis"]["image_name"]
                st.rerun()
        
        # If no current upload but we have stored image data, show it
        elif current_room.get("ai_analysis", {}).get("image_data"):
            try:
                import base64
                from io import BytesIO
                from PIL import Image
                
                # Decode stored image
                image_data = base64.b64decode(current_room["ai_analysis"]["image_data"])
                image = Image.open(BytesIO(image_data))
                
                st.image(image, caption=f"Previously Analyzed: {current_room['ai_analysis'].get('image_name', 'Unknown')}", 
                        use_container_width=True)
                
                # Restore to session state button
                if st.button("📷 Use This Image", key=f"restore_image_{selected_room_index}"):
                    # Convert back to uploadedfile-like object
                    buffered = BytesIO()
                    image.save(buffered, format="PNG")
                    buffered.seek(0)
                    st.session_state[image_key] = buffered
                    st.rerun()
                    
            except Exception as e:
                st.warning(f"Could not display stored image: {str(e)}")
    
    # Display AI results and confirmation
    if current_room.get("ai_analysis", {}).get("extracted_results"):
        results = current_room["ai_analysis"]["extracted_results"]
        
        st.write("**📊 AI Extracted Results**")
        
        # JSON Toggle
        show_json = st.checkbox("🔍 Show Raw JSON Data", key=f"show_json_ai_{selected_room_index}")
        if show_json:
            with st.expander("📋 Complete AI Analysis JSON", expanded=True):
                st.json(results)
        
        # Extract data from multiple possible locations
        extracted_dims = results.get("extracted_dimensions", {})
        room_geo = results.get("room_geometry", {})
        room_id = results.get("room_identification", {})
        openings_summary = results.get("openings_summary", {})
        detailed_openings = results.get("detailed_openings", [])
        wall_segments = results.get("wall_segments", [])
        
        # Combine all available dimensional data
        all_data = {**extracted_dims, **room_geo, **room_id}
        
        # Enhanced results display
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**📐 Room Dimensions:**")
            
            # Basic room info
            detected_room_name = all_data.get("detected_room_name", "Unknown")
            room_shape = all_data.get("room_shape", "rectangular")
            st.write(f"• **Room Type**: {detected_room_name}")
            st.write(f"• **Shape**: {room_shape.replace('_', ' ').title()}")
            
            # Areas
            floor_area = (all_data.get("total_floor_area_sf") or 
                        all_data.get("floor_area_sf") or 
                        all_data.get("room_area_sf") or "N/A")
            wall_area_gross = (all_data.get("wall_area_gross_sf") or 
                             all_data.get("total_wall_area_sf") or "N/A")
            wall_area_net = (all_data.get("wall_area_net_sf") or 
                           all_data.get("wall_area_sf") or "N/A")
            ceiling_area = (all_data.get("ceiling_area_sf") or 
                          all_data.get("total_ceiling_area_sf") or floor_area)
            
            st.write(f"• **Floor Area**: {floor_area} SF")
            if wall_area_gross != "N/A":
                st.write(f"• **Wall Area (Gross)**: {wall_area_gross} SF")
            if wall_area_net != "N/A" and wall_area_net != wall_area_gross:
                st.write(f"• **Wall Area (Net)**: {wall_area_net} SF")
            elif wall_area_net != "N/A":
                st.write(f"• **Wall Area**: {wall_area_net} SF")
            if ceiling_area != "N/A":
                st.write(f"• **Ceiling Area**: {ceiling_area} SF")
            
            # Perimeters - Enhanced with floor_perimeter_lf
            perimeter_gross = (all_data.get("perimeter_lf") or 
                             all_data.get("total_perimeter_lf") or 
                             all_data.get("wall_perimeter_lf") or "N/A")
            floor_perimeter = all_data.get("floor_perimeter_lf", "N/A")
            perimeter_net = (all_data.get("perimeter_net_lf") or 
                           all_data.get("wall_perimeter_net_lf") or "N/A")
            ceiling_perimeter = (all_data.get("ceiling_perimeter_lf") or perimeter_gross)
            
            if perimeter_gross != "N/A":
                st.write(f"• **Perimeter (Gross)**: {perimeter_gross} LF")
            if floor_perimeter != "N/A" and floor_perimeter != perimeter_gross:
                st.write(f"• **Floor Perimeter**: {floor_perimeter} LF")
            if perimeter_net != "N/A" and perimeter_net != perimeter_gross:
                st.write(f"• **Perimeter (Net)**: {perimeter_net} LF")
            if ceiling_perimeter != "N/A" and ceiling_perimeter != perimeter_gross:
                st.write(f"• **Ceiling Perimeter**: {ceiling_perimeter} LF")
            
            # Dimensions
            height = (all_data.get("ceiling_height_ft") or 
                    all_data.get("height_ft") or "N/A")
            length = (all_data.get("room_length_ft") or 
                    all_data.get("length_ft") or "N/A")
            width = (all_data.get("room_width_ft") or 
                   all_data.get("width_ft") or "N/A")
            
            st.write(f"• **Height**: {height} ft")
            if length != "N/A":
                st.write(f"• **Length**: {length} ft")
            if width != "N/A":
                st.write(f"• **Width**: {width} ft")
        
        with col2:
            st.write("**🚪 Openings & Features:**")
            
            # Enhanced openings display with window separation
            if openings_summary:
                # Door information
                total_doors = openings_summary.get("total_doors", 0)
                interior_doors = openings_summary.get("total_interior_doors", 0)
                exterior_doors = openings_summary.get("total_exterior_doors", 0)
                
                st.write(f"• **Total Doors**: {total_doors}")
                if interior_doors > 0 or exterior_doors > 0:
                    st.write(f"  - Interior: {interior_doors}")
                    st.write(f"  - Exterior: {exterior_doors}")
                
                # Window information - Enhanced with interior/exterior separation
                total_windows = openings_summary.get("total_windows", 0)
                window_area = openings_summary.get("window_area_total_sf", 0)
                
                # Count interior and exterior windows from detailed_openings
                interior_windows = 0
                exterior_windows = 0
                interior_window_area = 0
                exterior_window_area = 0
                
                if detailed_openings:
                    for opening in detailed_openings:
                        if opening.get("type", "").lower() == "window":
                            is_exterior = opening.get("is_exterior", True)
                            area = opening.get("area_sf", 0)
                            if is_exterior:
                                exterior_windows += 1
                                exterior_window_area += area
                            else:
                                interior_windows += 1
                                interior_window_area += area
                
                st.write(f"• **Windows**: {total_windows}")
                if exterior_windows > 0 or interior_windows > 0:
                    if exterior_windows > 0:
                        st.write(f"  - Exterior: {exterior_windows}")
                        if exterior_window_area > 0:
                            st.write(f"    Area: {exterior_window_area:.1f} SF")
                    if interior_windows > 0:
                        st.write(f"  - Interior: {interior_windows}")
                        if interior_window_area > 0:
                            st.write(f"    Area: {interior_window_area:.1f} SF")
                elif window_area > 0:
                    st.write(f"  - Total Area: {window_area:.1f} SF")
                
                # Open areas
                open_areas = openings_summary.get("total_open_areas", 0)
                open_area_width = openings_summary.get("open_area_width_total_ft", 0)
                open_area_total_sf = openings_summary.get("open_area_total_sf", 0)
                
                if open_areas > 0:
                    st.write(f"• **Open Areas**: {open_areas}")
                    if open_area_width > 0:
                        st.write(f"  - Total Width: {open_area_width:.1f} ft")
                    if open_area_total_sf > 0:
                        st.write(f"  - Total Area: {open_area_total_sf:.1f} SF")
                
                # Special features
                skylights = openings_summary.get("total_skylights", 0)
                if skylights > 0:
                    st.write(f"• **Skylights**: {skylights}")
                
                built_ins = openings_summary.get("built_in_features", 0)
                if built_ins > 0:
                    st.write(f"• **Built-in Features**: {built_ins}")
            
            # Wall segments summary
            if wall_segments:
                st.write(f"• **Wall Segments**: {len(wall_segments)}")
                
                with st.expander("🔍 Wall Segments Details"):
                    for i, wall in enumerate(wall_segments):
                        orientation = wall.get("orientation", "unknown")
                        wall_length = wall.get("length_ft", 0)
                        wall_doors = len(wall.get("doors", []))
                        wall_windows = len(wall.get("windows", []))
                        wall_openings = len(wall.get("open_areas", []))
                        
                        st.write(f"**Wall {i+1}**: {orientation.title()}")
                        st.write(f"  - Length: {wall_length:.1f} ft")
                        if wall_doors > 0:
                            st.write(f"  - Doors: {wall_doors}")
                        if wall_windows > 0:
                            st.write(f"  - Windows: {wall_windows}")
                        if wall_openings > 0:
                            st.write(f"  - Openings: {wall_openings}")
            
            # Detailed openings
            if detailed_openings:
                with st.expander("🔍 Detailed Openings Analysis"):
                    for i, opening in enumerate(detailed_openings):
                        opening_type = opening.get("type", "Unknown")
                        width = opening.get("width_ft", 0)
                        height = opening.get("height_ft", 0)
                        area = opening.get("area_sf", 0)
                        connects_to = opening.get("connects_to", "Unknown")
                        is_exterior = opening.get("is_exterior", False)
                        
                        st.write(f"**Opening {i+1}**: {opening_type}")
                        if width > 0:
                            st.write(f"  - Size: {width:.1f} ft × {height:.1f} ft")
                        if area > 0:
                            st.write(f"  - Area: {area:.1f} SF")
                        if connects_to != "Unknown":
                            st.write(f"  - Connects to: {connects_to}")
                        st.write(f"  - Type: {'Exterior' if is_exterior else 'Interior'}")
        
        # Analysis quality indicators
        confidence = results.get("confidence_level", "medium")
        analysis_notes = results.get("analysis_notes", "")
        
        col1, col2 = st.columns(2)
        with col1:
            if confidence == "high":
                st.success(f"🎯 **Analysis Confidence: {confidence.title()}**")
            elif confidence == "medium":
                st.warning(f"⚠️ **Analysis Confidence: {confidence.title()}**")
            else:
                st.error(f"❌ **Analysis Confidence: {confidence.title()} - Manual verification recommended**")
        
        with col2:
            if analysis_notes:
                st.info(f"📝 **Analysis Notes**: {analysis_notes}")
                
            # Show image type if available
            image_type = results.get("room_identification", {}).get("image_type", "")
            if image_type:
                st.info(f"🖼️ **Image Type**: {image_type.replace('_', ' ').title()}")
        
        # Technical details and calculated materials
        technical_details = results.get("technical_details", {})
        calculated_materials = results.get("calculated_materials", {})
        
        if calculated_materials:
            with st.expander("📊 AI Calculated Materials"):
                st.write("**Material quantities calculated by AI:**")
                
                flooring_area = calculated_materials.get("flooring_area_sf", 0)
                if flooring_area > 0:
                    st.write(f"• **Flooring Area**: {flooring_area} SF")
                
                wall_paint_area = calculated_materials.get("wall_paint_area_sf", 0)
                if wall_paint_area > 0:
                    st.write(f"• **Wall Paint Area**: {wall_paint_area} SF")
                
                ceiling_paint_area = calculated_materials.get("ceiling_paint_area_sf", 0)
                if ceiling_paint_area > 0:
                    st.write(f"• **Ceiling Paint Area**: {ceiling_paint_area} SF")
                
                baseboard_length = calculated_materials.get("baseboard_length_lf", 0)
                if baseboard_length > 0:
                    st.write(f"• **Baseboard Length**: {baseboard_length} LF")
                
                crown_molding_length = calculated_materials.get("crown_molding_length_lf", 0)
                if crown_molding_length > 0:
                    st.write(f"• **Crown Molding Length**: {crown_molding_length} LF")
        
        if technical_details:
            with st.expander("🔧 Technical Analysis Details"):
                for key, value in technical_details.items():
                    st.write(f"**{key.replace('_', ' ').title()}**: {value}")
        
        # Room features
        room_features = results.get("room_features", {})
        if room_features:
            with st.expander("🏠 Detected Room Features"):
                for feature_type, features in room_features.items():
                    if features:
                        st.write(f"**{feature_type.replace('_', ' ').title()}**:")
                        if isinstance(features, list):
                            for feature in features:
                                st.write(f"  • {feature}")
                        else:
                            st.write(f"  • {features}")
        
        # Confirmation buttons - SESSION STATE APPROACH
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirm and Apply", key=f"confirm_ai_{selected_room_index}"):
                apply_ai_data_to_room_stable(current_room, all_data, openings_summary)
                current_room["ai_analysis"]["user_confirmed"] = True
                st.success("✅ AI measurements applied!")
                # NO st.rerun() - let natural rerun handle it
        
        with col2:
            # SESSION STATE APPROACH - CLEAN RERUN
            if st.button("✏️ Edit Manually", key=f"override_ai_{selected_room_index}"):
                # Set session state flag for mode change
                edit_mode_key = f"switch_to_manual_edit_{selected_room_index}"
                st.session_state[edit_mode_key] = True
                
                # Apply AI data as starting values
                apply_ai_data_to_room_stable(current_room, all_data, openings_summary)
                
                # Now rerun to trigger the mode change
                st.rerun()

def apply_ai_data_to_room_stable(current_room, all_data, openings_summary):
    """Apply AI analysis data to room structure - UPDATED FOR PROVIDED JSON STRUCTURE"""
    # Ensure data structures exist
    initialize_room_data_structures(current_room)
    
    # Extract comprehensive AI data from the provided JSON structure
    ai_results = current_room.get("ai_analysis", {}).get("extracted_results", {})
    extracted_dims = ai_results.get("extracted_dimensions", {})
    room_geo = ai_results.get("room_geometry", {})
    room_id = ai_results.get("room_identification", {})
    
    # Combine data with priority: extracted_dimensions > room_geometry > room_identification > all_data
    comprehensive_data = {**all_data, **room_id, **room_geo, **extracted_dims}
    
    # Set room type and shape information
    detected_room_name = comprehensive_data.get("detected_room_name", "Unknown")
    if detected_room_name and detected_room_name != "Unknown":
        current_room["dimensions"]["room_type"] = detected_room_name
    
    room_shape = comprehensive_data.get("room_shape", "rectangular")
    if room_shape:
        current_room["dimensions"]["room_shape"] = room_shape
    
    # Set height
    ceiling_height = comprehensive_data.get("ceiling_height_ft", 8.0)
    current_room["dimensions"]["height"] = max(float(ceiling_height), 7.0)
    
    # Set floor area - prioritize room_area_sf, then floor_area_sf, then total_floor_area_sf
    floor_area = (comprehensive_data.get("room_area_sf") or 
                 comprehensive_data.get("floor_area_sf") or 
                 comprehensive_data.get("total_floor_area_sf") or 0)
    
    if floor_area and float(floor_area) > 0:
        current_room["dimensions"]["floor_area"] = float(floor_area)
    
    # Set wall areas - use wall_area_sf as gross wall area
    wall_area_sf = comprehensive_data.get("wall_area_sf", 0)
    if wall_area_sf > 0:
        current_room["dimensions"]["wall_area_gross"] = float(wall_area_sf)
        current_room["dimensions"]["wall_area"] = float(wall_area_sf)  # Initial value, will be recalculated
    
    # Set ceiling areas - use ceiling_area_sf as gross ceiling area
    ceiling_area_sf = comprehensive_data.get("ceiling_area_sf", 0)
    if ceiling_area_sf > 0:
        current_room["dimensions"]["ceiling_area_gross"] = float(ceiling_area_sf)
        current_room["dimensions"]["ceiling_area"] = float(ceiling_area_sf)  # Initial value, will be recalculated
    elif floor_area > 0:
        # Use floor area as default for ceiling area
        current_room["dimensions"]["ceiling_area_gross"] = float(floor_area)
        current_room["dimensions"]["ceiling_area"] = float(floor_area)
    
    # Set perimeters - ENHANCED WITH PROVIDED JSON STRUCTURE
    # Floor perimeter
    perimeter_lf = (comprehensive_data.get("perimeter_lf") or 
                   comprehensive_data.get("total_perimeter_lf") or 0)
    
    if perimeter_lf > 0:
        current_room["dimensions"]["floor_perimeter"] = float(perimeter_lf)
        current_room["dimensions"]["perimeter_gross"] = float(perimeter_lf)  # Compatibility
    
    # Ceiling perimeter - may be different from floor perimeter
    ceiling_perimeter_lf = comprehensive_data.get("ceiling_perimeter_lf", 0)
    if ceiling_perimeter_lf > 0:
        current_room["dimensions"]["ceiling_perimeter"] = float(ceiling_perimeter_lf)
    elif perimeter_lf > 0:
        # Use floor perimeter as default for ceiling perimeter
        current_room["dimensions"]["ceiling_perimeter"] = float(perimeter_lf)
    
    # Enhanced openings processing based on provided JSON structure
    if openings_summary:
        # Standard openings from the JSON structure
        current_room["openings"]["interior_doors"] = openings_summary.get("total_interior_doors", 0)
        current_room["openings"]["exterior_doors"] = openings_summary.get("total_exterior_doors", 0)
        current_room["openings"]["windows"] = openings_summary.get("total_windows", 0)
        current_room["openings"]["open_areas"] = openings_summary.get("total_open_areas", 0)
        current_room["openings"]["skylights"] = openings_summary.get("total_skylights", 0)
        
        # Advanced openings (if detected in future versions)
        current_room["openings"]["pocket_doors"] = openings_summary.get("total_pocket_doors", 0)
        current_room["openings"]["bifold_doors"] = openings_summary.get("total_bifold_doors", 0)
        current_room["openings"]["built_in_cabinets"] = openings_summary.get("built_in_features", 0)
        current_room["openings"]["archways"] = openings_summary.get("total_archways", 0)
        current_room["openings"]["pass_throughs"] = openings_summary.get("total_pass_throughs", 0)
        
        # Store opening areas if available from JSON
        if openings_summary.get("window_area_total_sf") or openings_summary.get("door_width_total_ft"):
            current_room["ai_detected_areas"] = {
                "window_area_total": openings_summary.get("window_area_total_sf", 0),
                "door_width_total": openings_summary.get("door_width_total_ft", 0),
                "open_area_width_total": openings_summary.get("open_area_width_total_ft", 0)
            }
    
    # Store calculated materials if available from JSON
    calculated_materials = ai_results.get("calculated_materials", {})
    if calculated_materials:
        current_room["ai_calculated_materials"] = {
            "baseboard_length_lf": calculated_materials.get("baseboard_length_lf", 0),
            "crown_molding_length_lf": calculated_materials.get("crown_molding_length_lf", 0),
            "flooring_area_sf": calculated_materials.get("flooring_area_sf", 0),
            "wall_paint_area_sf": calculated_materials.get("wall_paint_area_sf", 0),
            "ceiling_paint_area_sf": calculated_materials.get("ceiling_paint_area_sf", 0)
        }
    
    # Calculate initial net values after applying AI data
    current_room["dimensions"]["wall_area"] = calculate_net_wall_area(current_room)
    current_room["dimensions"]["ceiling_area"] = calculate_net_ceiling_area(current_room)
    current_room["dimensions"]["floor_perimeter_net"] = calculate_net_floor_perimeter(current_room)
    current_room["dimensions"]["ceiling_perimeter_net"] = calculate_net_ceiling_perimeter(current_room)
    current_room["dimensions"]["perimeter_net"] = current_room["dimensions"]["floor_perimeter_net"]  # Compatibility
    
    # Store original AI data for reference with enhanced structure
    from datetime import datetime
    current_room["ai_analysis"]["applied_data"] = {
        "extracted_dimensions": extracted_dims,
        "room_geometry": room_geo, 
        "room_identification": room_id,
        "openings_summary": openings_summary,
        "calculated_materials": calculated_materials,
        "confidence_level": comprehensive_data.get("confidence_level", "medium"),
        "analysis_notes": comprehensive_data.get("analysis_notes", ""),
        "dimension_source": comprehensive_data.get("dimension_source", "ai_analysis"),
        "applied_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Mark as AI initialized
    current_room["dimensions"]["ai_initialized"] = True


def render_simple_rectangular_mode_stable(current_room, selected_room_index):
    """Render Simple Rectangular Mode - STABLE VERSION"""
    st.write("**📐 Simple Rectangular Room**")

    # DISPLAY REFERENCE IMAGE IF AVAILABLE
    render_image_reference_panel(current_room, selected_room_index)
    
    # Ensure data structures exist
    initialize_room_data_structures(current_room)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        current_room["dimensions"]["length"] = st.number_input(
            "Length (ft)",
            min_value=0.0,
            max_value=100.0,
            value=float(current_room["dimensions"].get("length", 0.0)),
            step=0.1,
            key=f"length_{selected_room_index}"
        )
    
    with col2:
        current_room["dimensions"]["width"] = st.number_input(
            "Width (ft)",
            min_value=0.0,
            max_value=100.0,
            value=float(current_room["dimensions"].get("width", 0.0)),
            step=0.1,
            key=f"width_{selected_room_index}"
        )
    
    with col3:
        current_height = current_room["dimensions"].get("height", 8.0)
        if current_height < 7.0:
            current_height = 8.0
        
        current_room["dimensions"]["height"] = st.number_input(
            "Height (ft)",
            min_value=7.0,
            max_value=20.0,
            value=float(current_height),
            step=0.1,
            key=f"height_{selected_room_index}"
        )
    
    # Auto-calculate areas
    length = current_room["dimensions"]["length"]
    width = current_room["dimensions"]["width"]
    height = current_room["dimensions"]["height"]
    
    if length > 0 and width > 0:
        floor_area = length * width
        perimeter = 2 * (length + width)
        wall_area = perimeter * height
        
        current_room["dimensions"]["floor_area"] = floor_area
        current_room["dimensions"]["wall_area"] = wall_area
        current_room["dimensions"]["ceiling_area"] = floor_area
        current_room["dimensions"]["perimeter_gross"] = perimeter
        
        st.success(f"📐 **Calculated:** Floor: {floor_area:.1f} SF | Wall: {wall_area:.1f} SF | Perimeter: {perimeter:.1f} LF")
    
    # Openings
    st.write("**🚪 Room Openings**")
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


def render_complex_manual_mode_stable(current_room, selected_room_index):
    """Render Complex Manual Mode - STABLE VERSION"""
    st.write("**🔧 Complex Room Shape**")
    st.info("For L-shaped, T-shaped, or irregular rooms")

    # DISPLAY REFERENCE IMAGE IF AVAILABLE
    render_image_reference_panel(current_room, selected_room_index)
    
    # Ensure data structures exist
    initialize_room_data_structures(current_room)
    
    current_room["dimensions"]["floor_area_manual"] = st.number_input(
        "Actual Floor Area (SF)",
        min_value=0.0,
        value=float(current_room["dimensions"].get("floor_area_manual", 0)),
        step=0.1,
        key=f"manual_area_{selected_room_index}",
        help="Enter known measurement from blueprints or field measurement"
    )
    
    if current_room["dimensions"]["floor_area_manual"] > 0:
        current_room["dimensions"]["floor_area"] = current_room["dimensions"]["floor_area_manual"]
        
        equivalent_side = (current_room["dimensions"]["floor_area_manual"] ** 0.5)
        current_room["dimensions"]["length"] = equivalent_side
        current_room["dimensions"]["width"] = equivalent_side
        
        height = st.number_input(
            "Ceiling Height (ft)",
            min_value=7.0,
            max_value=20.0,
            value=float(current_room["dimensions"].get("height", 8.0)),
            step=0.1,
            key=f"complex_height_{selected_room_index}"
        )
        current_room["dimensions"]["height"] = height
        
        estimated_perimeter = 4 * equivalent_side
        current_room["dimensions"]["wall_area"] = estimated_perimeter * height
        current_room["dimensions"]["ceiling_area"] = current_room["dimensions"]["floor_area_manual"]
        current_room["dimensions"]["perimeter_gross"] = estimated_perimeter
        
        st.success(f"📐 **Set:** Floor: {current_room['dimensions']['floor_area_manual']:.1f} SF")


def render_standard_template_mode_stable(current_room, selected_room_index):
    """Render Standard Template Mode - STABLE VERSION"""
    st.write("**📋 Standard Room Templates**")

    # DISPLAY REFERENCE IMAGE IF AVAILABLE 
    render_image_reference_panel(current_room, selected_room_index)
    
    room_templates = {
        "small_bathroom": {"length": 5.0, "width": 8.0, "height": 8.0, "doors": 1, "windows": 1},
        "master_bathroom": {"length": 10.0, "width": 12.0, "height": 9.0, "doors": 1, "windows": 1},
        "kitchen": {"length": 10.0, "width": 14.0, "height": 9.0, "doors": 2, "windows": 2},
        "living_room": {"length": 14.0, "width": 20.0, "height": 9.0, "doors": 2, "windows": 3},
        "bedroom": {"length": 10.0, "width": 12.0, "height": 8.0, "doors": 1, "windows": 2},
        "master_bedroom": {"length": 14.0, "width": 16.0, "height": 9.0, "doors": 2, "windows": 2}
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_template = st.selectbox(
            "Choose Room Template",
            options=list(room_templates.keys()),
            format_func=lambda x: x.replace("_", " ").title(),
            key=f"template_measurements_{selected_room_index}"
        )
        
        if st.button("📋 Apply Template", key=f"apply_template_measurements_{selected_room_index}"):
            template = room_templates[selected_template]
            
            # Ensure data structures exist
            initialize_room_data_structures(current_room)
            
            # Apply template data
            current_room["dimensions"]["length"] = template["length"]
            current_room["dimensions"]["width"] = template["width"]
            current_room["dimensions"]["height"] = template["height"]
            current_room["openings"]["interior_doors"] = template["doors"]
            current_room["openings"]["windows"] = template["windows"]
            
            # Calculate areas
            floor_area = template["length"] * template["width"]
            perimeter = 2 * (template["length"] + template["width"])
            wall_area = perimeter * template["height"]
            
            current_room["dimensions"]["floor_area"] = floor_area
            current_room["dimensions"]["wall_area"] = wall_area
            current_room["dimensions"]["ceiling_area"] = floor_area
            current_room["dimensions"]["perimeter_gross"] = perimeter
            
            # Auto-name room if unnamed
            if not current_room.get("room_name"):
                current_room["room_name"] = selected_template.replace("_", " ").title()
            
            st.success(f"✅ Applied {selected_template.replace('_', ' ').title()} template!")
            # NO st.rerun() - let natural rerun handle it
    
    with col2:
        if selected_template:
            template = room_templates[selected_template]
            st.write(f"**{selected_template.replace('_', ' ').title()} Template:**")
            st.write(f"• Dimensions: {template['length']}' × {template['width']}' × {template['height']}'")
            st.write(f"• Floor Area: {template['length'] * template['width']:.1f} SF")
            st.write(f"• Doors: {template['doors']} | Windows: {template['windows']}")


def render_measurement_summary_stable(current_room, rooms):
    """Render measurement summary - STABLE VERSION"""
    # Measurement Summary
    if current_room["dimensions"].get("floor_area", 0) > 0:
        st.subheader("📊 Room Measurement Summary")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Floor Area", f"{current_room['dimensions']['floor_area']:.1f} SF")
            st.metric("Wall Area", f"{current_room['dimensions'].get('wall_area', 0):.1f} SF")
        
        with col2:
            st.metric("Ceiling Area", f"{current_room['dimensions'].get('ceiling_area', 0):.1f} SF")  
            st.metric("Perimeter", f"{current_room['dimensions'].get('perimeter_gross', 0):.1f} LF")
        
        with col3:
            st.metric("Height", f"{current_room['dimensions'].get('height', 8.0):.1f} ft")
            
            # Calculate total openings including all types  
            total_openings = (
                current_room["openings"].get("interior_doors", 0) + 
                current_room["openings"].get("exterior_doors", 0) + 
                current_room["openings"].get("windows", 0) + 
                current_room["openings"].get("open_areas", 0) + 
                current_room["openings"].get("skylights", 0) +
                current_room["openings"].get("pocket_doors", 0) +
                current_room["openings"].get("bifold_doors", 0) +
                current_room["openings"].get("built_in_cabinets", 0) +
                current_room["openings"].get("archways", 0) +
                current_room["openings"].get("pass_throughs", 0)
            )
            st.metric("Total Openings", total_openings)
        
        st.success("✅ Room measurements complete!")
    else:
        st.warning("⚠️ Room measurements not complete. Please input dimensions above.")
    
    # Rooms Summary
    st.subheader("🏠 All Rooms Summary")
    
    if rooms:
        measured_rooms = []
        unmeasured_rooms = []
        
        for i, room in enumerate(rooms):
            room_name = room.get("room_name", f"Room {i+1}")
            floor_area = room["dimensions"].get("floor_area", 0)
            
            if floor_area > 0:
                measured_rooms.append(f"✅ {room_name}: {floor_area:.1f} SF")
            else:
                unmeasured_rooms.append(f"❌ {room_name}: Not measured")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if measured_rooms:
                st.write("**✅ Measured Rooms:**")
                for room in measured_rooms:
                    st.write(f"• {room}")
            else:
                st.write("**No rooms measured yet**")
        
        with col2:
            if unmeasured_rooms:
                st.write("**❌ Unmeasured Rooms:**")
                for room in unmeasured_rooms:
                    st.write(f"• {room}")
            else:
                st.write("**All rooms measured! ✅**")
        
        # Total area
        total_area = sum(room["dimensions"].get("floor_area", 0) for room in rooms)
        if total_area > 0:
            st.info(f"🏠 **Total Project Area**: {total_area:.1f} SF across {len(measured_rooms)} measured rooms")
    else:
        st.info("📏 No rooms created yet. Click 'Add New Room' to start.")

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
    elif selected_page == "📏 Room Measurements":
        room_measurements_page()
    elif selected_page == "🔨 Work Data Entry":
        work_data_entry_page()
    elif selected_page == "📊 Summary & Export":
        summary_export_page()
    
    # Footer
    st.markdown("---")
    st.markdown("**Reconstruction Intake Form v3.0** | Enhanced with AI Image Analysis")

if __name__ == "__main__":
    main()