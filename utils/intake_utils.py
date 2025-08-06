"""
Enhanced utility functions for the Reconstruction Intake Form v3.0
- Complete JSON filtering to remove ALL unused default values
- Paint waste factor removed
- Support for all new data structures including demolition_status
"""

import json
import streamlit as st
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple


def create_empty_project() -> Dict[str, Any]:
    """Create an empty project data structure"""
    return {
        "property_info": {
            "property_address": "",
            "contractor_address": "",
            "photos_url": "",
            "claim_number": "",
            "adjuster": "",
            "construction_year": "",
            "primary_damage_source": "",
            "primary_impact_rooms": "",
            "secondary_impact_areas": "",
            "created_date": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat()
        },
        "project_coordination": {
            "other_contractors": [],
            "work_sequence_dependencies": []
        },
        "work_zones": {
            "content_manipulation_strategy": "",
            "floor_continuity_zones": [],
            "paint_continuity_zones": []
        },
        "project_standards": {
            "standard_ceiling_height": 8.0,
            "building_level": "ground",
            "access_conditions": "normal",
            "standard_drywall": "1/2\"",
            "flooring_default": "match_existing",
            "standard_baseboard": "3.5\"",
            "quarter_round": True,
            "paint_scope_default": "walls_and_ceiling"
        },
        "work_packages": {
            "selected_packages": []
        },
        "rooms": [],
        "room_connectivity": [],
        "protection_matrix": {}
    }


def create_empty_room() -> Dict[str, Any]:
    """Create an empty room data structure"""
    return {
        "room_name": "",
        "zone_assignment": "",
        "input_method": "simple_rectangular",
        "ai_analysis": {
            "uploaded_image": None,
            "room_type_hint": "",
            "extracted_results": {},
            "confidence_level": "",
            "user_confirmed": False
        },
        "dimensions": {
            "length": 0.0,
            "width": 0.0,
            "height": 0.0,
            "floor_area": 0.0,
            "wall_area": 0.0,
            "ceiling_area": 0.0
        },
        "openings": {
            "interior_doors": 1,
            "exterior_doors": 0,
            "windows": 1
        },
        "current_conditions": {
            "mitigation_status": "no_demo",
            "flooring_removed": {"status": "none", "quantity": 0},
            "drywall_removed": {"status": "none", "quantity": 0, "height": 0},
            "insulation_removed": {"status": "none", "quantity": 0},
            "trim_removed": {"status": "none", "quantity": 0},
            "structural_issues": "none",
            "structural_details": ""
        },
        "material_specifications": {
            "flooring_override": "",
            "flooring_grade": "",
            "wall_finish_override": "",
            "wall_texture": "",
            "ceiling_override": "",
            "ceiling_height_override": 0.0,
            "baseboard_override": "",
            "quarter_round_override": None,
            "complex_materials": {
                "multi_layer_flooring": False,
                "mixed_wall_materials": False,
                "specialty_ceiling": False,
                "details": ""
            }
        },
        "work_scope": {
            "flooring": {"required": False, "type": "", "extent": "full", "quantity": 0},
            "drywall": {"required": False, "extent": "full_room", "quantity": 0},
            "insulation": {"required": False, "type": "", "r_value": "", "quantity": 0},
            "trim_baseboard": {"required": False, "extent": "full_perimeter", "quantity": 0},
            "paint": {"required": False, "scope": "walls_and_ceiling", "quantity": 0},
            "electrical": {"required": False, "details": ""},
            "plumbing": {"required": False, "details": ""},
            "built_ins": {"action": "none", "details": ""},
            "hvac": {"required": False, "details": ""}
        },
        "special_conditions": {
            "access_protection": {
                "heavy_furniture": False,
                "delicate_items": False,
                "limited_access": False,
                "work_around_items": ""
            },
            "room_features": {
                "stairs": {"present": False, "type": "", "details": ""},
                "high_ceilings": {"present": False, "height": 0},
                "skylights": {"present": False, "quantity": 0, "work_needed": ""},
                "fireplace": {"present": False, "action": ""},
                "built_in_storage": {"present": False, "linear_feet": 0, "action": ""}
            }
        },
        "calculated_quantities": {},
        "auto_justifications": {},
        "validation_status": {
            "errors": [],
            "warnings": [],
            "is_valid": False
        }
    }


