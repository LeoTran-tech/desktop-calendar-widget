OUTER_CONTAINER_STYLE = """
QWidget#outerContainer {
    background-color: rgba(28, 27, 22, 235);
    border-radius: 18px;
}
"""

TRANSPARENT_PANEL_STYLE = """
background: transparent;
border: none;
"""

TITLE_STYLE = """
QLabel {
    color: white;
    background: transparent;
}
"""

WEEKDAY_STYLE = """
QLabel {
    color: #aaaaaa;
    background: transparent;
    font-weight: bold;
    font-size: 11px;
}
"""

DAY_STYLE = """
QLabel {
    background: transparent;
    color: white;
    font-size: 14px;
}
"""

TODAY_STYLE = """
QLabel {
    background-color: #4285F4;
    color: white;
    border-radius: 15px;
    font-weight: bold;
    font-size: 14px;
}
"""

EVENT_DAY_STYLE = """
QLabel {
    background: transparent;
    color: #8ab4f8;
    font-weight: bold;
    font-size: 14px;
}
"""

UPCOMING_TITLE_STYLE = """
QLabel {
    color: white;
    background: transparent;
    border: none;
}
"""

EVENT_CARD_STYLE = """
QLabel {
    color: white;
    background-color: rgba(255, 255, 255, 20);
    border: none;
    border-radius: 8px;
    padding: 10px;
    font-family: "Segoe UI";
    font-size: 14px;
    font-weight: 500;
}
QLabel:hover {
    background-color: rgba(255, 255, 255, 35);
}
"""

EMPTY_STYLE = """
QLabel {
    color: #AAAAAA;
    background: transparent;
    border: none;
    padding: 8px;
}
"""

SCROLL_AREA_STYLE = """
QScrollArea {
    background: transparent;
    border: none;
}
QScrollArea > QWidget > QWidget {
    background: transparent;
}
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: rgba(255, 255, 255, 80);
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: transparent;
}
"""
