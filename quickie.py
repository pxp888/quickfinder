from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import os
import sys
import time
import pickle
import threading
import multiprocessing
import subprocess

import node
import setter
import finder
import view 
import mover 
import homepage
import preview 

class blabel(QWidget):
    clicked = pyqtSignal()
    npath = pyqtSignal(object)
    def __init__(self, parent=None):
        super(blabel, self).__init__(parent)
        layout = QHBoxLayout()
        self.setLayout(layout)
        # layout.setContentsMargins(0, 0, 0, 0)
        # layout.setSpacing(0)
        self.label = QLabel()
        self.label.setFont(QFont("Arial",14))

        self.settingicon = QIcon(':/icons/settings.png')
        self.setbut = QPushButton()
        self.setbut.setIcon(self.settingicon)
        self.setbut.clicked.connect(self.clicked)
        self.setbut.setFocusPolicy(Qt.NoFocus)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        

        layout.addWidget(self.label)
        layout.addStretch()
        layout.addWidget(self.setbut)

    def clear(self):
        self.label.setText('')

    def setPath(self,path):
        if not os.path.isdir(path):
            path, file = os.path.split(path)
        self.label.setText(path)

    def mousePressEvent(self, event):
        self.npath.emit('home')
        super(blabel, self).mousePressEvent(event)



class primo(QWidget):
    npath = pyqtSignal(object)
    quit = pyqtSignal()
    def __init__(self, parent=None):
        super(primo, self).__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # self.setFont(QFont("Arial",10))
        self.layout = layout

        self.bros = []

        self.core = node.coreClass()
        self.core.setPath(os.path.expanduser("~"))
        self.core.scan()
        
        self.top = blabel()
        self.view = view.iconview(self.core)
        self.move = mover.mover()
        self.prev = preview.prevpane()
        self.split = QSplitter()

        self.npath.connect(self.view.setPath)
        self.npath.connect(self.top.setPath)
        self.view.npath.connect(self.setPath)
        self.view.ncopy.connect(self.move.copy)
        self.view.nmove.connect(self.move.move)
        self.view.quit.connect(self.quit)
        self.view.home.connect(self.top.clear)
        self.view.preview.connect(self.prev.preview)
        self.view.segundo.connect(self.segundo)
        self.top.clicked.connect(self.setwin)

        self.view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.top.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.prev.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.split.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.view.refresh()

        layout.addWidget(self.top)
        layout.addWidget(self.split)
        self.split.addWidget(self.view)
        self.split.addWidget(self.prev)
        self.split.setSizes([int(self.width()*(2/3)), int(self.width()*(1/3))])
        self.prev.hide()

    def setPath(self, path):
        self.core.setPath(path)
        self.npath.emit(path)

    def setwin(self):
        self.setwin = setter.setwin(self.core)
        self.setwin.show()

    def segundo(self, s):
        if s==0:
            w = mainwin()
            w.show()
            self.bros.append(w)
        if s==1:
            if self.prev.isVisible():
                self.prev.hide()
            else:
                self.prev.show()


if __name__ == "__main__":
    multiprocessing.freeze_support()

    class mainwin(QMainWindow):
        def __init__(self, parent=None):
            super(mainwin, self).__init__(parent)

            self.setWindowTitle('Quick Finder 1.3.0')
            frame = QFrame()
            self.setCentralWidget(frame)
            layout = QGridLayout()
            frame.setLayout(layout)
            layout.setContentsMargins(1,1,1,1)
            layout.setSpacing(1)
            self.resize(1400,800)

            self.thing = primo()
            layout.addWidget(self.thing)
            self.thing.npath.connect(self.setWindowTitle)
            self.thing.quit.connect(self.close)

    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    app.setPalette(setter.darkPalette)

    form = mainwin()
    form.show()
    # form.showFullScreen()
    # form.showMaximized()
    form.raise_()
    app.exec_()