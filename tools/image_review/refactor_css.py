import re

CSS_PATH = '/home/pauli/temp/AIFX013_VCR/tools/image_review/static/css/styles.css'

with open(CSS_PATH, 'r') as f:
    css = f.read()

# Base colors map to variable names
COLOR_MAP = {
    '#1a1a2e': '--bg-main',
    '#16213e': '--bg-panel',
    '#0f3460': '--bg-hover',
    '#000000': '--bg-black',
    '#000': '--bg-black',
    '#111': '--bg-darker',
    '#222': '--bg-dark',
    '#2a2a3e': '--bg-lighter',
    '#333': '--border-color',
    '#444': '--border-light',
    '#666': '--text-muted-dark',
    '#888': '--text-muted',
    '#aaa': '--text-secondary',
    '#ccc': '--text-light',
    '#ddd': '--text-lighter',
    '#eee': '--text-main',
    '#fff': '--text-white',
    '#ffffff': '--text-white',
    '#4a69bd': '--accent-color',
    '#5c7cfa': '--accent-hover',
    '#e74c3c': '--danger-color',
    '#c0392b': '--danger-hover',
    '#27ae60': '--success-color',
    '#2ecc71': '--success-hover',
    '#f39c12': '--warning-color',
    '#FF9800': '--warning-alt',
    
    # Specific semantic flags
    '#e91e63': '--flag-pink',
    '#c2185b': '--flag-pink-dark',
    '#9b59b6': '--flag-purple',
    '#8e44ad': '--flag-purple-dark',
    '#4CAF50': '--flag-green-alt',
    '#388E3C': '--flag-green-dark',
    '#2196F3': '--flag-blue-alt',
    '#1976D2': '--flag-blue-dark',
    
    # RGBA equivalents for accent
    'rgba(74, 105, 189, 0.9)': '--accent-90',
    'rgba(74, 105, 189, 0.8)': '--accent-80',
    'rgba(74, 105, 189, 0.7)': '--accent-70',
    'rgba(74, 105, 189, 0.5)': '--accent-50',
    'rgba(74, 105, 189, 0.4)': '--accent-40',
    'rgba(74, 105, 189, 0.3)': '--accent-30',
    'rgba(74, 105, 189, 0.25)': '--accent-25',
    'rgba(74, 105, 189, 0.2)': '--accent-20',
    'rgba(74, 105, 189, 0.15)': '--accent-15',
    'rgba(74, 105, 189, 0.1)': '--accent-10',

    # Modals / overlays
    'rgba(0, 0, 0, 0.9)': '--overlay-90',
    'rgba(0, 0, 0, 0.85)': '--overlay-85',
    'rgba(0, 0, 0, 0.8)': '--overlay-80',
    'rgba(0, 0, 0, 0.75)': '--overlay-75',
    'rgba(0, 0, 0, 0.7)': '--overlay-70',
    'rgba(0, 0, 0, 0.6)': '--overlay-60',
    'rgba(0, 0, 0, 0.5)': '--overlay-50',
    'rgba(0, 0, 0, 0.4)': '--overlay-40',
    'rgba(0, 0, 0, 0.3)': '--overlay-30',
    'rgba(0, 0, 0, 0.2)': '--overlay-20',
    
    'rgba(255, 255, 255, 0.6)': '--white-60',
    'rgba(255, 255, 255, 0.2)': '--white-20',
    'rgba(255, 255, 255, 0.15)': '--white-15',
    'rgba(255, 255, 255, 0.1)': '--white-10',
    'rgba(255, 255, 255, 0.05)': '--white-05',
    'rgba(255, 255, 255, 0.03)': '--white-03',

    # Danger/Success alphas
    'rgba(231, 76, 60, 0.9)': '--danger-90',
    'rgba(231, 76, 60, 0.8)': '--danger-80',
    'rgba(231, 76, 60, 0.5)': '--danger-50',
    'rgba(231, 76, 60, 0.4)': '--danger-40',
    'rgba(231, 76, 60, 0.3)': '--danger-30',
    'rgba(231, 76, 60, 0.1)': '--danger-10',

    'rgba(39, 174, 96, 0.9)': '--success-90',
    'rgba(39, 174, 96, 0.8)': '--success-80',
    'rgba(39, 174, 96, 0.1)': '--success-10',

    'rgba(243, 156, 18, 0.5)': '--warning-50',
    'rgba(243, 156, 18, 0.1)': '--warning-10',
    'rgba(255, 152, 0, 0.2)': '--warning-alt-20',
    
    'rgba(22, 33, 62, 0.98)': '--bg-panel-98',
    'rgba(60, 60, 60, 0.9)': '--bg-tooltip-90',
    'rgba(76, 175, 80, 0.2)': '--success-alt-20',
}

