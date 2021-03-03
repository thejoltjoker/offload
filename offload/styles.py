COLORS = {'primary': '#f9c74f',
          'dark-primary': '#732829',
          'secondary': '#5a8cba',
          'bright-orange': '#f8961e',
          'dark-orange': '#f3722c',
          'red': '#f94144',
          'green': '#90be6d',
          'white': '#ffffff',
          'gray': '#77787c',
          'black': '#1e1f24',
          'bg': '#2b2d33'}

STYLES = f"""
QWidget {{
    background: {COLORS['bg']};
    font-family: 'Source Sans 3';
    font-size: 15px;
    font-weight: 300;
    letter-spacing: 1px;
    color: {COLORS['gray']};
}}

QPushButton {{
    border-radius: 25px 25px;
    border: none;
    background: none;
    font-weight: bold;
    color: {COLORS['primary']};
}}

QPushButton:hover {{
    color: {COLORS['bright-orange']};
}}

QProgressBar {{
    background: {COLORS['black']};
    border-radius: 5px;
}}

QProgressBar::chunk {{
    background: {COLORS['primary']};
    border-radius: 5px;
}}

QComboBox {{
    border: 0;
    border-radius: 16px;
    padding: 4px 12px;
    background: {COLORS['gray']}; 
    color: {COLORS['bg']};
    font-weight: 400;
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    border: 0;
}}

QComboBox::item {{
    color: {COLORS['gray']};
}}

QComboBox::item:on {{
    color: {COLORS['primary']};
}}
QComboBox::item:selected {{
    color: {COLORS['primary']};
}}
QComboBox::down-arrow {{
    background-image: url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2216%22%20height%3D%2216%22%20fill%3D%22currentColor%22%20class%3D%22bi%20bi-caret-down-fill%22%20viewBox%3D%220%200%2016%2016%22%3E%0A%20%20%3Cpath%20d%3D%22M7.247%2011.14L2.451%205.658C1.885%205.013%202.345%204%203.204%204h9.592a1%201%200%200%201%20.753%201.659l-4.796%205.48a1%201%200%200%201-1.506%200z%22%2F%3E%0A%3C%2Fsvg%3E");
    background-repeat: no-repeat;
    background-position: center right;
    background-size: 100%;
    width: 15px;
    height: 15px;
}}

#offload-btn {{
    border-radius: 21px;
    padding: 10px 30px;
    background:{COLORS['primary']}; 
    color: {COLORS['dark-primary']};
}}


#source-title, #dest-title {{
    font-size: 24px;
    font-weight: bold;
    color: {COLORS['white']};
}}

#source-path, #dest-path, a{{
    color: {COLORS['primary']};
}}

#arrow {{
    font-size: 24px;
    color: {COLORS['white']};
}}
"""
