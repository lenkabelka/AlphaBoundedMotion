from PyQt6.QtWidgets import (QGraphicsPixmapItem,
                             QGraphicsItem,
                             QApplication,
                             QGraphicsScene,
                             QGraphicsView
                             )
from PyQt6.QtGui import QPainterPath, QPixmap, QTransform
from PyQt6.QtCore import QPointF, Qt
import cv2
import sys
import math


def get_contours(image):
    img = cv2.imread(image, cv2.IMREAD_UNCHANGED)

    # create a binary mask based on the alpha channel
    alpha = img[:, :, 3]  # RGBA
    _, binary = cv2.threshold(alpha, 1, 255, cv2.THRESH_BINARY)

    # find contours and hierarchy
    contours, hierarchy = cv2.findContours(
        binary,
        cv2.RETR_CCOMP,   # outer and inner contours
        cv2.CHAIN_APPROX_SIMPLE
    )

    return [contours, hierarchy]


def get_path(contours, hierarchy):
    path = QPainterPath()
    path.setFillRule(Qt.FillRule.OddEvenFill)

    if hierarchy is not None:
        for i, contour in enumerate(contours):
            # start a new subpath
            sub_path = QPainterPath()

            if len(contour) == 0:
                continue

            first_point = contour[0][0]
            sub_path.moveTo(QPointF(first_point[0], first_point[1]))

            for point in contour[1:]:
                x, y = point[0]
                sub_path.lineTo(QPointF(x, y))

            sub_path.closeSubpath()
            path.addPath(sub_path)

        return path


def allow_movement(path_1, path_2, new_x, new_y):
    transform = QTransform()
    transform.translate(new_x, new_y)
    transformed_path_2 = transform.map(path_2)

    if path_1.contains(transformed_path_2):
        print("Background fully contains subspace. Movement is allowed!")
        return True
    else:
        print("Movement is not allowed!")
        return False



class DraggablePixmapItem(QGraphicsPixmapItem):
    def __init__(self, pixmap, scene, app):
        super().__init__(pixmap)
        self.app_ref = app
        self.scene_ref = scene
        self.drag_offset = QPointF()
        self.binary_search = "version_2"

        self.setShapeMode(QGraphicsPixmapItem.ShapeMode.MaskShape)

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )

        self.path_1 = get_path(get_contours("room_alpha.png")[0], get_contours("room_alpha.png")[1])
        self.path_2 = get_path(get_contours("circle_with_hole.png")[0], get_contours("circle_with_hole.png")[1])


    def mousePressEvent(self, event):
        self.drag_offset = event.pos()
        super().mousePressEvent(event)


    def mouseMoveEvent(self, event):
        new_scene_pos = event.scenePos() - self.drag_offset
        self.setPos(new_scene_pos)
        super().mouseMoveEvent(event)


    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            current_pos = self.pos()
            desired_pos = value

            if allow_movement(self.path_1, self.path_2, desired_pos.x(), desired_pos.y()):
                return value

            if self.binary_search == "version_1":
                new_pos = self.binary_search_position_1(current_pos, desired_pos)
                return new_pos if new_pos else current_pos
            if self.binary_search == "version_2":
                new_pos = self.binary_search_position_2(current_pos, desired_pos)
                return new_pos if new_pos else current_pos

        return super().itemChange(change, value)


    def binary_search_position_1(self, start: QPointF, end: QPointF):
        best_pos = None
        while True:
            possible_pos = (start + end) / 2
            if allow_movement(self.path_1, self.path_2, possible_pos.x(), possible_pos.y()):
                best_pos = possible_pos
                start = possible_pos
            else:
                end = possible_pos

            dx = end.x() - start.x()
            dy = end.y() - end.y()
            distance = math.hypot(dx, dy)
            if  distance < 0.5:
                print(f"distance: {distance}")
                print(f"possible_pos: {possible_pos}")
                print(f"best: {best_pos}")
                break

        return best_pos


    def binary_search_position_2(self, start: QPointF, end: QPointF, max_iter=20, tolerance=0.5):
        left = 0.0
        right = 1.0
        best_pos = None

        for _ in range(max_iter):
            mid = (left + right) / 2.0
            mid_point = QPointF(
                start.x() + (end.x() - start.x()) * mid,
                start.y() + (end.y() - start.y()) * mid
            )

            if allow_movement(self.path_1, self.path_2, mid_point.x(), mid_point.y()):
                best_pos = mid_point
                left = mid
            else:
                right = mid

            if abs(right - left) < tolerance / (end - start).manhattanLength():
                break

        return best_pos



def main():
    app = QApplication(sys.argv)

    scene = QGraphicsScene()
    view = QGraphicsView()
    view.setWindowTitle("Alpha bounded motion")

    screen = QApplication.primaryScreen().geometry()
    coef_width = 0.9
    coef_height = 0.9
    window_width = int(screen.width() * coef_width)
    window_height = int(screen.height() * coef_height)
    view.resize(window_width, window_height)
    x = (screen.width() - window_width) // 2
    y = 0
    view.move(x, y)

    background_item = QPixmap("room_alpha.png")
    drag_item = QPixmap("circle_with_hole.png")

    background = QGraphicsPixmapItem(background_item)
    draggable_item = DraggablePixmapItem(drag_item, scene, app)
    background.setZValue(-1)
    draggable_item.setPos(60, 60)

    scene.addItem(background)
    scene.addItem(draggable_item)
    view.setScene(scene)

    view.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()