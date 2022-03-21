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



class prevpane(QScrollArea):
    def __init__(self, parent=None):
        super(prevpane, self).__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # self.setFont(QFont("Arial",12))
        # self.setFont(QFont("MS Shell Dlg 2",10))
        self.layout = layout

        self.text = QTextEdit()
        self.label1 = QLabel()

        layout.addWidget(self.text)
        layout.addWidget(self.label1)
        self.text.hide()
        self.label1.hide()

        darkPalette = QPalette()
        darkPalette.setColor(QPalette.Base, QColor(29, 31, 33));
        darkPalette.setColor(QPalette.Text, QColor(200, 200, 200));
        # darkPalette.setColor(QPalette.Base, QColor(190, 190, 190));
        # darkPalette.setColor(QPalette.Text, Qt.black);

        self.text.setPalette(darkPalette)
        # self.text.setFont(QFont("MS Shell Dlg 2",12))
        self.text.setFont(QFont("Arial",13))

    def preview(self, paths):
        if self.width() < 100: return
        txtfiles = ['py','txt','bat','json','ini','log','sh','h','cpp','conf']
        images = ['jpg','png','bmp','jpeg','webp']

        if len(paths)==1:
            path = paths[0]
            if path.split('.')[-1].lower() in txtfiles:
                self.showtext(path)
                return
            if path.split('.')[-1].lower() in images:
                self.showimage(path)
                return
        self.clear()

    def clear(self):
        self.text.hide()
        self.label1.hide()

    def showtext(self, path):
        self.label1.hide()
        self.text.show()
        try:
            fin = open(path,'r')
            self.text.setPlainText(fin.read(10000))
            fin.close()
        except:
            pass

    def showimage(self,path):
        self.label1.show()
        self.text.hide()

        im = Image.open(path)
        im = ImageOps.exif_transpose(im)
        im2 = im.convert("RGBA")
        data = im2.tobytes("raw", "BGRA")
        qim = QImage(data, im.width, im.height, QImage.Format_ARGB32)
        pm = QPixmap.fromImage(qim)
        pic = pm.scaledToWidth(self.width())
        if pic.height() > self.height():
            pic = pic.scaledToHeight(self.height())

        # pic = QPixmap(path)
        # pic = pic.scaledToWidth(self.width())
        # # pip = pic.scaled(QSize(self.height(), self.width()),1)
        # if pic.height() > self.height():
        #     pic = pic.scaledToHeight(self.height())

        self.label1.setPixmap(pic)

class prevwin(QDialog):
    def __init__(self, core=None, parent=None):
        super(prevwin, self).__init__(parent)
        self.setWindowTitle('Preview')
        # frame = QFrame()
        # self.setCentralWidget(frame)
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # self.resize(1200,900)

        self.prev = prevpane()
        layout.addWidget(self.prev)