def initialize_room_data_structures(current_room):
    """Initialize all required room data structures - ENHANCED WITH NEW STRUCTURE"""
    if "dimensions" not in current_room:
        current_room["dimensions"] = {
            "length": 10.0, 
            "width": 12.0, 
            "height": 8.0, 
            "floor_area": 120.0,
            "wall_area": 0.0,
            "wall_area_gross": 0.0,
            "ceiling_area": 0.0,
            "ceiling_area_gross": 0.0,
            "perimeter_gross": 0.0,  # Compatibility
            "perimeter_net": 0.0,    # Compatibility
            "floor_perimeter": 0.0,  # Floor perimeter
            "floor_perimeter_net": 0.0,  # Net floor perimeter
            "ceiling_perimeter": 0.0,  # Ceiling perimeter
            "ceiling_perimeter_net": 0.0,  # Net ceiling perimeter
            "room_type": "Unknown",  # Room type from AI
            "room_shape": "rectangular",  # Room shape from AI
            "ai_initialized": False  # NEW: Track if AI data has been applied
        }
    
    # Ensure new fields exist in existing dimensions
    required_dimension_fields = {
        "floor_perimeter": 0.0,
        "floor_perimeter_net": 0.0,
        "ceiling_perimeter": 0.0,
        "ceiling_perimeter_net": 0.0,
        "room_type": "Unknown",
        "room_shape": "rectangular",
        "ai_initialized": False,
        "wall_area_gross": 0.0,
        "ceiling_area_gross": 0.0
    }
    
    for field, default_value in required_dimension_fields.items():
        if field not in current_room["dimensions"]:
            current_room["dimensions"][field] = default_value

    # Initialize calculation_mode if not exists (for AI Manual Edit Mode)
    if "calculation_mode" not in current_room:
        current_room["calculation_mode"] = "auto_calculate"
    
    if "openings" not in current_room:
        current_room["openings"] = {
            # Standard openings
            "interior_doors": 1, 
            "exterior_doors": 0, 
            "windows": 1, 
            "open_areas": 0, 
            "skylights": 0,
            # Advanced openings
            "pocket_doors": 0,
            "bifold_doors": 0,
            "built_in_cabinets": 0,
            "archways": 0,
            "pass_throughs": 0
        }
    
    if "opening_sizes" not in current_room:
        current_room["opening_sizes"] = {
            # Standard sizes
            "door_width_ft": 3.0, 
            "door_height_ft": 8.0,
            "window_width_ft": 3.0, 
            "window_height_ft": 4.0,
            "open_area_width_ft": 6.0, 
            "open_area_height_ft": 8.0,
            "skylight_width_ft": 2.0, 
            "skylight_length_ft": 4.0,
            # Advanced sizes
            "pocket_door_width_ft": 3.0, 
            "pocket_door_height_ft": 8.0,
            "bifold_door_width_ft": 4.0, 
            "bifold_door_height_ft": 8.0,
            "built_in_width_ft": 3.0, 
            "built_in_height_ft": 8.0,
            "archway_width_ft": 4.0, 
            "archway_height_ft": 8.0,
            "pass_through_width_ft": 3.0, 
            "pass_through_height_ft": 2.0
        }
    
    # Ensure all opening types exist in the openings dict
    required_openings = [
        "interior_doors", "exterior_doors", "windows", "open_areas", "skylights",
        "pocket_doors", "bifold_doors", "built_in_cabinets", "archways", "pass_throughs"
    ]
    
    for opening_type in required_openings:
        if opening_type not in current_room["openings"]:
            current_room["openings"][opening_type] = 0


def create_continuity_zone(zone_type: str, primary_room: str, connected_rooms: List[str], reason: str) -> Dict[str, Any]:
    """Create a continuity zone structure"""
    return {
        "zone_id": f"{zone_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "zone_type": zone_type,  # 'floor' or 'paint'
        "primary_room": primary_room,
        "connected_rooms": connected_rooms,
        "reason": reason,
        "auto_generated": False,
        "material_specification": "",
        "work_scope": {}
    }


def get_damage_source_options() -> List[Tuple[str, str]]:
    """Get damage source options"""
    return [
        ("water_damage", "Water Damage"),
        ("fire_damage", "Fire Damage"),
        ("storm_tree_fall", "Storm/Tree Fall"),
        ("structural", "Structural"),
        ("other", "Other")
    ]


def get_contractor_types() -> List[Tuple[str, str]]:
    """Get contractor type options"""
    return [
        ("roofing", "Roofing"),
        ("hvac", "HVAC"),
        ("plumbing", "Plumbing"),
        ("electrical", "Electrical"),
        ("flooring_specialist", "Flooring Specialist"),
        ("kitchen_cabinet", "Kitchen Cabinet"),
        ("moving_company", "Moving Company"),
        ("mold_remediation", "Mold Remediation")
    ]


def get_content_manipulation_options() -> List[Tuple[str, str]]:
    """Get content manipulation strategy options"""
    return [
        ("zone_based", "Zone-Based (Different per area)"),
        ("project_wide_exclude", "Project-Wide Exclude (Moving company)"),
        ("project_wide_basic", "Project-Wide Basic (Contractor minimal)"),
        ("room_empty", "Room Empty (All cleared)")
    ]


def get_building_level_options() -> List[Tuple[str, str]]:
    """Get building level options"""
    return [
        ("ground", "Ground Floor"),
        ("second_floor", "2nd Floor"),
        ("third_plus_floor", "3rd+ Floor"),
        ("basement", "Basement"),
        ("multi_level", "Multi-Level")
    ]


def get_access_condition_options() -> List[Tuple[str, str]]:
    """Get access condition options"""
    return [
        ("normal", "Normal Access"),
        ("stairs_required", "Stairs Required"),
        ("tight_access", "Tight Access"),
        ("over_100ft_dumpster", ">100ft to Dumpster")
    ]


def get_standard_work_packages() -> List[Tuple[str, str, str]]:
    """Get standard work package options with descriptions"""
    return [
        ("full_room_restoration", "Complete Water Damage Package", "Demo, dry, rebuild, finish"),
        ("floor_replacement", "Floor Replacement Package", "Remove, prep, install, finish"),
        ("paint_refresh", "Paint Refresh Package", "Prep, prime, 2-coat paint system"),
        ("trim_restoration", "Trim Restoration Package", "Remove, replace, prime, paint"),
        ("bathroom_restoration", "Bathroom Restoration", "Moisture-resistant materials, ventilation"),
        ("kitchen_prep", "Kitchen Prep Package", "Cabinet-ready prep work only"),
        ("basement_finishing", "Basement Finishing", "Moisture control, insulation, code compliance"),
        ("stairway_package", "Stairway Package", "Specialized access, safety requirements"),
        ("minor_structural", "Minor Structural Repair", "Joist/stud repair, code compliance"),
        ("subfloor_replacement", "Subfloor Replacement", "Removal, substrate prep, installation"),
        ("drywall_blend", "Drywall Blend Package", "New-to-existing seamless integration")
    ]


def get_room_input_methods() -> List[Tuple[str, str]]:
    """Get room input method options"""
    return [
        ("ai_image_analysis", "AI Image Analysis"),
        ("simple_rectangular", "Simple Rectangular"),
        ("complex_manual", "Complex Manual"),
        ("standard_template", "Standard Template")
    ]


def get_mitigation_status_options() -> List[Tuple[str, str]]:
    """Get mitigation status options"""
    return [
        ("complete_gut", "Complete Gut - All materials removed"),
        ("partial_demo", "Partial Demo - Some materials removed"),
        ("no_demo", "No Demo - All materials intact")
    ]


