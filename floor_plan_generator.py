"""
Floor Plan Generator for Insurance Estimates
Generates SVG floor plans for individual rooms with measurements
"""

import json
import math
from typing import Dict, List, Tuple, Optional
from pathlib import Path

class FloorPlanGenerator:
    """Generate SVG floor plans for rooms with measurements"""
    
    def __init__(self, canvas_width: int = 450, canvas_height: int = 250):
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.padding = 35  # Ensure dimension labels are visible
        
    def generate_room_svg(self, room_data: Dict) -> str:
        """
        Generate SVG floor plan for a single room
        
        Args:
            room_data: Dictionary containing room information
                Expected structure:
                {
                    "name": "Room Name",
                    "dimensions": {"length": 20, "width": 15},
                    "area": 300,
                    "perimeter": 70,
                    "features": {...},
                    "measurements": {...}
                }
        
        Returns:
            SVG string representation of the room
        """
        # Extract dimensions
        length = room_data.get('dimensions', {}).get('length', 20)
        width = room_data.get('dimensions', {}).get('width', 15)
        area = room_data.get('area', length * width)
        
        # Calculate scale to fit canvas
        scale = self._calculate_scale(length, width)
        
        # Scaled dimensions
        scaled_length = length * scale
        scaled_width = width * scale
        
        # Always center the room in canvas
        offset_x = (self.canvas_width - scaled_length) / 2
        offset_y = (self.canvas_height - scaled_width) / 2
        
        # Ensure minimum offset for dimension labels
        offset_x = max(offset_x, 35)
        offset_y = max(offset_y, 35)
        
        # Start building SVG
        svg_parts = []
        svg_parts.append(f'<svg width="{self.canvas_width}" height="{self.canvas_height}" viewBox="0 0 {self.canvas_width} {self.canvas_height}" xmlns="http://www.w3.org/2000/svg">')
        
        # Add white background
        svg_parts.append(f'<rect width="{self.canvas_width}" height="{self.canvas_height}" fill="white"/>')
        
        # Draw room outline
        svg_parts.append(f'''
            <rect x="{offset_x}" y="{offset_y}" 
                  width="{scaled_length}" height="{scaled_width}" 
                  fill="none" stroke="black" stroke-width="2"/>
        ''')
        
        # Add dimension labels
        # Top dimension (length)
        svg_parts.append(f'''
            <line x1="{offset_x}" y1="{offset_y - 20}" 
                  x2="{offset_x + scaled_length}" y2="{offset_y - 20}" 
                  stroke="black" stroke-width="1"/>
            <line x1="{offset_x}" y1="{offset_y - 25}" 
                  x2="{offset_x}" y2="{offset_y - 15}" 
                  stroke="black" stroke-width="1"/>
            <line x1="{offset_x + scaled_length}" y1="{offset_y - 25}" 
                  x2="{offset_x + scaled_length}" y2="{offset_y - 15}" 
                  stroke="black" stroke-width="1"/>
            <text x="{offset_x + scaled_length/2}" y="{offset_y - 25}" 
                  text-anchor="middle" font-size="12" font-family="Arial">
                {length}'
            </text>
        ''')
        
        # Left dimension (width)
        svg_parts.append(f'''
            <line x1="{offset_x - 20}" y1="{offset_y}" 
                  x2="{offset_x - 20}" y2="{offset_y + scaled_width}" 
                  stroke="black" stroke-width="1"/>
            <line x1="{offset_x - 25}" y1="{offset_y}" 
                  x2="{offset_x - 15}" y2="{offset_y}" 
                  stroke="black" stroke-width="1"/>
            <line x1="{offset_x - 25}" y1="{offset_y + scaled_width}" 
                  x2="{offset_x - 15}" y2="{offset_y + scaled_width}" 
                  stroke="black" stroke-width="1"/>
            <text x="{offset_x - 30}" y="{offset_y + scaled_width/2}" 
                  text-anchor="middle" font-size="12" font-family="Arial"
                  transform="rotate(-90 {offset_x - 30} {offset_y + scaled_width/2})">
                {width}'
            </text>
        ''')
        
        # Add room name in center
        room_name = room_data.get('name', 'Room')
        svg_parts.append(f'''
            <text x="{offset_x + scaled_length/2}" y="{offset_y + scaled_width/2 - 10}" 
                  text-anchor="middle" font-size="16" font-weight="bold" font-family="Arial">
                {room_name}
            </text>
        ''')
        
        # Add area text
        svg_parts.append(f'''
            <text x="{offset_x + scaled_length/2}" y="{offset_y + scaled_width/2 + 10}" 
                  text-anchor="middle" font-size="14" font-family="Arial">
                {area} sq ft
            </text>
        ''')
        
        # Add doors if present
        doors = room_data.get('features', {}).get('doors', [])
        for door in doors:
            self._add_door(svg_parts, door, offset_x, offset_y, scaled_length, scaled_width, scale)
        
        # Add windows if present
        windows = room_data.get('features', {}).get('windows', [])
        for window in windows:
            self._add_window(svg_parts, window, offset_x, offset_y, scaled_length, scaled_width, scale)
        
        # Add fixtures if present
        fixtures = room_data.get('features', {}).get('fixtures', [])
        for fixture in fixtures:
            self._add_fixture(svg_parts, fixture, offset_x, offset_y, scaled_length, scaled_width, scale)
        
        svg_parts.append('</svg>')
        
        return ''.join(svg_parts)
    
    def generate_complex_room_svg(self, room_data: Dict) -> str:
        """
        Generate SVG for rooms with complex polygon shapes
        
        Args:
            room_data: Dictionary with polygon coordinates or complex features
                {
                    "name": "Room Name",
                    "coordinates": [...] or walls/features structure,
                    "area": 300
                }
        """
        # Check if it's the new format with walls/features
        if isinstance(room_data.get('coordinates'), dict):
            return self.generate_enhanced_room_svg(room_data)
            
        coordinates = room_data.get('coordinates', [])
        if not coordinates:
            return self.generate_room_svg(room_data)
        
        # Find bounding box
        min_x = min(p['x'] for p in coordinates)
        max_x = max(p['x'] for p in coordinates)
        min_y = min(p['y'] for p in coordinates)
        max_y = max(p['y'] for p in coordinates)
        
        room_width = max_x - min_x
        room_height = max_y - min_y
        
        # Calculate scale
        scale = self._calculate_scale(room_width, room_height)
        
        # Center offset
        scaled_width = room_width * scale
        scaled_height = room_height * scale
        offset_x = (self.canvas_width - scaled_width) / 2
        offset_y = (self.canvas_height - scaled_height) / 2
        
        # Build SVG
        svg_parts = []
        svg_parts.append(f'<svg width="{self.canvas_width}" height="{self.canvas_height}" xmlns="http://www.w3.org/2000/svg">')
        svg_parts.append(f'<rect width="{self.canvas_width}" height="{self.canvas_height}" fill="white"/>')
        
        # Create polygon points
        points = []
        for coord in coordinates:
            x = (coord['x'] - min_x) * scale + offset_x
            y = (coord['y'] - min_y) * scale + offset_y
            points.append(f"{x},{y}")
        
        points_str = " ".join(points)
        svg_parts.append(f'<polygon points="{points_str}" fill="none" stroke="black" stroke-width="2"/>')
        
        # Add room name and area
        center_x = offset_x + scaled_width / 2
        center_y = offset_y + scaled_height / 2
        
        room_name = room_data.get('name', 'Room')
        area = room_data.get('area', 0)
        
        svg_parts.append(f'''
            <text x="{center_x}" y="{center_y - 10}" 
                  text-anchor="middle" font-size="16" font-weight="bold" font-family="Arial">
                {room_name}
            </text>
            <text x="{center_x}" y="{center_y + 10}" 
                  text-anchor="middle" font-size="14" font-family="Arial">
                {area} sq ft
            </text>
        ''')
        
        svg_parts.append('</svg>')
        
        return ''.join(svg_parts)
    
    def _calculate_scale(self, length: float, width: float) -> float:
        """Calculate scale factor to fit room in canvas"""
        available_width = self.canvas_width - 2 * self.padding
        available_height = self.canvas_height - 2 * self.padding
        
        scale_x = available_width / length if length > 0 else 1
        scale_y = available_height / width if width > 0 else 1
        
        return min(scale_x, scale_y)
    
    def _add_door(self, svg_parts: List[str], door: Dict, 
                  offset_x: float, offset_y: float, 
                  scaled_length: float, scaled_width: float, scale: float):
        """Add door to SVG"""
        wall = door.get('wall', door.get('location', 'south'))  # Support both 'wall' and 'location'
        door_width = door.get('width', 3) * scale
        position = door.get('position', 0.5)  # Position as percentage along wall
        
        if wall == 'north':
            x = offset_x + scaled_length * position - door_width / 2
            y = offset_y
            svg_parts.append(f'''
                <rect x="{x}" y="{y - 3}" width="{door_width}" height="6" 
                      fill="white" stroke="black" stroke-width="1"/>
            ''')
        elif wall == 'south':
            x = offset_x + scaled_length * position - door_width / 2
            y = offset_y + scaled_width
            svg_parts.append(f'''
                <rect x="{x}" y="{y - 3}" width="{door_width}" height="6" 
                      fill="white" stroke="black" stroke-width="1"/>
            ''')
        elif wall == 'east':
            x = offset_x + scaled_length
            y = offset_y + scaled_width * position - door_width / 2
            svg_parts.append(f'''
                <rect x="{x - 3}" y="{y}" width="6" height="{door_width}" 
                      fill="white" stroke="black" stroke-width="1"/>
            ''')
        elif wall == 'west':
            x = offset_x
            y = offset_y + scaled_width * position - door_width / 2
            svg_parts.append(f'''
                <rect x="{x - 3}" y="{y}" width="6" height="{door_width}" 
                      fill="white" stroke="black" stroke-width="1"/>
            ''')
    
    def _add_window(self, svg_parts: List[str], window: Dict,
                    offset_x: float, offset_y: float,
                    scaled_length: float, scaled_width: float, scale: float):
        """Add window to SVG"""
        wall = window.get('wall', window.get('location', 'north'))  # Support both 'wall' and 'location'
        window_width = window.get('width', 4) * scale
        position = window.get('position', 0.5)  # Position as percentage along wall
        
        if wall == 'north':
            x = offset_x + scaled_length * position - window_width / 2
            y = offset_y
            svg_parts.append(f'''
                <line x1="{x}" y1="{y}" x2="{x + window_width}" y2="{y}" 
                      stroke="blue" stroke-width="3"/>
            ''')
        elif wall == 'south':
            x = offset_x + scaled_length * position - window_width / 2
            y = offset_y + scaled_width
            svg_parts.append(f'''
                <line x1="{x}" y1="{y}" x2="{x + window_width}" y2="{y}" 
                      stroke="blue" stroke-width="3"/>
            ''')
        elif wall == 'east':
            x = offset_x + scaled_length
            y = offset_y + scaled_width * position - window_width / 2
            svg_parts.append(f'''
                <line x1="{x}" y1="{y}" x2="{x}" y2="{y + window_width}" 
                      stroke="blue" stroke-width="3"/>
            ''')
        elif wall == 'west':
            x = offset_x
            y = offset_y + scaled_width * position - window_width / 2
            svg_parts.append(f'''
                <line x1="{x}" y1="{y}" x2="{x}" y2="{y + window_width}" 
                      stroke="blue" stroke-width="3"/>
            ''')
    
    def _add_fixture(self, svg_parts: List[str], fixture: Dict,
                     offset_x: float, offset_y: float,
                     scaled_length: float, scaled_width: float, scale: float):
        """Add fixture (island, sink, toilet, etc.) to SVG"""
        fixture_type = fixture.get('type', '')
        location = fixture.get('location', '')
        dimensions = fixture.get('dimensions', '')
        
        # Define relative positions based on location descriptions
        positions = {
            'island': (0.5, 0.5),  # Center
            'north': (0.5, 0.15),
            'south': (0.5, 0.85),
            'east': (0.85, 0.5),
            'west': (0.15, 0.5),
            'northeast': (0.85, 0.15),
            'northwest': (0.15, 0.15),
            'southeast': (0.85, 0.85),
            'southwest': (0.15, 0.85),
            'north wall': (0.5, 0.1),
            'south wall': (0.5, 0.9),
            'east wall': (0.9, 0.5),
            'west wall': (0.1, 0.5)
        }
        
        # Get position or default to center
        if location in positions:
            rel_x, rel_y = positions[location]
        else:
            rel_x, rel_y = 0.5, 0.5
        
        x = offset_x + scaled_length * rel_x
        y = offset_y + scaled_width * rel_y
        
        if fixture_type == 'island':
            # Draw island as a rectangle
            island_width = 6 * scale  # 6 feet default
            island_height = 3 * scale  # 3 feet default
            
            # Parse dimensions if provided (e.g., "6' x 3'")
            if dimensions and 'x' in dimensions:
                parts = dimensions.replace("'", "").split('x')
                if len(parts) == 2:
                    try:
                        island_width = float(parts[0].strip()) * scale
                        island_height = float(parts[1].strip()) * scale
                    except:
                        pass
            
            svg_parts.append(f'''
                <rect x="{x - island_width/2}" y="{y - island_height/2}" 
                      width="{island_width}" height="{island_height}" 
                      fill="lightgray" stroke="black" stroke-width="1.5"/>
                <text x="{x}" y="{y}" 
                      text-anchor="middle" font-size="10" font-family="Arial">
                    Island
                </text>
            ''')
        
        elif fixture_type == 'sink':
            # Draw sink as a circle
            sink_radius = 0.75 * scale
            svg_parts.append(f'''
                <circle cx="{x}" cy="{y}" r="{sink_radius}" 
                        fill="lightblue" stroke="black" stroke-width="1"/>
                <text x="{x}" y="{y + sink_radius + 10}" 
                      text-anchor="middle" font-size="8" font-family="Arial">
                    Sink
                </text>
            ''')
        
        elif fixture_type == 'range':
            # Draw range as a square
            range_size = 2.5 * scale
            svg_parts.append(f'''
                <rect x="{x - range_size/2}" y="{y - range_size/2}" 
                      width="{range_size}" height="{range_size}" 
                      fill="gray" stroke="black" stroke-width="1"/>
                <text x="{x}" y="{y}" 
                      text-anchor="middle" font-size="8" font-family="Arial" fill="white">
                    Range
                </text>
            ''')
        
        elif fixture_type == 'refrigerator':
            # Draw refrigerator as a rectangle
            fridge_width = 3 * scale
            fridge_height = 2.5 * scale
            svg_parts.append(f'''
                <rect x="{x - fridge_width/2}" y="{y - fridge_height/2}" 
                      width="{fridge_width}" height="{fridge_height}" 
                      fill="darkgray" stroke="black" stroke-width="1"/>
                <text x="{x}" y="{y}" 
                      text-anchor="middle" font-size="8" font-family="Arial" fill="white">
                    Fridge
                </text>
            ''')
        
        elif fixture_type == 'shower':
            # Draw shower as a square with pattern
            shower_size = 5 * scale  # Default 5x5
            if dimensions and 'x' in dimensions:
                parts = dimensions.replace("'", "").split('x')
                if len(parts) == 2:
                    try:
                        shower_size = float(parts[0].strip()) * scale
                    except:
                        pass
            
            svg_parts.append(f'''
                <rect x="{x - shower_size/2}" y="{y - shower_size/2}" 
                      width="{shower_size}" height="{shower_size}" 
                      fill="none" stroke="blue" stroke-width="2" stroke-dasharray="5,5"/>
                <text x="{x}" y="{y}" 
                      text-anchor="middle" font-size="10" font-family="Arial">
                    Shower
                </text>
            ''')
        
        elif fixture_type == 'double_vanity' or fixture_type == 'vanity':
            # Draw vanity as a rectangle
            vanity_width = 5 * scale  # Default 60" = 5 feet
            vanity_height = 2 * scale
            
            if dimensions and '"' in dimensions:
                try:
                    vanity_width = float(dimensions.replace('"', '').strip()) / 12 * scale
                except:
                    pass
            
            svg_parts.append(f'''
                <rect x="{x - vanity_width/2}" y="{y - vanity_height/2}" 
                      width="{vanity_width}" height="{vanity_height}" 
                      fill="lightgray" stroke="black" stroke-width="1"/>
                <text x="{x}" y="{y}" 
                      text-anchor="middle" font-size="8" font-family="Arial">
                    Vanity
                </text>
            ''')
        
        elif fixture_type == 'toilet':
            # Draw toilet as an oval
            toilet_width = 1.5 * scale
            toilet_height = 2 * scale
            svg_parts.append(f'''
                <ellipse cx="{x}" cy="{y}" rx="{toilet_width/2}" ry="{toilet_height/2}" 
                         fill="white" stroke="black" stroke-width="1"/>
                <text x="{x}" y="{y + toilet_height/2 + 10}" 
                      text-anchor="middle" font-size="8" font-family="Arial">
                    WC
                </text>
            ''')

    def generate_enhanced_room_svg(self, room_data: Dict) -> str:
        """
        Generate SVG for rooms with enhanced wall and feature data
        
        Args:
            room_data: Dictionary with walls and features structure
        """
        coordinates_data = room_data.get('coordinates', {})
        walls = coordinates_data.get('walls', [])
        features = coordinates_data.get('features', [])
        
        if not walls:
            return self.generate_room_svg(room_data)
        
        # Calculate bounding box from walls
        all_points = []
        for wall in walls:
            all_points.extend([wall['start'], wall['end']])
        
        min_x = min(p['x'] for p in all_points)
        max_x = max(p['x'] for p in all_points)
        min_y = min(p['y'] for p in all_points)
        max_y = max(p['y'] for p in all_points)
        
        width = max_x - min_x
        height = max_y - min_y
        
        # Calculate scale
        scale = self._calculate_scale(width, height)
        scaled_width = width * scale
        scaled_height = height * scale
        
        # Center in canvas
        offset_x = (self.canvas_width - scaled_width) / 2
        offset_y = (self.canvas_height - scaled_height) / 2
        
        svg_parts = []
        svg_parts.append(f'''
            <svg width="{self.canvas_width}" height="{self.canvas_height}" 
                 xmlns="http://www.w3.org/2000/svg">
        ''')
        
        # Draw walls
        for wall in walls:
            x1 = offset_x + (wall['start']['x'] - min_x) * scale
            y1 = offset_y + (wall['start']['y'] - min_y) * scale
            x2 = offset_x + (wall['end']['x'] - min_x) * scale
            y2 = offset_y + (wall['end']['y'] - min_y) * scale
            
            stroke_width = 3 if wall.get('type') == 'exterior' else 2
            svg_parts.append(f'''
                <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" 
                      stroke="black" stroke-width="{stroke_width}"/>
            ''')
        
        # Draw features (doors, windows)
        for feature in features:
            feature_type = feature.get('type')
            position = feature.get('position', {})
            
            if feature_type == 'door':
                x = offset_x + (position.get('x', 0) - min_x) * scale
                y = offset_y + (position.get('y', 0) - min_y) * scale
                width = feature.get('width', 3) * scale
                
                # Determine orientation based on wall
                wall_ref = feature.get('wall')
                if wall_ref and isinstance(wall_ref, int) and wall_ref < len(walls):
                    wall = walls[wall_ref]
                    if abs(wall['start']['x'] - wall['end']['x']) > abs(wall['start']['y'] - wall['end']['y']):
                        # Horizontal wall
                        svg_parts.append(f'''
                            <rect x="{x - width/2}" y="{y - 3}" width="{width}" height="6" 
                                  fill="white" stroke="black" stroke-width="1"/>
                        ''')
                    else:
                        # Vertical wall
                        svg_parts.append(f'''
                            <rect x="{x - 3}" y="{y - width/2}" width="6" height="{width}" 
                                  fill="white" stroke="black" stroke-width="1"/>
                        ''')
            
            elif feature_type == 'window':
                x = offset_x + (position.get('x', 0) - min_x) * scale
                y = offset_y + (position.get('y', 0) - min_y) * scale
                width = feature.get('width', 4) * scale
                
                # Determine orientation based on wall
                wall_ref = feature.get('wall')
                if wall_ref and isinstance(wall_ref, int) and wall_ref < len(walls):
                    wall = walls[wall_ref]
                    if abs(wall['start']['x'] - wall['end']['x']) > abs(wall['start']['y'] - wall['end']['y']):
                        # Horizontal wall
                        svg_parts.append(f'''
                            <line x1="{x - width/2}" y1="{y}" x2="{x + width/2}" y2="{y}" 
                                  stroke="blue" stroke-width="3"/>
                        ''')
                    else:
                        # Vertical wall
                        svg_parts.append(f'''
                            <line x1="{x}" y1="{y - width/2}" x2="{x}" y2="{y + width/2}" 
                                  stroke="blue" stroke-width="3"/>
                        ''')
        
        # Add room name and area
        room_name = room_data.get('name', 'Room')
        area = room_data.get('area', 0)
        center_x = offset_x + scaled_width / 2
        center_y = offset_y + scaled_height / 2
        
        svg_parts.append(f'''
            <text x="{center_x}" y="{center_y - 10}" 
                  text-anchor="middle" font-size="16" font-weight="bold" font-family="Arial">
                {room_name}
            </text>
            <text x="{center_x}" y="{center_y + 10}" 
                  text-anchor="middle" font-size="14" font-family="Arial">
                {area} sq ft
            </text>
        ''')
        
        svg_parts.append('</svg>')
        
        return ''.join(svg_parts)

    def generate_measurement_table_html(self, room_data: Dict) -> str:
        """Generate HTML table with room measurements"""
        measurements = room_data.get('measurements', {})
        work_items = room_data.get('work_items', {})
        
        html = '<table class="room-measurements">'
        html += '<thead><tr><th colspan="2">Room Measurements</th></tr></thead>'
        html += '<tbody>'
        
        # Basic measurements
        if 'area' in room_data:
            html += f'<tr><td>Area</td><td>{room_data["area"]} sq ft</td></tr>'
        if 'perimeter' in room_data:
            html += f'<tr><td>Perimeter</td><td>{room_data["perimeter"]} ft</td></tr>'
        if 'ceiling_height' in measurements:
            html += f'<tr><td>Ceiling Height</td><td>{measurements["ceiling_height"]} ft</td></tr>'
        
        # Dimensions
        dimensions = room_data.get('dimensions', {})
        if 'length' in dimensions:
            html += f'<tr><td>Length</td><td>{dimensions["length"]} ft</td></tr>'
        if 'width' in dimensions:
            html += f'<tr><td>Width</td><td>{dimensions["width"]} ft</td></tr>'
        
        html += '</tbody></table>'
        
        # Work items table
        if work_items:
            html += '<table class="work-items">'
            html += '<thead><tr><th colspan="2">Work Items</th></tr></thead>'
            html += '<tbody>'
            
            for item_name, item_data in work_items.items():
                if isinstance(item_data, dict):
                    quantity = item_data.get('quantity', item_data.get('area', ''))
                    unit = item_data.get('unit', 'sq ft')
                    html += f'<tr><td>{item_name.title()}</td><td>{quantity} {unit}</td></tr>'
                else:
                    html += f'<tr><td>{item_name.title()}</td><td>{item_data}</td></tr>'
            
            html += '</tbody></table>'
        
        return html


# Example usage and testing
if __name__ == "__main__":
    # Test data
    sample_room = {
        "name": "Living Room",
        "dimensions": {"length": 20, "width": 15},
        "area": 300,
        "perimeter": 70,
        "measurements": {
            "ceiling_height": 9
        },
        "features": {
            "doors": [
                {"wall": "south", "width": 3, "position": 0.7}
            ],
            "windows": [
                {"wall": "north", "width": 4, "position": 0.3},
                {"wall": "north", "width": 4, "position": 0.7}
            ]
        },
        "work_items": {
            "flooring": {"area": 300, "unit": "sq ft"},
            "painting": {"area": 540, "unit": "sq ft"},
            "baseboard": {"quantity": 70, "unit": "linear ft"}
        }
    }
    
    generator = FloorPlanGenerator()
    svg = generator.generate_room_svg(sample_room)
    table = generator.generate_measurement_table_html(sample_room)
    
    # Save test output
    with open("test_floor_plan.svg", "w") as f:
        f.write(svg)
    
    with open("test_measurement_table.html", "w") as f:
        f.write(f"<html><body>{table}</body></html>")
    
    print("Test files created: test_floor_plan.svg and test_measurement_table.html")