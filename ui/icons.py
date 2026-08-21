from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap


ICON_PRIMARY = "#F5F5F5"
ICON_SECONDARY = "#D3D7DC"
ICON_ACCENT = "#8AB4F8"
ICON_DANGER = "#FF8585"


def make_icon(
    name: str,
    color: str = ICON_PRIMARY,
    size: int = 24,
    stroke_width: float = 1.8,
) -> QIcon:
    """Return a small monochrome line icon drawn with Qt itself.

    Keeping icons vector-like and single-colour avoids platform emoji styling
    and makes the widget visually consistent on Windows.
    """
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)

    scale = size / 24.0
    pen = QPen(QColor(color), stroke_width * scale)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)
    painter.scale(scale, scale)

    draw = _DRAWERS.get(name)
    if draw is not None:
        draw(painter)

    painter.end()
    return QIcon(pixmap)


def _refresh(p: QPainter) -> None:
    p.drawArc(QRectF(4.5, 4.5, 15, 15), 35 * 16, 285 * 16)
    p.drawLine(QPointF(17.0, 4.7), QPointF(20.0, 5.0))
    p.drawLine(QPointF(20.0, 5.0), QPointF(19.2, 8.0))


def _back(p: QPainter) -> None:
    p.drawLine(QPointF(19, 12), QPointF(5, 12))
    p.drawLine(QPointF(5, 12), QPointF(10, 7))
    p.drawLine(QPointF(5, 12), QPointF(10, 17))


def _external(p: QPainter) -> None:
    p.drawRoundedRect(QRectF(4.5, 7.5, 12, 12), 2, 2)
    p.drawLine(QPointF(11, 13), QPointF(20, 4))
    p.drawLine(QPointF(14, 4), QPointF(20, 4))
    p.drawLine(QPointF(20, 4), QPointF(20, 10))


def _lock(p: QPainter) -> None:
    p.drawRoundedRect(QRectF(5.5, 10.5, 13, 9.5), 2.2, 2.2)
    path = QPainterPath()
    path.moveTo(8, 10.5)
    path.lineTo(8, 8.0)
    path.cubicTo(8, 4.8, 10.0, 3.0, 12.0, 3.0)
    path.cubicTo(14.0, 3.0, 16.0, 4.8, 16.0, 8.0)
    path.lineTo(16.0, 10.5)
    p.drawPath(path)
    p.drawEllipse(QPointF(12, 15.0), 0.9, 0.9)


def _unlock(p: QPainter) -> None:
    p.drawRoundedRect(QRectF(5.5, 10.5, 13, 9.5), 2.2, 2.2)
    path = QPainterPath()
    path.moveTo(8, 10.5)
    path.lineTo(8, 8.0)
    path.cubicTo(8, 4.8, 10.0, 3.0, 12.0, 3.0)
    path.cubicTo(14.0, 3.0, 16.0, 4.8, 16.0, 8.0)
    path.lineTo(19.0, 8.0)
    p.drawPath(path)
    p.drawEllipse(QPointF(12, 15.0), 0.9, 0.9)


def _close(p: QPainter) -> None:
    # Simple line X matching the rest of the monochrome control icons.
    p.drawLine(QPointF(7, 7), QPointF(17, 17))
    p.drawLine(QPointF(17, 7), QPointF(7, 17))


def _location(p: QPainter) -> None:
    path = QPainterPath()
    path.moveTo(12, 21)
    path.cubicTo(10.5, 18.8, 6.5, 14.8, 6.5, 10.2)
    path.cubicTo(6.5, 6.8, 8.9, 4.5, 12, 4.5)
    path.cubicTo(15.1, 4.5, 17.5, 6.8, 17.5, 10.2)
    path.cubicTo(17.5, 14.8, 13.5, 18.8, 12, 21)
    p.drawPath(path)
    p.drawEllipse(QPointF(12, 10.0), 2.1, 2.1)


def _link(p: QPainter) -> None:
    # Two interlocking rounded links represented by opposing curves.
    a = QPainterPath()
    a.moveTo(9.7, 8.0)
    a.lineTo(7.5, 8.0)
    a.cubicTo(4.7, 8.0, 3.5, 10.0, 3.5, 12.0)
    a.cubicTo(3.5, 14.0, 4.7, 16.0, 7.5, 16.0)
    a.lineTo(10.0, 16.0)
    p.drawPath(a)

    b = QPainterPath()
    b.moveTo(14.0, 8.0)
    b.lineTo(16.5, 8.0)
    b.cubicTo(19.3, 8.0, 20.5, 10.0, 20.5, 12.0)
    b.cubicTo(20.5, 14.0, 19.3, 16.0, 16.5, 16.0)
    b.lineTo(14.3, 16.0)
    p.drawPath(b)
    p.drawLine(QPointF(8.5, 12), QPointF(15.5, 12))


def _note(p: QPainter) -> None:
    p.drawRoundedRect(QRectF(5.0, 3.5, 14.0, 17.0), 1.8, 1.8)
    p.drawLine(QPointF(8, 8), QPointF(16, 8))
    p.drawLine(QPointF(8, 12), QPointF(16, 12))
    p.drawLine(QPointF(8, 16), QPointF(13.5, 16))


def _bell(p: QPainter) -> None:
    path = QPainterPath()
    path.moveTo(6.5, 16.5)
    path.cubicTo(7.5, 15.0, 7.7, 13.8, 7.7, 10.0)
    path.cubicTo(7.7, 7.2, 9.4, 5.3, 12, 5.3)
    path.cubicTo(14.6, 5.3, 16.3, 7.2, 16.3, 10.0)
    path.cubicTo(16.3, 13.8, 16.5, 15.0, 17.5, 16.5)
    path.closeSubpath()
    p.drawPath(path)
    p.drawLine(QPointF(5.8, 16.5), QPointF(18.2, 16.5))
    p.drawArc(QRectF(10.0, 17.0, 4.0, 3.2), 180 * 16, 180 * 16)


def _person(p: QPainter) -> None:
    p.drawEllipse(QPointF(12, 8), 3.1, 3.1)
    p.drawArc(QRectF(5.5, 12.5, 13, 8.5), 0, 180 * 16)


def _people(p: QPainter) -> None:
    p.drawEllipse(QPointF(9, 8.2), 2.6, 2.6)
    p.drawEllipse(QPointF(15.5, 9.0), 2.2, 2.2)
    p.drawArc(QRectF(3.5, 12.0, 11, 8.5), 0, 180 * 16)
    p.drawArc(QRectF(11.0, 13.0, 9, 7.0), 0, 180 * 16)


_DRAWERS = {
    "refresh": _refresh,
    "back": _back,
    "external": _external,
    "lock": _lock,
    "unlock": _unlock,
    "close": _close,
    "location": _location,
    "link": _link,
    "note": _note,
    "bell": _bell,
    "person": _person,
    "people": _people,
}