def get_structural_issue_options() -> List[Tuple[str, str]]:
    """Get structural issue options"""
    return [
        ("none", "None"),
        ("minor_repair", "Minor Repair Needed"),
        ("major_structural", "Major Structural Work")
    ]


def calculate_room_quantities(room_data: Dict[str, Any], project_standards: Dict[str, Any]) -> Dict[str, float]:
    """Calculate room quantities with waste factors and deductions - PAINT WASTE REMOVED"""
    
    dimensions = room_data.get("dimensions", {})
    openings = room_data.get("openings", {})
    work_scope = room_data.get("work_scope", {})
    
    # Get base dimensions
    length = float(dimensions.get("length", 0))
    width = float(dimensions.get("width", 0))
    height = float(dimensions.get("height", project_standards.get("standard_ceiling_height", 8)))
    
    if length <= 0 or width <= 0:
        return {}
    
    # Base calculations
    floor_area = length * width
    perimeter = 2 * (length + width)
    wall_area_gross = perimeter * height
    ceiling_area = floor_area
    
    # Deductions
    interior_doors = openings.get("interior_doors", 1)
    exterior_doors = openings.get("exterior_doors", 0)
    windows = openings.get("windows", 1)
    
    door_wall_deduction = (interior_doors * 20) + (exterior_doors * 20)
    window_wall_deduction = windows * 15
    door_perimeter_deduction = (interior_doors + exterior_doors) * 3
    
    # Net calculations
    wall_area_net = max(0, wall_area_gross - door_wall_deduction - window_wall_deduction)
    baseboard_length_net = max(0, perimeter - door_perimeter_deduction)
    
    quantities = {
        "floor_area": floor_area,
        "wall_area_gross": wall_area_gross,
        "wall_area_net": wall_area_net,
        "ceiling_area": ceiling_area,
        "perimeter_gross": perimeter,
        "baseboard_length_net": baseboard_length_net
    }
    
    # Work scope calculations with waste factors
    if work_scope.get("flooring", {}).get("required", False):
        flooring_type = work_scope["flooring"].get("type", "hardwood")
        waste_factor = get_flooring_waste_factor(flooring_type)
        quantities["flooring_install_sf"] = floor_area * (1 + waste_factor)
        quantities["flooring_waste_factor"] = waste_factor
    
    if work_scope.get("drywall", {}).get("required", False):
        drywall_extent = work_scope["drywall"].get("extent", "full_room")
        if drywall_extent == "full_room":
            quantities["drywall_install_sf"] = wall_area_net * 1.10
            quantities["drywall_tape_sf"] = wall_area_net * 1.10
        else:
            # Partial drywall
            partial_area = wall_area_net * 0.3
            quantities["drywall_install_sf"] = partial_area * 1.10
            quantities["drywall_tape_lf"] = perimeter * 0.5 * 1.10
    
    if work_scope.get("trim_baseboard", {}).get("required", False):
        quantities["baseboard_install_lf"] = baseboard_length_net * 1.10
        
        # Quarter round if applicable
        if project_standards.get("quarter_round", True):
            quantities["quarter_round_install_lf"] = baseboard_length_net * 1.10
    
    # PAINT CALCULATIONS - NO WASTE FACTOR APPLIED
    if work_scope.get("paint", {}).get("required", False):
        paint_scope = work_scope["paint"].get("scope", "walls_and_ceiling")
        
        if paint_scope == "walls_and_ceiling":
            paint_area = wall_area_net + ceiling_area
        elif paint_scope == "walls_only":
            paint_area = wall_area_net
        elif paint_scope == "ceiling_only":
            paint_area = ceiling_area
        else:
            paint_area = 0
        
        if paint_area > 0:
            quantities["primer_sf"] = paint_area  # NO WASTE FACTOR (was 1.05)
            quantities["paint_sf"] = paint_area   # NO WASTE FACTOR (was 1.05)
    
    if work_scope.get("insulation", {}).get("required", False):
        quantities["insulation_sf"] = wall_area_gross * 1.05
    
    return quantities


def get_flooring_waste_factor(flooring_type: str) -> float:
    """Get waste factor for different flooring types"""
    waste_factors = {
        "hardwood": 0.10,
        "laminate": 0.10,
        "luxury_vinyl_plank": 0.10,
        "carpet": 0.15,
        "sheet_vinyl": 0.25,
        "tile": 0.10,
        "large_format_tile": 0.15
    }
    return waste_factors.get(flooring_type, 0.10)


def calculate_debris_weight(room_data: Dict[str, Any]) -> Dict[str, float]:
    """Calculate debris weight for materials being removed"""
    
    material_weights = {
        "drywall_half_inch": 2.2,
        "drywall_five_eighth": 2.75,
        "hardwood_flooring": 2.5,
        "laminate_flooring": 1.8,
        "carpet_and_pad": 1.2,
        "vinyl_lvp": 1.5,
        "ceramic_tile": 4.0,
        "insulation_fiberglass": 0.5,
        "trim_baseboard": 1.5
    }
    
    current_conditions = room_data.get("current_conditions", {})
    debris_weights = {}
    total_weight = 0
    
    # Calculate removal quantities
    flooring_removed = current_conditions.get("flooring_removed", {})
    if flooring_removed.get("status") != "none":
        quantity = flooring_removed.get("quantity", 0)
        weight = quantity * material_weights.get("hardwood_flooring", 2.5)  # Default to hardwood
        debris_weights["flooring"] = weight
        total_weight += weight
    
    drywall_removed = current_conditions.get("drywall_removed", {})
    if drywall_removed.get("status") != "none":
        quantity = drywall_removed.get("quantity", 0)
        weight = quantity * material_weights.get("drywall_half_inch", 2.2)
        debris_weights["drywall"] = weight
        total_weight += weight
    
    insulation_removed = current_conditions.get("insulation_removed", {})
    if insulation_removed.get("status") != "none":
        quantity = insulation_removed.get("quantity", 0)
        weight = quantity * material_weights.get("insulation_fiberglass", 0.5)
        debris_weights["insulation"] = weight
        total_weight += weight
    
    trim_removed = current_conditions.get("trim_removed", {})
    if trim_removed.get("status") != "none":
        quantity = trim_removed.get("quantity", 0)
        weight = quantity * material_weights.get("trim_baseboard", 1.5)
        debris_weights["trim"] = weight
        total_weight += weight
    
    # Add 10% miscellaneous debris factor
    misc_debris = total_weight * 0.10
    debris_weights["miscellaneous"] = misc_debris
    total_weight += misc_debris
    
    debris_weights["total_pounds"] = total_weight
    debris_weights["total_tons"] = total_weight / 2000
    
    return debris_weights


