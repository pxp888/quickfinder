from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import os
import sys
import time

import multiprocessing as mp
from queue import Queue
import threading
import resources
from PIL import Image, ImageOps
from appdata import AppDataPaths

import node
import setter



class homeClass(QWidget):
    def __init__(self, core, parent=None):
        super(homeClass, self).__init__(parent)
        layout = QGridLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # self.setFont(QFont("Arial",10))
        self.layout = layout

        self.core = core
        self.set = setter.setter('quickfinder1')
        self.homepaths = self.set.get('homepaths',[])
        if len(self.homepaths)==0:
            self.homepaths.append(os.path.expanduser("~"))
            self.set.set('homepaths',self.homepaths)

        for i in self.homepaths:
            b = QLabel(i)
            self.layout.addWidget(b)

        self.layout.addWidget(QLabel('Drives : '))

        drives = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        for i in drives:
            path = i+r':\\'
            if os.path.exists(path):
                self.layout.addWidget(QLabel(path))

        # self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout.addItem(verticalSpacer)

        self.setup()

    def setup(self, path=''):
        self.core.sniffer = node.node()
        for i in self.homepaths: self.core.addSnifPath(i)
        self.core.n = self.core.sniffer
        self.core.scan()




######################################################################################################################################################


if __name__ == "__main__":

    class mainwin(QMainWindow):
        def __init__(self, parent=None):
            super(mainwin, self).__init__(parent)

            self.setWindowTitle('Quick Finder')
            frame = QFrame()
            self.setCentralWidget(frame)
            layout = QGridLayout()
            frame.setLayout(layout)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            self.resize(1600,1200)

            self.core = node.coreClass()
            self.home = homeClass(self.core)


    app = QApplication(sys.argv)
    # app.setStyle(QStyleFactory.create("Plastique"))
    app.setStyle(QStyleFactory.create("Fusion"))

    form = mainwin()
    form.show()
    # form.showFullScreen()
    # form.showMaximized()
    form.raise_()
    app.exec_()
