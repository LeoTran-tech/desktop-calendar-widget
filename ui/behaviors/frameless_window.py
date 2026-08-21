from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import QWidget


class FramelessWindowBehavior:

    def _init_frameless_behavior(
        self,
        resize_margin: int = 10,
    ) -> None:

        self.resize_margin = resize_margin

        self.resize_edges = None
        self.resize_start_geometry = None
        self.resize_start_mouse = None
        self.drag_position = None

        # Chỉ dùng boolean này để lock drag/resize
        self.position_locked = True

        self._install_mouse_tracking(self)

    def set_position_locked(
        self,
        locked: bool,
    ) -> None:

        self.position_locked = locked

        # Hủy drag/resize đang diễn ra
        self.resize_edges = None
        self.resize_start_geometry = None
        self.resize_start_mouse = None
        self.drag_position = None

        self.setCursor(Qt.ArrowCursor)

    def _install_mouse_tracking(
        self,
        widget: QWidget,
    ) -> None:

        widget.setMouseTracking(True)
        widget.installEventFilter(self)

        for child in widget.findChildren(QWidget):
            child.setMouseTracking(True)
            child.installEventFilter(self)

    def _get_resize_edges(self, global_pos):

        local = self.mapFromGlobal(global_pos)

        x = local.x()
        y = local.y()

        width = self.width()
        height = self.height()

        margin = self.resize_margin

        return (
            x <= margin,
            x >= width - margin,
            y <= margin,
            y >= height - margin,
        )

    def _update_cursor(self, global_pos) -> None:

        # LOCKED → luôn cursor bình thường
        if self.position_locked:
            self.setCursor(Qt.ArrowCursor)
            return

        left, right, top, bottom = (
            self._get_resize_edges(global_pos)
        )

        if (
            (left and top)
            or (right and bottom)
        ):
            self.setCursor(Qt.SizeFDiagCursor)

        elif (
            (right and top)
            or (left and bottom)
        ):
            self.setCursor(Qt.SizeBDiagCursor)

        elif left or right:
            self.setCursor(Qt.SizeHorCursor)

        elif top or bottom:
            self.setCursor(Qt.SizeVerCursor)

        else:
            self.setCursor(Qt.ArrowCursor)

    def eventFilter(self, obj, event):

        # Các button/link vẫn click được bình thường
        if obj.property("interactive"):
            return False

        # ============================================================
        # LOCKED
        # Không xử lý drag hoặc resize.
        # ============================================================

        if self.position_locked:

            if event.type() == QEvent.MouseMove:
                self.setCursor(Qt.ArrowCursor)

            return False

        # ============================================================
        # NORMAL / UNLOCKED
        # ============================================================

        if event.type() == QEvent.MouseMove:

            global_pos = (
                event.globalPosition().toPoint()
            )

            # Resize
            if (
                event.buttons() & Qt.LeftButton
                and self.resize_edges
            ):
                self._perform_resize(global_pos)
                return True

            # Drag
            if (
                event.buttons() & Qt.LeftButton
                and self.drag_position is not None
            ):
                self.move(
                    global_pos
                    - self.drag_position
                )

                return True

            self._update_cursor(global_pos)

        elif event.type() == QEvent.MouseButtonPress:

            if event.button() == Qt.LeftButton:

                global_pos = (
                    event.globalPosition().toPoint()
                )

                edges = self._get_resize_edges(
                    global_pos
                )

                # Resize
                if any(edges):

                    self.resize_edges = edges

                    self.resize_start_geometry = (
                        self.geometry()
                    )

                    self.resize_start_mouse = (
                        global_pos
                    )

                    return True

                # Drag
                self.drag_position = (
                    global_pos
                    - self.frameGeometry().topLeft()
                )

                return True

        elif event.type() == QEvent.MouseButtonRelease:

            if event.button() == Qt.LeftButton:

                self.resize_edges = None
                self.resize_start_geometry = None
                self.resize_start_mouse = None
                self.drag_position = None

                return True

        return False

    def _perform_resize(
        self,
        global_pos,
    ) -> None:

        if (
            self.resize_start_geometry is None
            or self.resize_edges is None
        ):
            return

        left, right, top, bottom = (
            self.resize_edges
        )

        delta = (
            global_pos
            - self.resize_start_mouse
        )

        rect = self.resize_start_geometry

        x = rect.x()
        y = rect.y()

        width = rect.width()
        height = rect.height()

        min_width = self.minimumWidth()
        min_height = self.minimumHeight()

        if left:

            new_width = width - delta.x()

            if new_width >= min_width:
                x = rect.x() + delta.x()
                width = new_width

        if right:

            width = max(
                min_width,
                width + delta.x(),
            )

        if top:

            new_height = height - delta.y()

            if new_height >= min_height:
                y = rect.y() + delta.y()
                height = new_height

        if bottom:

            height = max(
                min_height,
                height + delta.y(),
            )

        self.setGeometry(
            x,
            y,
            width,
            height,
        )

    def mouseDoubleClickEvent(
        self,
        event,
    ) -> None:

        if event.button() == Qt.RightButton:
            self.close()
            return

        super().mouseDoubleClickEvent(event)