def validate_project_data(project_data):
    """Enhanced project validation that supports AI analysis measurements"""
    errors = []
    
    # Basic property info validation
    property_info = project_data.get("property_info", {})
    
    if not property_info.get("property_address", "").strip():
        errors.append("Property address is required")
    
    if not property_info.get("claim_number", "").strip():
        errors.append("Claim number is required")
    
    # Rooms validation with enhanced logic
    rooms = project_data.get("rooms", [])
    if not rooms:
        errors.append("At least one room is required")
    else:
        for i, room in enumerate(rooms):
            room_errors = validate_room_data(room, i)
            errors.extend(room_errors)
    
    return errors


def validate_room_data(room_data, room_index=0):
    """Enhanced room validation that supports AI analysis measurements"""
    errors = []
    room_name = room_data.get("room_name", f"Room {room_index + 1}")
    
    # Check if this room was measured using AI analysis
    is_ai_analyzed = (
        room_data.get("input_method") in ["ai_image_analysis", "ai_manual_edit"] or
        room_data.get("dimensions", {}).get("ai_initialized", False) or
        room_data.get("ai_analysis", {}).get("user_confirmed", False)
    )
    
    # Basic room info validation
    if not room_data.get("room_name", "").strip():
        errors.append(f"{room_name}: Room name is required")
    
    dimensions = room_data.get("dimensions", {})
    
    # Floor area is always required
    floor_area = dimensions.get("floor_area", 0)
    if not floor_area or floor_area <= 0:
        errors.append(f"{room_name}: Floor area must be greater than 0")
    
    # Height is always required
    height = dimensions.get("height", 0)
    if not height or height < 7.0:
        errors.append(f"{room_name}: Height must be at least 7.0 feet")
    
    # Length and Width validation - SKIP FOR AI ANALYZED ROOMS
    if not is_ai_analyzed:
        # Only validate length/width for non-AI analyzed rooms (simple rectangular, manual input)
        length = dimensions.get("length", 0)
        width = dimensions.get("width", 0)
        
        if not length or length <= 0:
            errors.append(f"{room_name}: Length must be greater than 0")
        
        if not width or width <= 0:
            errors.append(f"{room_name}: Width must be greater than 0")
        
        # Check if calculated area matches length × width (with tolerance)
        if length > 0 and width > 0:
            calculated_area = length * width
            if abs(calculated_area - floor_area) > 1.0:  # 1 SF tolerance
                errors.append(f"{room_name}: Floor area ({floor_area:.1f} SF) doesn't match length × width ({calculated_area:.1f} SF)")
    
    # Zone assignment validation
    zone = room_data.get("zone_assignment", "")
    if not zone or zone not in ["A", "B", "C", "Independent"]:
        errors.append(f"{room_name}: Valid zone assignment is required (A, B, C, or Independent)")
    
    return errors


# ========== JSON FILTERING FUNCTIONS ==========

def filter_openings_for_export(openings: Dict[str, Any]) -> Dict[str, Any]:
    """Filter openings to only include non-zero values"""
    filtered_openings = {}
    
    for opening_type, count in openings.items():
        if count > 0:
            filtered_openings[opening_type] = count
    
    return filtered_openings


def filter_opening_sizes_for_export(openings: Dict[str, Any], opening_sizes: Dict[str, Any]) -> Dict[str, Any]:
    """Filter opening sizes to only include sizes for openings that exist"""
    if not openings or not opening_sizes:
        return {}
    
    filtered_opening_sizes = {}
    
    # Mapping of opening types to their size keys
    opening_size_mappings = {
        "doors": {
            "condition": lambda: openings.get("interior_doors", 0) + openings.get("exterior_doors", 0) > 0,
            "keys": ["door_width_ft", "door_height_ft"]
        },
        "windows": {
            "condition": lambda: openings.get("windows", 0) > 0,
            "keys": ["window_width_ft", "window_height_ft"]
        },
        "open_areas": {
            "condition": lambda: openings.get("open_areas", 0) > 0,
            "keys": ["open_area_width_ft", "open_area_height_ft"]
        },
        "skylights": {
            "condition": lambda: openings.get("skylights", 0) > 0,
            "keys": ["skylight_width_ft", "skylight_length_ft"]
        },
        "pocket_doors": {
            "condition": lambda: openings.get("pocket_doors", 0) > 0,
            "keys": ["pocket_door_width_ft", "pocket_door_height_ft"]
        },
        "bifold_doors": {
            "condition": lambda: openings.get("bifold_doors", 0) > 0,
            "keys": ["bifold_door_width_ft", "bifold_door_height_ft"]
        },
        "built_in_cabinets": {
            "condition": lambda: openings.get("built_in_cabinets", 0) > 0,
            "keys": ["built_in_width_ft", "built_in_height_ft"]
        },
        "archways": {
            "condition": lambda: openings.get("archways", 0) > 0,
            "keys": ["archway_width_ft", "archway_height_ft"]
        },
        "pass_throughs": {
            "condition": lambda: openings.get("pass_throughs", 0) > 0,
            "keys": ["pass_through_width_ft", "pass_through_height_ft"]
        }
    }
    
    # Only include size keys for openings that exist
    for opening_group, config in opening_size_mappings.items():
        if config["condition"]():
            for size_key in config["keys"]:
                if size_key in opening_sizes:
                    filtered_opening_sizes[size_key] = opening_sizes[size_key]
    
    return filtered_opening_sizes


