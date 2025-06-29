"""
Enhanced utility functions for the Reconstruction Intake Form v3.0
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
    """Calculate room quantities with waste factors and deductions"""
    
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
            quantities["primer_sf"] = paint_area * 1.05
            quantities["paint_sf"] = paint_area * 1.05
    
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


def validate_project_data(project_data: Dict[str, Any]) -> List[str]:
    """Validate complete project data"""
    errors = []
    
    # Validate property info
    property_info = project_data.get("property_info", {})
    if not property_info.get("property_address"):
        errors.append("Property address is required")
    
    # Validate rooms
    rooms = project_data.get("rooms", [])
    if not rooms:
        errors.append("At least one room is required")
    
    for i, room in enumerate(rooms):
        room_errors = validate_room_data(room)
        errors.extend([f"Room {i+1} ({room.get('room_name', 'Unnamed')}): {error}" for error in room_errors])
    
    return errors


def validate_room_data(room_data: Dict[str, Any]) -> List[str]:
    """Validate individual room data"""
    errors = []
    
    # Check required fields
    if not room_data.get("room_name"):
        errors.append("Room name is required")
    
    # Validate dimensions
    dimensions = room_data.get("dimensions", {})
    length = dimensions.get("length", 0)
    width = dimensions.get("width", 0)
    height = dimensions.get("height", 0)
    
    if not isinstance(length, (int, float)) or length <= 0:
        errors.append("Length must be greater than 0")
    elif length > 100:
        errors.append(f"Length seems unreasonably large ({length} ft)")
    
    if not isinstance(width, (int, float)) or width <= 0:
        errors.append("Width must be greater than 0")
    elif width > 100:
        errors.append(f"Width seems unreasonably large ({width} ft)")
    
    if not isinstance(height, (int, float)) or height < 7 or height > 20:
        errors.append("Height must be between 7 and 20 feet")
    
    return errors


def export_to_json(project_data: Dict[str, Any]) -> str:
    """Export project data to JSON string"""
    # Update last modified timestamp
    if "property_info" in project_data:
        project_data["property_info"]["last_modified"] = datetime.now().isoformat()
    
    return json.dumps(project_data, indent=2, ensure_ascii=False, default=str)


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
        justifications["paint"] = "IRC R702.3.8 requires proper surface preparation with PVA primer for adequate paint adhesion, 5% waste factor applied"
    
    return justifications