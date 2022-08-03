from __future__ import absolute_import, division, print_function
from operator import index
from re import X

from typing import Dict, List, Any
from collections import OrderedDict
from functools import partial
from matplotlib.pyplot import show
import numpy as np
import cv2
import os

from PyQt5.QtWidgets import (QWidget, QDialog, QLabel, QGridLayout, QVBoxLayout, QSizePolicy, QApplication)
from PyQt5.QtCore import (QThread, pyqtSignal, pyqtSlot, QSize, Qt, QTimer, QTime, QDate, QObject, QEvent)
from PyQt5.QtGui import (QImage, QPixmap, QFont, QIcon)

os.environ['OPENCV_VIDEOIO_DEBUG'] = '1'
os.environ['OPENCV_VIDEOIO_PRIORITY_MSMF'] = '0'

# QLabel display
width, height = 480*6, 270*6
w = 1920//2 # 960
h = 1080//2 # 540
capture_delay = 80 # 80 ms

## ------------------------
class Slot (QThread):
    signal = pyqtSignal (np.ndarray, int, int, bool)
    
    def __init__(self, parent: QWidget, index: int, cam_id: int, link: str) -> None:
        QThread.__init__(self, parent)
        self.parent = parent
        self.index = index
        self.cam_id = cam_id
        self.link = link
        
    def run(self) -> None:
        cap = cv2.VideoCapture(self.link)
        while cap.isOpened():
            has, im = cap.read()
            if not has: break
            im = cv2.resize(im, (w,h))
            self.signal.emit(im, self.index, self.cam_id, True)
            cv2.waitKey(capture_delay) & 0xFF
            
        im = np.zeros((h,w,3), dtype=np.uint8)
        self.signal.emit (im, self.index, self.cam_id, False)
        cv2.waitKey(capture_delay) & 0xFF

## ----------------------
def clickable(widget):
    class Filter(QObject):
        clicked = pyqtSignal()
        def eventFilter(self, obj, event):
            if obj == widget:
                if event.type() == QEvent.MouseButtonRelease:
                    self.clicked.emit()
                    return True
            return False

    filter = Filter(widget)
    widget.installEventFilter(filter)
    return filter.clicked