def filter_demolition_status_for_export(demolition_status: Dict[str, Any]) -> Dict[str, Any]:
    """Filter demolition status to only include actual demolition work"""
    filtered_demo = {}
    
    for demo_type, demo_data in demolition_status.items():
        if demo_type == "general_notes":
            # Include general notes if they exist and are not empty
            if demo_data and str(demo_data).strip():
                filtered_demo[demo_type] = demo_data
        elif isinstance(demo_data, dict):
            # Check if there's actual demolition
            demolished = demo_data.get("demolished", False)
            demolished_area = demo_data.get("demolished_area", 0)
            demolished_length = demo_data.get("demolished_length", 0)
            
            if demolished or demolished_area > 0 or demolished_length > 0:
                # Only include this demolition item if there's actual work
                filtered_item = {}
                
                if demolished:
                    filtered_item["demolished"] = True
                
                if demolished_area > 0:
                    filtered_item["demolished_area"] = demolished_area
                
                if demolished_length > 0:
                    filtered_item["demolished_length"] = demolished_length
                
                # Include total areas/lengths if they exist
                if demo_data.get("total_area", 0) > 0:
                    filtered_item["total_area"] = demo_data["total_area"]
                
                if demo_data.get("total_length", 0) > 0:
                    filtered_item["total_length"] = demo_data["total_length"]
                
                # Include notes if they exist
                if demo_data.get("notes") and str(demo_data["notes"]).strip():
                    filtered_item["notes"] = demo_data["notes"]
                
                if filtered_item:
                    filtered_demo[demo_type] = filtered_item
    
    return filtered_demo


def filter_work_scope_enhanced_for_export(work_scope: Dict[str, Any]) -> Dict[str, Any]:
    """Enhanced work scope filtering that handles the new structure with other_work"""
    filtered_work_scope = {}
    
    for work_type, work_data in work_scope.items():
        if work_type == "other_work":
            # Handle the special other_work structure
            if isinstance(work_data, dict):
                other_work_filtered = {}
                
                # Include items if they exist
                if work_data.get("items") and len(work_data["items"]) > 0:
                    other_work_filtered["items"] = work_data["items"]
                
                # Include notes if they exist
                if work_data.get("notes") and str(work_data["notes"]).strip():
                    other_work_filtered["notes"] = work_data["notes"]
                
                if other_work_filtered:
                    filtered_work_scope[work_type] = other_work_filtered
        
        elif isinstance(work_data, dict):
            # Check if work is required
            if work_data.get("required", False):
                # Only include this work item if it's required
                filtered_item = {"required": True}
                
                # Add other relevant fields
                for key, value in work_data.items():
                    if key != "required" and value:  # Only include non-empty values
                        if isinstance(value, str) and value.strip():
                            filtered_item[key] = value
                        elif isinstance(value, (int, float)) and value > 0:
                            filtered_item[key] = value
                        elif isinstance(value, bool):
                            filtered_item[key] = value
                        elif isinstance(value, list) and len(value) > 0:
                            filtered_item[key] = value
                
                filtered_work_scope[work_type] = filtered_item
        else:
            # Handle non-dict work scope items
            if work_data:
                filtered_work_scope[work_type] = work_data
    
    return filtered_work_scope


def filter_current_conditions_for_export(current_conditions: Dict[str, Any]) -> Dict[str, Any]:
    """Filter current conditions to only include relevant demolition status"""
    filtered_conditions = {}
    
    for condition_type, condition_data in current_conditions.items():
        if isinstance(condition_data, dict):
            # Check if there's actual demolition/removal
            status = condition_data.get("status", "none")
            quantity = condition_data.get("quantity", 0)
            demolished = condition_data.get("demolished", False)
            
            if status != "none" or quantity > 0 or demolished:
                # Only include if there's actual work/removal
                filtered_item = {}
                for key, value in condition_data.items():
                    if value:  # Only include non-empty/non-zero values
                        if isinstance(value, str) and value.strip() and value != "none":
                            filtered_item[key] = value
                        elif isinstance(value, (int, float)) and value > 0:
                            filtered_item[key] = value
                        elif isinstance(value, bool) and value:
                            filtered_item[key] = value
                
                if filtered_item:
                    filtered_conditions[condition_type] = filtered_item
        else:
            # Handle non-dict items
            if condition_data and condition_data != "none":
                filtered_conditions[condition_type] = condition_data
    
    return filtered_conditions


def filter_special_conditions_for_export(special_conditions: Dict[str, Any]) -> Dict[str, Any]:
    """Filter special conditions to only include actual conditions"""
    filtered_special = {}
    
    for category, category_data in special_conditions.items():
        if isinstance(category_data, dict):
            filtered_category = {}
            
            for condition_type, condition_data in category_data.items():
                if isinstance(condition_data, dict):
                    # Check if condition is present/true
                    present = condition_data.get("present", False)
                    if present:
                        filtered_item = {"present": True}
                        # Add other relevant fields
                        for key, value in condition_data.items():
                            if key != "present" and value:
                                if isinstance(value, str) and value.strip():
                                    filtered_item[key] = value
                                elif isinstance(value, (int, float)) and value > 0:
                                    filtered_item[key] = value
                        
                        filtered_category[condition_type] = filtered_item
                else:
                    # Handle boolean or other simple conditions
                    if condition_data:
                        filtered_category[condition_type] = condition_data
            
            if filtered_category:
                filtered_special[category] = filtered_category
    
    return filtered_special


