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
import base64
import hashlib
import shutil 
import subprocess 
import stat 
import zipfile 

import node
import setter
import mover 
import iconview

def humanTime(t):
    lt = time.localtime(t)
    # n = str(lt[0]) + '-'+ str(lt[1]) +'-'+ str(lt[2]) + '   ' + str(lt[3]) + ':' + str(lt[4])
    n = str(lt[0]) + '-'+ str(lt[1]).zfill(2) +'-'+ str(lt[2]).zfill(2) + '      ' + str(lt[3]).zfill(2) + ':' + str(lt[4]).zfill(2) + ' '
    return str(n)

def humanSize(s):
    if s > 1073741824: return str(round(s/1073741824,2))+'  Gb  '
    if s > 1048576: return str(int(round(s/1048576,0)))+'  Mb  '
    if s > 1024: return str(int(round(s/1024,0)))+'  Kb  '
    if s < 10: return '  '
    return str(s)+'  b  '

def remove_readonly(func, path, exc_info):
    if func not in (os.unlink, os.rmdir) or exc_info[1].winerror != 5:
        raise exc_info[1]
    os.chmod(path, stat.S_IWRITE)
    func(path)


######################################################################################################################################################


class listitem(QGraphicsItem):
    doublenpath = pyqtSignal(object)
    def __init__(self, path='', dir=True, width=200, parent=None):
        super(listitem, self).__init__(parent)
        self.path = path
        self.pic = None
        self.sel = False
        self.w = int(width)
        self.h = int(30)
        # self.dir = dir 
        self.size = 0 
        self.msize = 0 
        self.mtime = 0
        self.fsize = 9

        # self.setAcceptHoverEvents(True)
        # if self.dir: self.setAcceptDrops(True)

    def boundingRect(self):
        return QRectF(0,0,self.w, self.h)

    def paint(self, painter, option, widget):
        if self.msize > 0:
            pen = QPen(QColor(50,50,50),1)
            painter.setPen(pen)
            outrect = self.boundingRect().adjusted(2,0,-1*(self.w-(self.size / self.msize)*self.w),-1)
            path = QPainterPath()
            path.addRect(outrect)   
            painter.fillPath(path,QColor(80,80,80))
            # painter.drawRect(outrect)

        if self.sel:
            pen = QPen(QColor(42, 130, 130),1)
            painter.setPen(pen)
            outrect = self.boundingRect().adjusted(1,0,-1,0)
            path = QPainterPath()
            path.addRect(outrect)
            painter.fillPath(path,QColor(42, 130, 130))
            # painter.drawRect(outrect)

        pen = QPen(Qt.white,1)
        painter.setPen(pen)
        font = QFont("Arial",self.fsize)
        fm = QFontMetrics(font)

        timetext = humanTime(self.mtime)
        sizetext = humanSize(self.size)

        timewidth = fm.boundingRect(timetext).width()+5
        sizewidth = fm.boundingRect(sizetext).width()+25

        painter.setFont(font)
        trect = self.boundingRect().adjusted(self.h*2,0,-1*(timewidth + sizewidth),0)
        painter.drawText(trect, Qt.AlignLeft | Qt.AlignVCenter ,os.path.split(self.path)[1])

        srect = self.boundingRect().adjusted(self.w - timewidth - sizewidth,0,0,0)
        painter.drawText(srect, Qt.AlignLeft | Qt.AlignVCenter ,sizetext)

        drect = self.boundingRect().adjusted(self.w - timewidth ,0,0,0)
        painter.drawText(drect, Qt.AlignLeft | Qt.AlignVCenter ,timetext)

        if not self.pic==None:
            s = self.pic.size()
            s.scale(round(self.h*1.5), self.h-1, Qt.KeepAspectRatio)
            painter.drawPixmap( 10, 1 ,  s.width(), s.height(), self.pic)

    def setpic(self, pic):
        self.pic = pic
        self.update()

    def toggle(self):
        if self.sel==True:
            self.sel = False
        else:
            self.sel = True
        self.update()


######################################################################################################################################################


