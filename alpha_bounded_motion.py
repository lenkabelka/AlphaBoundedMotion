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


def get_contours(image):
    img = cv2.imread(image, cv2.IMREAD_UNCHANGED)

    # create a binary mask based on the alpha channel
    alpha = img[:, :, 3]  # RGBA
    _, binary = cv2.threshold(alpha, 1, 255, cv2.THRESH_BINARY)

    # find contours and hierarchy
    contours, hierarchy = cv2.findContours(
        binary,
        cv2.RETR_CCOMP,   # внешние и внутренние контуры
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
        print("Background fully contains subspace")
        return True
    else:
        print("!!!!!!")
        return False


class DraggablePixmapItem(QGraphicsPixmapItem):
    def __init__(self, pixmap, scene, app):
        super().__init__(pixmap)
        self.app_ref = app
        self.scene_ref = scene

        self.setShapeMode(QGraphicsPixmapItem.ShapeMode.MaskShape)

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )

        self.path_1 = get_path(get_contours("room_alpha.png")[0], get_contours("room_alpha.png")[1])
        self.path_2 = get_path(get_contours("circle_with_hole.png")[0], get_contours("circle_with_hole.png")[1])


    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():

            if allow_movement(self.path_1, self.path_2, value.x(), value.y()):
                return value  # allow movement
            else:
                return self.pos()
        return super().itemChange(change, value)



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