def filter_material_specifications_for_export(material_specs: Dict[str, Any]) -> Dict[str, Any]:
    """Filter material specifications to only include overrides and customizations"""
    filtered_specs = {}
    
    for spec_type, spec_value in material_specs.items():
        if isinstance(spec_value, dict):
            # Filter complex material specs
            filtered_complex = {}
            for key, value in spec_value.items():
                if value:  # Only include non-empty values
                    if isinstance(value, bool) and value:
                        filtered_complex[key] = value
                    elif isinstance(value, str) and value.strip():
                        filtered_complex[key] = value
                    elif isinstance(value, (int, float)) and value > 0:
                        filtered_complex[key] = value
            
            if filtered_complex:
                filtered_specs[spec_type] = filtered_complex
        else:
            # Handle simple overrides
            if spec_value:
                if isinstance(spec_value, str) and spec_value.strip():
                    filtered_specs[spec_type] = spec_value
                elif isinstance(spec_value, (int, float)) and spec_value > 0:
                    filtered_specs[spec_type] = spec_value
                elif isinstance(spec_value, bool):
                    filtered_specs[spec_type] = spec_value
    
    return filtered_specs


def filter_project_coordination_for_export(project_coordination: Dict[str, Any]) -> Dict[str, Any]:
    """Filter project coordination to only include active coordination items"""
    filtered_coordination = {}
    
    for coord_type, coord_value in project_coordination.items():
        if isinstance(coord_value, list):
            # Filter non-empty lists
            if len(coord_value) > 0:
                filtered_coordination[coord_type] = coord_value
        elif isinstance(coord_value, bool):
            # Only include True boolean values
            if coord_value:
                filtered_coordination[coord_type] = coord_value
        elif coord_value:
            # Include other non-empty values
            filtered_coordination[coord_type] = coord_value
    
    return filtered_coordination


def filter_work_zones_for_export(work_zones: Dict[str, Any]) -> Dict[str, Any]:
    """Filter work zones to only include configured zones and strategies"""
    filtered_zones = {}
    
    for zone_type, zone_value in work_zones.items():
        if isinstance(zone_value, list):
            # Filter non-empty zone lists
            if len(zone_value) > 0:
                filtered_zones[zone_type] = zone_value
        elif isinstance(zone_value, str):
            # Only include non-empty strategies
            if zone_value.strip():
                filtered_zones[zone_type] = zone_value
        elif zone_value:
            # Include other configured values
            filtered_zones[zone_type] = zone_value
    
    return filtered_zones