class lscene(iconview.mscene):
    def __init__(self, core, parent=None):
        super(iconview.mscene, self).__init__(parent)

        self.core = core
        self.maker = setter.iconMaker()
        self.icmaker = QFileIconProvider()

        # self.thunder = thumbmaker()
        # self.thunder.result.connect(self.seticonslot)
        # self.thunder.qin = self.core.qin 

        self.its = []
        self.paths = []

        self.wide = 1
        self.cols = 1
        self.shiftkey = False
        self.ctrlkey = False
        self.cursA = -1
        self.cursB = -1

        self.clickbuffer = False
        self.iconwidth = 120
        self.iconheight = 20
        self.fsize = 11

    def refresh(self):
        for i in self.its: self.removeItem(i)
        self.its = []
        self.paths = []

        self.cursA = -1
        self.cursB = -1
        self.shiftkey = False
        self.ctrlkey = False
        self.cols = 1

        # while 1:
        #     try:
        #         job, detail = self.thunder.qin.get(False)
        #         if not job==5: self.thunder.qit.put((job,detail))
        #     except:
        #         break

        for n in list(self.core.n.kids.values()):
            path = n.fpath()
            # self.thunder.getThumb(path, n.mtime)
            it = listitem(path, n.dir)
            it.setpic(self.icmaker.icon(QFileInfo(path)).pixmap(256,256))
            it.size = n.size 
            it.msize = 0 
            it.mtime = n.mtime 
            self.addItem(it)
            self.its.append(it)
            self.paths.append(path)

    def reflow(self, wide=0):
        font = QFont("Arial",self.fsize)
        fm = QFontMetrics(font)
        ch = fm.capHeight()

        if wide==0: wide=self.wide
        self.wide = wide
        cols = 1 
        self.cols = cols
        itemw = self.wide -20
        n = 0
        for i in self.its:
            i.w = itemw
            i.h = round(ch*1.6)
            i.fsize = self.fsize
            row = int(n / cols) * i.h
            col = (n % cols ) * itemw
            i.setPos(col,row)
            n+=1
        self.setSceneRect(self.itemsBoundingRect())


######################################################################################################################################################


class listview(iconview.iconview):
    def __init__(self, core, parent=None):
        super(iconview.iconview, self).__init__(parent)
        layout = QGridLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # self.setFont(QFont("Arial",10))
        self.layout = layout

        self.set = setter.setter('quickfinder1')

        self.core = core

        self.eye = QFileSystemWatcher()
        self.eye.directoryChanged.connect(self.changes)

        self.zen = lscene(core)
        self.view = iconview.mview(self.zen)
        self.view.setBackgroundBrush(QBrush(QColor(20,20,20)))
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.nmove.connect(self.nmove)

        self.zen.npath.connect(self.npath)
        self.zen.kevin.connect(self.kevin)
        self.zen.home.connect(self.home)
        self.zen.preview.connect(self.preview)
        self.zen.ncopy.connect(self.ncopy)
        self.zen.segundo.connect(self.segundo)

        self.view.copyAction.triggered.connect(self.zen.copyToClip)
        self.view.pasteAction.triggered.connect(self.zen.pasteFromClip)
        self.view.deleteAction.triggered.connect(self.zen.deleteFiles)
        self.view.noIndexAction.triggered.connect(self.noIndexFunc)
        self.view.noNameAction.triggered.connect(self.noNameFunc)
        self.view.noPathAction.triggered.connect(self.noPathFunc)
        self.view.addHomePathAction.triggered.connect(self.addHomePathFunc)
        self.view.zipAction.triggered.connect(self.zipFunc)

        layout.addWidget(self.view)
        self.zen.reflow(self.width())

    def wheelEvent(self, event):
        if self.zen.ctrlkey:
            if event.angleDelta().y() > 0:
                # self.zen.iconwidth += 8
                self.zen.fsize += 1
            else:
                # self.zen.iconwidth -= 8
                self.zen.fsize -= 1
            self.zen.reflow()
            self.zen.update()
            return
        super(iconview.iconview, self).wheelEvent(event)



    def cleanup(self):
    #     # self.zen.thunder.cleanup()
        pass 


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
            self.core.setPath(os.path.expanduser("~"))
            self.core.scan()

            self.thing = listview(self.core)
            layout.addWidget(self.thing)

            self.thing.npath.connect(self.setPath)

            self.thing.refresh2()

        def setPath(self, path):
            self.core.setPath(path)
            self.thing.refresh2()

    app = QApplication(sys.argv)
    # app.setStyle(QStyleFactory.create("Plastique"))
    app.setStyle(QStyleFactory.create("Fusion"))

    form = mainwin()
    form.show()
    # form.showFullScreen()
    # form.showMaximized()
    form.raise_()
    app.exec_()












# hello
