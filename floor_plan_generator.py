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
    
    def __init__(self, canvas_width: int = 600, canvas_height: int = 400):
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.padding = 40  # Padding around the floor plan
        
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
        
        # Center the room in canvas
        offset_x = (self.canvas_width - scaled_length) / 2
        offset_y = (self.canvas_height - scaled_width) / 2
        
        # Start building SVG
        svg_parts = []
        svg_parts.append(f'<svg width="{self.canvas_width}" height="{self.canvas_height}" xmlns="http://www.w3.org/2000/svg">')
        
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
        
        svg_parts.append('</svg>')
        
        return ''.join(svg_parts)
    
    def generate_complex_room_svg(self, room_data: Dict) -> str:
        """
        Generate SVG for rooms with complex polygon shapes
        
        Args:
            room_data: Dictionary with polygon coordinates
                {
                    "name": "Room Name",
                    "coordinates": [
                        {"x": 0, "y": 0},
                        {"x": 20, "y": 0},
                        {"x": 20, "y": 15},
                        {"x": 0, "y": 15}
                    ],
                    "area": 300
                }
        """
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
        wall = door.get('wall', 'south')
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
        wall = window.get('wall', 'north')
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