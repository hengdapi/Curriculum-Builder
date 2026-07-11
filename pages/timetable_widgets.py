"""
课程表拖拽相关的自定义组件。

- TimeTableWidget        课程表预览的表格（支持表格内拖拽 + 接收从暂存区拖来的课程）
- LessonStoragePane      暂存区容器（接收从表格拖来的课程）
- DraggableLessonCard    暂存区的可拖拽卡片（支持点击/拖拽激活课表高亮）
"""

from PySide6.QtCore import Qt, Signal, QMimeData, QPoint
from PySide6.QtGui import (
    QDropEvent, QDragMoveEvent, QDragEnterEvent, QPixmap, QPainter, QBrush,
    QColor, QDrag
)
from PySide6.QtWidgets import QFrame, QVBoxLayout

from locals import *
from style import CardWidget, BodyLabel, TableWidget
from PySide6.QtWidgets import QTableWidgetItem, QAbstractItemView


# =====================================================================
# 课程表预览表格
# =====================================================================
class TimeTableWidget(TableWidget):
    """课表预览表格：支持两种拖拽来源
       1. 表格内（选中项拖到另一格） -> 执行交换或移动
       2. 暂存区卡片（application/x-stored-lesson-card）-> 放入课程
    """

    # 表格内拖到有课程的位置（emit target_item）
    dropdown = Signal(QTableWidgetItem)
    # 表格内拖拽移动时（用于课表详情显示，历史兼容）
    dragmove = Signal(QTableWidgetItem)
    # 拖到暂存区（历史兼容）
    lesson_storage = Signal(QTableWidgetItem)
    # 暂存区卡片拖放到课表某个位置（emit (row, col)）
    stored_lesson_dropped = Signal(tuple)
    # 暂存区卡片在课表上移动时（emit subject_name）
    stored_lesson_dragmove = Signal(Subject)
    # 表格内拖到空位（emit (row, col)）
    table_dropped_on_empty = Signal(tuple)

    # 最近一次被拖动的暂存区卡片（DraggableLessonCard，由 DraggableLessonCard 设置）
    _dragged_card = None
    # 最近一次表格内拖拽的源 item（QTableWidgetItem，由 startDrag 设置）
    _drag_source_item = None

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self._dragged_item = None

    # ---------------------------------------------------------------
    # 表格内拖拽：记录源位置
    # ---------------------------------------------------------------
    def startDrag(self, supportedActions):
        self._dragged_item = self.currentItem()
        TimeTableWidget._drag_source_item = self.currentItem()
        super().startDrag(supportedActions)

    def get_dragged_item(self):
        return self._dragged_item

    # ---------------------------------------------------------------
    # 接收从暂存区拖来的卡片
    # ---------------------------------------------------------------
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasFormat("application/x-stored-lesson-card"):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragMoveEvent):
        if event.mimeData().hasFormat("application/x-stored-lesson-card"):
            # 在课表上移动时，告知 Generate 当前拖拽的学科名（用于实时高亮检查）
            try:
                data = bytes(event.mimeData().data("application/x-stored-lesson-card")).decode("utf-8")
                subject_name = data.split("\n")[0]
                self.stored_lesson_dragmove.emit(str2subject(subject_name))
            except Exception:
                pass
            event.acceptProposedAction()
        else:
            self.dragmove.emit(self.currentItem())
            super().dragMoveEvent(event)

    # ---------------------------------------------------------------
    # 拖放落点处理
    # ---------------------------------------------------------------
    def dropEvent(self, event: QDropEvent):
        # 1) 来自暂存区
        if event.mimeData().hasFormat("application/x-stored-lesson-card"):
            row, col = self._cell_at(event.pos())
            if row < 0 or col < 0:
                return
            event.setDropAction(Qt.CopyAction)
            event.accept()
            self.stored_lesson_dropped.emit((row, col))
            return

        # 2) 表格内拖拽
        row, col = self._cell_at(event.pos())
        if row < 0 or col < 0:
            return
        event.accept()
        if self.item(row, col) is not None and self.item(row, col).text():
            # 拖到有内容的格子
            self.dropdown.emit(self.item(row, col))
        else:
            # 拖到空格子
            self.table_dropped_on_empty.emit((row, col))

    # ---------------------------------------------------------------
    # 辅助：把鼠标坐标换算为 (row, col)，越界返回 (-1, -1)
    # ---------------------------------------------------------------
    def _cell_at(self, pos):
        row = self.rowAt(pos.y())
        col = self.columnAt(pos.x())
        if row < 0 or col < 0 or row >= self.rowCount() or col >= self.columnCount():
            return -1, -1
        return row, col


