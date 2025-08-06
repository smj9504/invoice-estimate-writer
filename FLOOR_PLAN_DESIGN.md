# Floor Plan Integration Design for Insurance Estimates

## Overview
Design for integrating room-by-room floor plans with measurement data into PDF generation system.

## 1. Architecture Components

### A. Data Flow
```
JSON Input → Floor Plan Parser → Room Extractor → SVG Generator → PDF Template → Final PDF
```

### B. Key Technologies
- **SVG Generation**: For scalable, high-quality floor plans in PDFs
- **Python Libraries**: 
  - `svgwrite` or `drawsvg`: Create SVG floor plans
  - `Pillow`: Process raster images if needed
  - `shapely`: Handle geometric calculations
  - `matplotlib`: Alternative for complex visualizations

## 2. Implementation Strategy

### A. Floor Plan Rendering Options

#### Option 1: SVG-Based (Recommended)
```python
# Advantages:
- Scalable vector graphics
- Perfect for PDF integration
- Small file size
- Can be styled with CSS
- Interactive possibilities

# Implementation:
- Parse room coordinates
- Generate SVG for each room
- Embed directly in HTML template
- WeasyPrint renders to PDF
```

#### Option 2: Canvas/Image-Based
```python
# Advantages:
- More complex visualizations
- Photo-realistic rendering
- Better for complex floor plans

# Disadvantages:
- Larger file sizes
- Potential quality loss
- More processing required
```

## 3. Data Structure Requirements

### A. Optimal JSON Structure for Floor Plans
```json
{
  "project_info": {
    "address": "123 Main St",
    "total_area": 2500
  },
  "floor_plan": {
    "total_dimensions": {
      "width": 50,
      "height": 50,
      "unit": "feet"
    },
    "rooms": [
      {
        "id": "room_001",
        "name": "Living Room",
        "floor": 1,
        "coordinates": {
          "type": "polygon",
          "points": [
            {"x": 0, "y": 0},
            {"x": 20, "y": 0},
            {"x": 20, "y": 15},
            {"x": 0, "y": 15}
          ],
          "unit": "feet"
        },
        "measurements": {
          "area": 300,
          "perimeter": 70,
          "ceiling_height": 9,
          "dimensions": {
            "length": 20,
            "width": 15
          }
        },
        "features": {
          "windows": [
            {"wall": "north", "width": 4, "position": {"x": 10, "y": 0}}
          ],
          "doors": [
            {"wall": "east", "width": 3, "position": {"x": 20, "y": 7}}
          ]
        },
        "work_items": {
          "flooring": {"area": 300, "type": "hardwood"},
          "painting": {"wall_area": 540, "ceiling_area": 300},
          "baseboard": {"linear_feet": 70}
        }
      }
    ],
    "walls": [
      {
        "id": "wall_001",
        "start": {"x": 0, "y": 0},
        "end": {"x": 20, "y": 0},
        "thickness": 0.5,
        "type": "exterior"
      }
    ]
  }
}
```

### B. Alternative: Simple Measurement Format
```json
{
  "rooms": {
    "Living Room": {
      "dimensions": "20' x 15'",
      "area": "300 sq ft",
      "ceiling_height": "9'",
      "shape": "rectangle",
      "measurements": {
        "north_wall": 20,
        "south_wall": 20,
        "east_wall": 15,
        "west_wall": 15
      }
    }
  }
}
```

## 4. Floor Plan Generation Logic

### A. Room Extraction Algorithm
```python
class FloorPlanGenerator:
    def __init__(self, floor_plan_data):
        self.data = floor_plan_data
        self.scale = self.calculate_scale()
    
    def generate_room_svg(self, room):
        # 1. Extract room boundaries
        # 2. Scale to fit page
        # 3. Add measurements as labels
        # 4. Add features (doors, windows)
        # 5. Return SVG string
        pass
    
    def generate_measurement_table(self, room):
        # Create HTML table with measurements
        pass
```

### B. SVG Generation Example
```python
import svgwrite

def create_room_floor_plan(room_data, canvas_width=400, canvas_height=300):
    dwg = svgwrite.Drawing(size=(f'{canvas_width}px', f'{canvas_height}px'))
    
    # Calculate scale
    room_width = room_data['dimensions']['width']
    room_height = room_data['dimensions']['height']
    scale = min(canvas_width / room_width, canvas_height / room_height) * 0.8
    
    # Draw room outline
    points = [(p['x'] * scale, p['y'] * scale) for p in room_data['coordinates']['points']]
    dwg.add(dwg.polygon(points, fill='white', stroke='black', stroke_width=2))
    
    # Add measurements
    # Add room name
    # Add features
    
    return dwg.tostring()
```

## 5. PDF Template Structure