# Reverse map for the :root declaration
variables_decl = ":root,\n[data-theme='dark'] {\n"
for color, var_name in COLOR_MAP.items():
    variables_decl += f"    {var_name}: {color};\n"
variables_decl += "}\n\n"

# Add Light Theme
variables_decl += "[data-theme='light'] {\n"
variables_decl += """    --bg-main: #f5f6fa;
    --bg-panel: #ffffff;
    --bg-hover: #e8ecef;
    --bg-black: #ffffff;
    --bg-darker: #f0f0f0;
    --bg-dark: #e0e0e0;
    --bg-lighter: #dcdde1;
    --border-color: #dcdde1;
    --border-light: #ececec;
    --text-muted-dark: #a0a0a0;
    --text-muted: #7f8fa6;
    --text-secondary: #718093;
    --text-light: #353b48;
    --text-lighter: #2f3640;
    --text-main: #2f3640;
    --text-white: #000000;
    --accent-color: #0097e6;
    --accent-hover: #00a8ff;
    --bg-panel-98: rgba(255, 255, 255, 0.98);
    --bg-tooltip-90: rgba(240, 240, 240, 0.9);
    
    --overlay-90: rgba(255, 255, 255, 0.9);
    --overlay-85: rgba(255, 255, 255, 0.85);
    --overlay-80: rgba(255, 255, 255, 0.8);
    --overlay-75: rgba(255, 255, 255, 0.75);
    --overlay-70: rgba(255, 255, 255, 0.7);
    --overlay-60: rgba(255, 255, 255, 0.6);
    --overlay-50: rgba(255, 255, 255, 0.5);
    --overlay-40: rgba(255, 255, 255, 0.4);
    --overlay-30: rgba(255, 255, 255, 0.3);
    --overlay-20: rgba(255, 255, 255, 0.2);
    
    --white-60: rgba(0, 0, 0, 0.6);
    --white-20: rgba(0, 0, 0, 0.2);
    --white-15: rgba(0, 0, 0, 0.15);
    --white-10: rgba(0, 0, 0, 0.1);
    --white-05: rgba(0, 0, 0, 0.05);
    --white-03: rgba(0, 0, 0, 0.03);
    
    --accent-90: rgba(0, 151, 230, 0.9);
    --accent-80: rgba(0, 151, 230, 0.8);
    --accent-70: rgba(0, 151, 230, 0.7);
    --accent-50: rgba(0, 151, 230, 0.5);
    --accent-40: rgba(0, 151, 230, 0.4);
    --accent-30: rgba(0, 151, 230, 0.3);
    --accent-25: rgba(0, 151, 230, 0.25);
    --accent-20: rgba(0, 151, 230, 0.2);
    --accent-15: rgba(0, 151, 230, 0.15);
    --accent-10: rgba(0, 151, 230, 0.1);
"""
variables_decl += "}\n\n"

# Replace colors in CSS
# Sort by length descending to avoid replacing '#000' inside '#000000'
sorted_colors = sorted(COLOR_MAP.keys(), key=len, reverse=True)

for color in sorted_colors:
    var_name = COLOR_MAP[color]
    # Use word boundaries or exact match to replace
    # We must escape parens for rgba
    pattern = re.escape(color)
    # If it is a hex color, make sure it's not part of a larger hex
    if color.startswith('#'):
        pattern += r'(?![0-9a-fA-F])'
    
    css = re.sub(pattern, f'var({var_name})', css, flags=re.IGNORECASE)

# Now, we also want to remove 'var(--border-color)0000' artifacts if any? 
# Wait, let's just write.
new_css = variables_decl + css

with open(CSS_PATH, 'w') as f:
    f.write(new_css)
print("CSS refactored!")