# =====================================================================
# 暂存区容器
# =====================================================================
class LessonStoragePane(QFrame):
    """接收从课表拖入课程的容器（只发射信号，具体新增卡片由 Generate 处理）"""

    lesson_dropped = Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setAcceptDrops(True)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("QFrame{background: transparent;}")

    def dragEnterEvent(self, event: QDragEnterEvent):
        event.acceptProposedAction()

    def dragMoveEvent(self, event: QDragMoveEvent):
        event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        event.acceptProposedAction()
        self.lesson_dropped.emit()


# =====================================================================
# 可拖拽的暂存课程卡片
# =====================================================================
class DraggableLessonCard(CardWidget):
    """暂存区的课程卡片。
       - 点击（未发生拖动）：发射 card_activated，让课表立刻高亮能否放入
       - 开始拖拽：同样发射 card_activated，然后创建 QDrag 对象并绘制预览图
       - 拖到课表：由 TimeTableWidget / Generate 接收并放入
       - 拖到暂存区内部的其他位置：由 LessonStoragePane 接收并重排卡片顺序
    """

    card_activated = Signal(Subject)

    def __init__(self, subject: Subject, teacher: Teacher, parent=None):
        super().__init__(parent=parent)
        self.subject = subject
        self.teacher = teacher
        self._drag_start_pos = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        label = BodyLabel()
        label.setText(f"{subject}\n{teacher}")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        self.setCursor(Qt.PointingHandCursor)

    # ---------------------------------------------------------------
    # 鼠标事件：区分"点击"和"拖拽"
    # ---------------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start_pos = self._event_pos(event)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        # 点击（移动距离 < 4 像素）→ 视为激活，让课表立刻高亮能否放入
        if event.button() == Qt.LeftButton and self._drag_start_pos is not None:
            current_pos = self._event_pos(event)
            if (current_pos - self._drag_start_pos).manhattanLength() < 4:
                self.card_activated.emit(self.subject)
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        current_pos = self._event_pos(event)
        if self._drag_start_pos is None or (current_pos - self._drag_start_pos).manhattanLength() < 4:
            return

        # 先激活高亮
        self.card_activated.emit(self.subject)

        # 构造拖拽数据
        mime_data = QMimeData()
        payload = f"{self.subject}\n{self.teacher}".encode("utf-8")
        mime_data.setData("application/x-stored-lesson-card", payload)
        mime_data.setText(self.subject.name)

        # 绘制拖拽预览图
        pixmap = self._render_drag_pixmap()

        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(self.width() // 2, self.height() // 2))

        TimeTableWidget._dragged_card = self
        drag.exec(Qt.CopyAction | Qt.MoveAction)
        TimeTableWidget._dragged_card = None

    # ---------------------------------------------------------------
    # 内部辅助
    # ---------------------------------------------------------------
    @staticmethod
    def _event_pos(event):
        """兼容旧版 PySide6：某些版本的 event 没有 position() 方法"""
        if hasattr(event, "position"):
            return event.position().toPoint()
        return event.pos()

    def _render_drag_pixmap(self) -> QPixmap:
        """绘制高 DPI 的拖拽预览图，避免在高分屏上出现模糊"""
        dpr = self.devicePixelRatioF() if hasattr(self, "devicePixelRatioF") else 1.0
        if dpr < 1.0:
            dpr = 1.0
        logical_w = self.width()
        logical_h = self.height()

        pixmap = QPixmap(int(logical_w * dpr), int(logical_h * dpr))
        pixmap.setDevicePixelRatio(dpr)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        # 圆角卡片背景
        painter.setBrush(QBrush(QColor(255, 255, 255, 255)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, logical_w, logical_h, 8, 8)

        # 文字（继承控件自身的字体，保证字号与视觉一致）
        painter.setPen(QColor(50, 50, 50))
        font = self.font()
        if font.pointSize() > 0:
            font.setPointSize(max(9, font.pointSize()))
        else:
            font.setPointSize(10)
        painter.setFont(font)
        painter.drawText(
            0, 0, logical_w, logical_h,
            Qt.AlignCenter,
            f"{self.subject}\n{self.teacher}"
        )

        painter.end()
        return pixmap