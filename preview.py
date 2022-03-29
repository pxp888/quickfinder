from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import os
import sys
import time
import zipfile 

import multiprocessing as mp
from queue import Queue
import threading
import resources
from PIL import Image, ImageOps

def humanSize(s):
    if s > 1073741824: return str(round(s/1073741824,2))+'  G  '
    if s > 1048576: return str(int(round(s/1048576,0)))+'  m  '
    if s > 1024: return str(int(round(s/1024,0)))+'  k  '
    if s < 10: return '  '
    return str(s)+'  b  '


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
        self.extractbutton = QPushButton('Extract Zip File')
        self.zipbutton = QPushButton('Create Zip File')
        self.zipname = QLineEdit()

        layout.addWidget(self.text)
        layout.addWidget(self.label1)
        layout.addWidget(self.extractbutton)
        layout.addWidget(self.zipname)
        layout.addWidget(self.zipbutton)

        self.text.hide()
        self.label1.hide()
        self.extractbutton.hide()
        self.zipname.hide()
        self.zipbutton.hide()

        self.extractbutton.clicked.connect(self.unzip)
        self.zipbutton.clicked.connect(self.makezip)

        darkPalette = QPalette()
        darkPalette.setColor(QPalette.Base, QColor(40, 42, 54));
        darkPalette.setColor(QPalette.Text, QColor(200, 200, 200));
        # darkPalette.setColor(QPalette.Base, QColor(190, 190, 190));
        # darkPalette.setColor(QPalette.Text, Qt.black);

        self.text.setPalette(darkPalette)
        # self.text.setFont(QFont("MS Shell Dlg 2",12))
        # self.text.setFont(QFont("Arial",13))
        self.setFocusPolicy(Qt.NoFocus)
        self.text.setFocusPolicy(Qt.NoFocus)
        self.extractbutton.setFocusPolicy(Qt.NoFocus)
        self.zipbutton.setFocusPolicy(Qt.NoFocus)

        self.zfile = None 
        self.lastpaths = []

    def preview(self, paths):
        try:
            if self.width() < 100: return
            txtfiles = ['py','txt','bat','json','ini','log','sh','h','cpp','conf','csv']
            images = ['jpg','png','bmp','jpeg','webp']
            zipfiles = ['zip']

            if len(paths)==1:
                path = paths[0]
                if path.split('.')[-1].lower() in txtfiles:
                    self.showtext(path)
                    return
                if path.split('.')[-1].lower() in images:
                    self.showimage(path)
                    return
                if path.split('.')[-1].lower() in zipfiles:
                    self.showzip(path)
                    return
            if len(paths)>1: 
                self.showmany(paths)
                return 
            
            self.clear()
        except:
            self.clear()

    def clear(self):
        self.text.hide()
        self.label1.hide()
        self.extractbutton.hide()
        self.zipbutton.hide()
        self.zipname.hide()

    def showtext(self, path):
        self.label1.hide()
        self.text.show()
        self.extractbutton.hide()
        self.zipbutton.hide()
        self.zipname.hide()
        try:
            fin = open(path,'r')
            self.text.setPlainText(fin.read(10000))
            fin.close()
        except:
            pass

    def showimage(self,path):
        self.label1.show()
        self.text.hide()
        self.extractbutton.hide()
        self.zipbutton.hide()
        self.zipname.hide()

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

    def showzip(self, path):
        self.label1.hide()
        self.text.show()
        self.extractbutton.show()
        self.zipbutton.hide()
        self.zipname.hide()

        t = ''
        with zipfile.ZipFile(path, 'r') as zipper:
            list = zipper.infolist()
            for i in list:
                t += i.filename + '\t\t\t' + str(i.date_time[0]) + '/'+str(i.date_time[1])+'/'+str(i.date_time[2])+ '\n'
            self.text.setPlainText(t)
        self.zfile = path 

    def unzip(self):
        outpath = os.path.split(self.zfile)[0]
        with zipfile.ZipFile(self.zfile, 'r') as zipper:
            zipper.extractall(os.path.splitext(self.zfile)[0])


    def showmany(self, paths):
        self.label1.hide()
        self.text.show()
        self.extractbutton.hide()
        self.zipbutton.show()
        self.zipname.show()

        self.lastpaths = paths
        cur = os.path.split(self.lastpaths[0])[0]
        os.chdir(cur)
        cur = os.path.split(cur)[1]
        size = 0
        for i in paths:
            size+=os.path.getsize(i)
        msg = str(len(paths)) + ' Selected, '+ humanSize(size) 
        msg += '\n\n'
        for i in paths:
            msg += os.path.relpath(i) + '\n'
        self.text.setPlainText(msg)
        proposedname = cur + '.zip'
        self.zipname.setText(proposedname)

    def makezip(self):
        zname = self.zipname.text()
        os.chdir(os.path.split(self.lastpaths[0])[0])
        with zipfile.ZipFile(zname, 'w') as zipper:
            for i in self.lastpaths:
                if os.path.isdir(i):
                    for root, dirs, files in os.walk(i, topdown=False):
                        for name in files:
                            zipper.write(os.path.relpath(os.path.join(root, name)))
                else:
                    zipper.write(os.path.relpath(i))



# class prevwin(QDialog):
#     def __init__(self, core=None, parent=None):
#         super(prevwin, self).__init__(parent)
#         self.setWindowTitle('Preview')
#         # frame = QFrame()
#         # self.setCentralWidget(frame)
#         layout = QVBoxLayout()
#         self.setLayout(layout)
#         layout.setContentsMargins(0, 0, 0, 0)
#         layout.setSpacing(0)
#         # self.resize(1200,900)

#         self.prev = prevpane()
#         layout.addWidget(self.prev)