def clean_room_data_for_export_enhanced(room_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhanced room data cleaning - UPDATED TO HANDLE CALCULATION_MODE
    """
    cleaned_room = {}
    
    # Basic room info - always include if present
    if room_data.get("room_name"):
        cleaned_room["room_name"] = room_data["room_name"]
    
    if room_data.get("zone_assignment"):
        cleaned_room["zone_assignment"] = room_data["zone_assignment"]
    
    if room_data.get("input_method"):
        cleaned_room["input_method"] = room_data["input_method"]
    
    # Filter AI analysis - only keep essential confirmed data
    if room_data.get("ai_analysis"):
        ai_analysis = room_data["ai_analysis"]
        essential_ai_data = {}
        
        if ai_analysis.get("user_confirmed"):
            essential_ai_data["user_confirmed"] = True
        if ai_analysis.get("manually_edited"):
            essential_ai_data["manually_edited"] = True
        if ai_analysis.get("confidence_level") and ai_analysis["confidence_level"] != "":
            essential_ai_data["confidence_level"] = ai_analysis["confidence_level"]
        # Include calculation mode used if it exists and is not default
        if ai_analysis.get("calculation_mode_used") and ai_analysis["calculation_mode_used"] != "auto_calculate":
            essential_ai_data["calculation_mode_used"] = ai_analysis["calculation_mode_used"]
        
        # Include applied_data if it exists and has meaningful content
        if ai_analysis.get("applied_data"):
            applied_data = ai_analysis["applied_data"]
            filtered_applied = {}
            
            for key, value in applied_data.items():
                if value:  # Only include non-empty values
                    if isinstance(value, dict) and any(value.values()):
                        filtered_applied[key] = value
                    elif not isinstance(value, dict):
                        filtered_applied[key] = value
            
            if filtered_applied:
                essential_ai_data["applied_data"] = filtered_applied
        
        if essential_ai_data:
            cleaned_room["ai_analysis"] = essential_ai_data
    
    # Always include dimensions (core data)
    if room_data.get("dimensions"):
        # Only include dimensions with meaningful values
        dimensions = room_data["dimensions"]
        filtered_dimensions = {}
        
        # Core dimensions that should always be included if > 0
        core_dimensions = ["length", "width", "height", "floor_area", "wall_area", "ceiling_area"]
        for dim in core_dimensions:
            if dimensions.get(dim, 0) > 0:
                filtered_dimensions[dim] = dimensions[dim]
        
        # Additional calculated dimensions
        additional_dims = ["wall_area_gross", "ceiling_area_gross", "perimeter_gross", "perimeter_net", 
                          "floor_perimeter", "floor_perimeter_net", "ceiling_perimeter", "ceiling_perimeter_net"]
        for dim in additional_dims:
            if dimensions.get(dim, 0) > 0:
                filtered_dimensions[dim] = dimensions[dim]
        
        # Room metadata
        if dimensions.get("room_type") and dimensions["room_type"] != "Unknown":
            filtered_dimensions["room_type"] = dimensions["room_type"]
        if dimensions.get("room_shape") and dimensions["room_shape"] != "rectangular":
            filtered_dimensions["room_shape"] = dimensions["room_shape"]
        if dimensions.get("ai_initialized"):
            filtered_dimensions["ai_initialized"] = True
        
        if filtered_dimensions:
            cleaned_room["dimensions"] = filtered_dimensions
    
    # NOTE: calculation_mode is intentionally NOT exported as it's a temporary UI state
    # It gets saved in ai_analysis.calculation_mode_used when confirmed
    
    # Filter openings - only include non-zero openings
    if room_data.get("openings"):
        filtered_openings = filter_openings_for_export(room_data["openings"])
        if filtered_openings:
            cleaned_room["openings"] = filtered_openings
    
    # Filter opening sizes - only for existing openings
    if room_data.get("opening_sizes") and cleaned_room.get("openings"):
        filtered_opening_sizes = filter_opening_sizes_for_export(
            cleaned_room["openings"], 
            room_data["opening_sizes"]
        )
        if filtered_opening_sizes:
            cleaned_room["opening_sizes"] = filtered_opening_sizes
    
    # Filter current conditions - only include actual demolition/issues
    if room_data.get("current_conditions"):
        filtered_conditions = filter_current_conditions_for_export(room_data["current_conditions"])
        if filtered_conditions:
            cleaned_room["current_conditions"] = filtered_conditions
    
    # NEW: Filter demolition status - only include actual demolition work
    if room_data.get("demolition_status"):
        filtered_demolition = filter_demolition_status_for_export(room_data["demolition_status"])
        if filtered_demolition:
            cleaned_room["demolition_status"] = filtered_demolition
    
    # Filter material specifications - only include overrides
    if room_data.get("material_specifications"):
        filtered_specs = filter_material_specifications_for_export(room_data["material_specifications"])
        if filtered_specs:
            cleaned_room["material_specifications"] = filtered_specs
    
    # NEW: Enhanced work scope filtering - handles other_work structure
    if room_data.get("work_scope"):
        filtered_work_scope = filter_work_scope_enhanced_for_export(room_data["work_scope"])
        if filtered_work_scope:
            cleaned_room["work_scope"] = filtered_work_scope
    
    # Filter special conditions - only include present conditions
    if room_data.get("special_conditions"):
        filtered_special = filter_special_conditions_for_export(room_data["special_conditions"])
        if filtered_special:
            cleaned_room["special_conditions"] = filtered_special
    
    # Include calculated quantities only if they exist and have values
    if room_data.get("calculated_quantities"):
        calc_quantities = room_data["calculated_quantities"]
        filtered_calc = {}
        for key, value in calc_quantities.items():
            if isinstance(value, (int, float)) and value > 0:
                filtered_calc[key] = value
            elif isinstance(value, str) and value.strip():
                filtered_calc[key] = value
        
        if filtered_calc:
            cleaned_room["calculated_quantities"] = filtered_calc
    
    # Include validation status only if there are actual errors/warnings
    if room_data.get("validation_status"):
        validation = room_data["validation_status"]
        filtered_validation = {}
        
        if validation.get("errors") and len(validation["errors"]) > 0:
            filtered_validation["errors"] = validation["errors"]
        if validation.get("warnings") and len(validation["warnings"]) > 0:
            filtered_validation["warnings"] = validation["warnings"]
        if validation.get("is_valid") is False:
            filtered_validation["is_valid"] = False
        
        if filtered_validation:
            cleaned_room["validation_status"] = filtered_validation
    
    return cleaned_room

def export_to_json_clean_enhanced(project_data: Dict[str, Any]) -> str:
    """
    Enhanced export with support for ALL new data structures including demolition_status
    """
    # Create a deep copy to avoid modifying the original data
    export_data = json.loads(json.dumps(project_data, default=str))
    
    # Update last modified timestamp
    if "property_info" in export_data:
        export_data["property_info"]["last_modified"] = datetime.now().isoformat()
        
        # Only include non-empty property info fields
        filtered_property = {}
        for key, value in export_data["property_info"].items():
            if value and str(value).strip():
                filtered_property[key] = value
        export_data["property_info"] = filtered_property
    
    # Filter project coordination
    if "project_coordination" in export_data:
        filtered_coordination = filter_project_coordination_for_export(export_data["project_coordination"])
        if filtered_coordination:
            export_data["project_coordination"] = filtered_coordination
        else:
            export_data.pop("project_coordination", None)
    
    # Filter work zones
    if "work_zones" in export_data:
        filtered_zones = filter_work_zones_for_export(export_data["work_zones"])
        if filtered_zones:
            export_data["work_zones"] = filtered_zones
        else:
            export_data.pop("work_zones", None)
    
    # Filter project standards - only include non-default values
    if "project_standards" in export_data:
        standards = export_data["project_standards"]
        filtered_standards = {}
        
        # Define defaults to compare against
        default_standards = {
            "standard_ceiling_height": 8.0,
            "building_level": "ground",
            "access_conditions": "normal",
            "standard_drywall": "1/2\"",
            "flooring_default": "match_existing",
            "standard_baseboard": "3.5\"",
            "quarter_round": True,
            "paint_scope_default": "walls_and_ceiling"
        }
        
        for key, value in standards.items():
            # Only include if different from default or not in defaults
            if key not in default_standards or value != default_standards[key]:
                filtered_standards[key] = value
        
        if filtered_standards:
            export_data["project_standards"] = filtered_standards
        else:
            export_data.pop("project_standards", None)
    
    # Filter work packages - only include if packages are selected
    if "work_packages" in export_data:
        work_packages = export_data["work_packages"]
        if work_packages.get("selected_packages") and len(work_packages["selected_packages"]) > 0:
            export_data["work_packages"] = work_packages
        else:
            export_data.pop("work_packages", None)
    
    # Clean up room data comprehensively with enhanced cleaning
    if "rooms" in export_data:
        cleaned_rooms = []
        for room in export_data["rooms"]:
            cleaned_room = clean_room_data_for_export_enhanced(room)  # Use enhanced version
            if cleaned_room:  # Only include rooms with actual data
                cleaned_rooms.append(cleaned_room)
        
        if cleaned_rooms:
            export_data["rooms"] = cleaned_rooms
        else:
            export_data.pop("rooms", None)
    
    # Remove empty sections
    empty_sections = []
    for key, value in export_data.items():
        if not value:  # Remove completely empty sections
            empty_sections.append(key)
        elif isinstance(value, dict) and not any(value.values()):
            empty_sections.append(key)
        elif isinstance(value, list) and len(value) == 0:
            empty_sections.append(key)
    
    for section in empty_sections:
        export_data.pop(section, None)
    
    return json.dumps(export_data, indent=2, ensure_ascii=False, default=str)


def export_to_json_with_indicators(project_data: Dict[str, Any]) -> str:
    """
    Alternative: Export with 'N/A' indicators for unused values instead of removing them.
    """
    # Create a deep copy
    export_data = json.loads(json.dumps(project_data, default=str))
    
    # Update timestamp
    if "property_info" in export_data:
        export_data["property_info"]["last_modified"] = datetime.now().isoformat()
    
    # Process rooms with indicators
    if "rooms" in export_data:
        for room in export_data["rooms"]:
            openings = room.get("openings", {})
            
            # Mark unused openings as N/A
            for opening_type, count in openings.items():
                if count == 0:
                    openings[opening_type] = "N/A"
            
            # Mark unused opening sizes as N/A
            if room.get("opening_sizes"):
                opening_sizes = room["opening_sizes"]
                
                # Check each opening type and mark sizes as N/A if opening doesn't exist
                total_doors = (openings.get("interior_doors", 0) if openings.get("interior_doors") != "N/A" else 0) + \
                             (openings.get("exterior_doors", 0) if openings.get("exterior_doors") != "N/A" else 0)
                
                if total_doors == 0:
                    opening_sizes["door_width_ft"] = "N/A"
                    opening_sizes["door_height_ft"] = "N/A"
                
                if openings.get("windows") == "N/A" or openings.get("windows", 0) == 0:
                    opening_sizes["window_width_ft"] = "N/A"
                    opening_sizes["window_height_ft"] = "N/A"
                
                # Continue for all opening types...
                opening_checks = [
                    ("open_areas", ["open_area_width_ft", "open_area_height_ft"]),
                    ("skylights", ["skylight_width_ft", "skylight_length_ft"]),
                    ("pocket_doors", ["pocket_door_width_ft", "pocket_door_height_ft"]),
                    ("bifold_doors", ["bifold_door_width_ft", "bifold_door_height_ft"]),
                    ("built_in_cabinets", ["built_in_width_ft", "built_in_height_ft"]),
                    ("archways", ["archway_width_ft", "archway_height_ft"]),
                    ("pass_throughs", ["pass_through_width_ft", "pass_through_height_ft"])
                ]
                
                for opening_type, size_keys in opening_checks:
                    if openings.get(opening_type) == "N/A" or openings.get(opening_type, 0) == 0:
                        for size_key in size_keys:
                            if size_key in opening_sizes:
                                opening_sizes[size_key] = "N/A"
            
            # Mark unused work scope items as N/A
            if room.get("work_scope"):
                work_scope = room["work_scope"]
                for work_type, work_data in work_scope.items():
                    if isinstance(work_data, dict) and not work_data.get("required", False):
                        work_data["required"] = "N/A"
            
            # Mark unused demolition status as N/A
            if room.get("demolition_status"):
                demolition_status = room["demolition_status"]
                for demo_type, demo_data in demolition_status.items():
                    if isinstance(demo_data, dict) and not demo_data.get("demolished", False):
                        demo_data["demolished"] = "N/A"
    
    return json.dumps(export_data, indent=2, ensure_ascii=False, default=str)


# ========== MAIN EXPORT FUNCTION ==========

def export_to_json(project_data: Dict[str, Any]) -> str:
    """
    Main export function - uses the enhanced clean version with all new data structure support
    """
    return export_to_json_clean_enhanced(project_data)


def import_from_json(json_str: str) -> Optional[Dict[str, Any]]:
    """Import project data from JSON string"""
    try:
        data = json.loads(json_str)
        
        # Validate basic structure
        if not isinstance(data, dict):
            return None
        
        # Ensure required keys exist with proper structure
        required_keys = ["property_info", "project_coordination", "work_zones", 
                        "project_standards", "work_packages", "rooms"]
        
        for key in required_keys:
            if key not in data:
                if key == "property_info":
                    data[key] = {}
                elif key == "project_coordination":
                    data[key] = {"other_contractors": [], "work_sequence_dependencies": []}
                elif key == "work_zones":
                    data[key] = {"content_manipulation_strategy": "", "floor_continuity_zones": [], "paint_continuity_zones": []}
                elif key == "project_standards":
                    data[key] = {}
                elif key == "work_packages":
                    data[key] = {"selected_packages": []}
                elif key == "rooms":
                    data[key] = []
        
        return data
    except json.JSONDecodeError:
        return None


def generate_filename(project_data: Dict[str, Any]) -> str:
    """Generate a filename for the project"""
    property_info = project_data.get("property_info", {})
    address = property_info.get("property_address", "")
    claim_number = property_info.get("claim_number", "")
    
    # Clean address for filename
    if address:
        clean_address = "".join(c for c in address if c.isalnum() or c in (' ', '-', '_')).rstrip()
        clean_address = clean_address.replace(' ', '_')[:30]
    else:
        clean_address = "reconstruction_project"
    
    # Add claim number if available
    if claim_number:
        clean_claim = "".join(c for c in claim_number if c.isalnum() or c in ('-', '_'))
        filename = f"{clean_address}_{clean_claim}_intake_v3.json"
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"{clean_address}_{timestamp}_intake_v3.json"
    
    return filename


def generate_auto_justifications(room_data: Dict[str, Any], work_scope: Dict[str, Any]) -> Dict[str, str]:
    """Generate automatic justifications for work items"""
    justifications = {}
    
    if work_scope.get("flooring", {}).get("required", False):
        flooring_type = work_scope["flooring"].get("type", "")
        waste_factor = get_flooring_waste_factor(flooring_type) * 100
        justifications["flooring"] = f"IRC R503.1 requires proper installation with {waste_factor:.0f}% waste factor for cutting allowance and proper layout"
    
    if work_scope.get("drywall", {}).get("required", False):
        justifications["drywall"] = "IRC R702.3 installation requirements with 10% waste factor for cutting allowance and proper joint placement"
    
    if work_scope.get("insulation", {}).get("required", False):
        justifications["insulation"] = "IRC R402 minimum insulation requirements with 5% waste factor for cutting and fitting around framing"
    
    if work_scope.get("paint", {}).get("required", False):
        justifications["paint"] = "IRC R702.3.8 requires proper surface preparation with PVA primer for adequate paint adhesion, no waste factor applied for paint coverage"
    
    return justifications