## ----------------------
class NewWindow(QDialog):
    def __init__(self, parent: QWidget) -> None:
        QDialog.__init__(self, parent)
        self.parent = parent
        self.index: int = 0

        self.label = QLabel()
        self.label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.label.setScaledContents(True)
        self.label.setFont(QFont("Times", 30))
        self.label.setStyleSheet(
            "color: rgb(255,0,255);"
            "background-color: rgb(0,0,0);"
            "qproperty-alignment: AlignCenter;")

        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        # layout.setSpacing(2)
        layout.addWidget(self.label)
        self.setLayout(layout)
        self.setWindowTitle('Camera {}'.format(self.index))

    def sizeHint(self) -> QSize:
        return QSize(width//3, height//3)

    def resizeEvent(self, event) -> None:
        self.update()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_Escape:
            self.accept()

## ---------------------------
class Window(QWidget):
    def __init__(self, cams: Dict[int, str]) -> None:
        super(Window, self).__init__()

        # initialize the cameras with empty values
        self.cameras: Dict[int, List[Any]] = OrderedDict()
        index: int
        for index in range (len(cams.key())):
            #
            self.cameras[index] = [None, None, False]

        index = 0
        for cam_id, link in cams.items():
            #
            self.cameras[index] = [cam_id, link, False]
            index += 1

        # main layout ------
        layout = QGridLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(2)

        self.labels: List[QLabel] = []
        self.threads: List[Slot] = []
        for index, value in self.cameras.items():
            cam_id, link, active = value

            # thread ----------
            slot = Slot(self, index, cam_id, link)
            slot.signal.connect(self.ReadImage)
            self.threads.append(slot)

            # screen ------------
            label = QLabel()
            label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            label.setScaledContents(True)
            label.setFont(QFont("Times", 30))
            label.setStyleSheet(
                "color: rgb(255,0,255); background-color: rgb(0,0,0);"
                "qproperty-alignment: AlignCenter;")

            clickable(label).connect(partial(self.showCam, index))
            self.labels.append(label)

            if index == 0:
                layout.addWidget(label, 0,0) # row 1, col1
            elif index == 1:
                layout.addWidget(label, 0,1) # row 1, col2
            elif index == 2:
                layout.addWidget(label, 0,2) # row 1, col3
            elif index == 3:
                layout.addWidget(label, 0,3) # row 1, col4

            elif index == 4:
                layout.addWidget(label, 1,0) # row 2, col1
            elif index == 5:
                layout.addWidget(label, 1,1) # row 2, col2
            elif index == 6:
                layout.addWidget(label, 1,2) # row 2, col3
            elif index == 7:
                layout.addWidget(label, 1,3) # row 2, col4

            elif index == 8:
                layout.addWidget(label, 2,0) # row 3, col1
            elif index == 9:
                layout.addWidget(label, 2,1) # row 3, col2
            elif index == 10:
                layout.addWidget(label, 2,2) # row 3, col3
            elif index == 11:
                layout.addWidget(label, 2,3) # row 3, col4

            elif index == 12:
                layout.addWidget(label, 3,0) # row 4, col1
            elif index == 13:
                layout.addWidget(label, 3,1) # row 4, col2
            elif index == 14:
                layout.addWidget(label, 3,2) # row 4, col3
            elif index == 15:
                layout.addWidget(label, 3,3) # row 4, col4
            else:
                raise ValueError("n Camera != rows/cols")

        # Time screen ----------
        timer = QTimer(self)
        timer.timeout.connect(self.showTime)
        timer.start(1000) # 1s
        self.showTime()

        # Timer auto restart threads (restart every 3 hours)
        timer_th = QTimer(self)
        timer_th.timeout.connect(self.refresh)
        timer_th.start(6000*60*3) # 3 hr

        self.setLayout(layout)
        self.setWindowTitle('cctv')
        self.setWindowIcon(QIcon('icon.png'))

        self.newWindow = NewWindow(self)

        self.refresh()


    def sizeHint(self) -> QSize:
        return QSize(width, height)

    def resizeEvent(self, event) -> None:
        self.update()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_Escape:
            self.close()

    def closeEvent(self, event): pass

    def showCam(self, index: Any) -> None:
        self.newWindow.index = index
        if not self.cameras[index][2]:
            text_ = "Camera {}\nNot active!".format(self.cameras[index][0])
            self.newWindow.label.setText(text_)
        self.newWindow.setWindowTitle('Camera {}'.format(self.cameras[index][0]))
        self.newWindow.show()

    def showTime(self) -> None:
        # Time
        time = QTime.currentTime()
        textTime = time.toString('hh:mm:ss')
        # Date
        date = QDate.currentDate()
        textDate = date.toString('ddd, MMMM d')

        text = "{}\n{}".format(textTime, textDate)

        for index, value in self.cameras.items():
            cam_id, link, active = value
            if not active:
                text_ = "Camera {}\n".format(cam_id) + text
                self.labels[index].setText(text_)

    @pyqtSlot(np.ndarray, int, int, bool)
    def ReadImage(self, im: np.ndarray, index: int, cam_id: int, active: bool) -> None:
        self.cameras[index][2] = active
        cam_id, link, active = self.cameras[index]

        im=QImage(im.data, im.shape[1], im.shape[2], QImage.Format_RGB888).rgbSwapped()
        self.labels[index].setPixmap(QPixmap.fromImage(im))

        if index == self.newWindow.index:
            self.newWindow.label.setPixmap(QPixmap.fromImage(im))

    def refresh(self) -> None:
        for slot in self.threads:
            slot.start()


if __name__ == 'main':
    
    import sys

    # cams = OrderedDict()
    cams: Dict[int, Any] = OrderedDict()

    cams[1] = None
    cams[2] = None
    cams[3] = "AUV2\\1.mp4"
    cams[4] = None
    cams[5] = "AUV2\\2.mp4"
    cams[6] = None
    cams[7] = None
    cams[8] = "AUV2\\3.mp4"
    cams[9] = "AUV2\\4.mp4"
    cams[10] = None
    cams[11] = None
    cams[12] = None
    cams[13] = None
    cams[14] = None
    cams[15] = None
    cams[16] = None

    app = QApplication(sys.argv)
    win = Window(cams=cams)
    win.show()
    sys.exit(app.exec_())
