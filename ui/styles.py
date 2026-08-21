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
    color: #F5F5F5;
    background: transparent;
    font-weight: 600;
}
"""

WEEKDAY_STYLE = """
QLabel {
    color: #A8A8A8;
    background: transparent;

    font-family: "Segoe UI";
    font-weight: 600;
    font-size: 10px;
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
    color: #F5F5F5;
    background: transparent;
    border: none;
    font-weight: 600;
}
"""

EVENT_CARD_STYLE = """
QLabel {
    color: #F1F1F1;
    background-color: rgba(255, 255, 255, 20);

    border: none;
    border-radius: 8px;

    padding: 10px;

    font-family: "Segoe UI";
    font-size: 13px;
    font-weight: 400;
}

QLabel:hover {
    background-color: rgba(255, 255, 255, 30);
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
