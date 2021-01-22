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