### A. New Template: `insurance_estimate_with_plans.html`
```html
<!-- Main estimate content -->
<div class="estimate-content">
  <!-- Existing estimate tables -->
</div>

<!-- Floor Plans Section -->
<div class="floor-plans-section page-break">
  <h2>Floor Plans and Measurements</h2>
  
  {% for room in rooms %}
  <div class="room-plan-container">
    <h3>{{ room.name }}</h3>
    
    <div class="plan-layout">
      <div class="floor-plan">
        {{ room.svg_plan | safe }}
      </div>
      
      <div class="measurements-panel">
        <table class="measurements-table">
          <tr><th>Area</th><td>{{ room.area }} sq ft</td></tr>
          <tr><th>Perimeter</th><td>{{ room.perimeter }} ft</td></tr>
          <tr><th>Ceiling Height</th><td>{{ room.ceiling_height }} ft</td></tr>
        </table>
        
        <div class="work-items">
          <h4>Work Items</h4>
          <ul>
            {% for item in room.work_items %}
            <li>{{ item.name }}: {{ item.quantity }} {{ item.unit }}</li>
            {% endfor %}
          </ul>
        </div>
      </div>
    </div>
  </div>
  {% endfor %}
</div>
```

## 6. CSS Styling for Floor Plans

```css
.floor-plans-section {
  page-break-before: always;
}

.room-plan-container {
  margin-bottom: 30px;
  page-break-inside: avoid;
}

.plan-layout {
  display: flex;
  gap: 20px;
}

.floor-plan {
  flex: 1;
  border: 1px solid #ccc;
  padding: 10px;
  background: #f9f9f9;
}

.measurements-panel {
  flex: 0 0 300px;
}

.measurements-table {
  width: 100%;
  border-collapse: collapse;
}

.measurements-table th {
  text-align: left;
  padding: 5px;
  background: #e0e0e0;
}
```

## 7. Integration Steps

### Step 1: Install Required Libraries
```bash
pip install svgwrite shapely pillow
```

### Step 2: Create Floor Plan Module
```python
# floor_plan_generator.py
class FloorPlanGenerator:
    # Implementation here
```

### Step 3: Modify PDF Generator
```python
def generate_insurance_estimate_with_plans(data):
    # Process estimate data
    # Generate floor plans for each room
    # Combine with template
    # Generate PDF
```

### Step 4: Update Insurance Estimate Editor
- Add floor plan data upload
- Parse and validate floor plan data
- Pass to PDF generator

## 8. Data Input Recommendations

### Best Format for Your Use Case
Given that you have a total floor plan but need individual room plans:

#### Option A: Provide Room Boundaries
```json
{
  "total_floor_plan": {
    "image_url": "path/to/full_floorplan.png",
    "total_area": 2500,
    "scale": "1:100"
  },
  "room_boundaries": {
    "Living Room": {
      "bounding_box": {
        "top_left": {"x": 100, "y": 100},
        "bottom_right": {"x": 400, "y": 300}
      },
      "area": 300
    }
  }
}
```

#### Option B: Provide Coordinate Lists
```json
{
  "rooms": [
    {
      "name": "Living Room",
      "polygon": [[0,0], [20,0], [20,15], [0,15]],
      "measurements": {
        "area": 300,
        "perimeter": 70
      }
    }
  ]
}
```

#### Option C: Provide Relative Positions
```json
{
  "floor_plan_grid": {
    "rows": 10,
    "cols": 10,
    "cell_size": 5,
    "rooms": [
      {
        "name": "Living Room",
        "cells": [[0,0], [0,1], [0,2], [1,0], [1,1], [1,2]]
      }
    ]
  }
}
```

## 9. Advanced Features (Future Enhancements)

### A. Auto-Detection from Images
- Use OpenCV to detect room boundaries
- OCR for reading measurements
- ML models for room classification

### B. Interactive Features
- Clickable floor plans in digital PDFs
- Zoom capabilities
- Layer toggles (show/hide measurements)

### C. 3D Visualization
- Generate 3D room models
- Export to CAD formats
- VR/AR integration

## 10. Testing Data Structure

Create test files in `measurement/` directory:
```
measurement/
├── sample_floor_plan.json
├── room_coordinates.json
└── measurement_data.json
```

## Recommended Implementation Order

1. **Phase 1**: Basic SVG generation for rectangular rooms
2. **Phase 2**: Support for complex polygonal rooms
3. **Phase 3**: Add measurements and annotations
4. **Phase 4**: Include doors, windows, features
5. **Phase 5**: Advanced visualization options

## Next Steps

1. Confirm which data format works best for you
2. Create sample data files
3. Implement basic SVG generator
4. Create new PDF template
5. Test with sample data
6. Iterate and refine