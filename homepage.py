from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import os
import sys
import time
import shutil 

import multiprocessing as mp
from queue import SimpleQueue
import threading
import resources
from PIL import Image, ImageOps
from appdata import AppDataPaths

import node
import setter

class fileitem(QGraphicsItem):
    doublenpath = pyqtSignal(object)
    def __init__(self, path='', width=200, parent=None):
        super(fileitem, self).__init__(parent)
        self.path = path
        self.dpath = path 
        self.pic = None
        self.sel = False
        self.frame = False
        self.w = int(width)
        self.h = int(width*.75)
        self.total = 0 
        self.used = 0

        self.setAcceptHoverEvents(True)
        self.hlite = False

    def boundingRect(self):
        return QRectF(0,0,self.w, self.h)

    def paint(self, painter, option, widget):
        if self.sel:
            pen = QPen(QColor(42, 130, 130),1)
            painter.setPen(pen)
            outrect = self.boundingRect().adjusted(1,1,-1,-1)
            path = QPainterPath()
            path.addRect(outrect)
            painter.fillPath(path,QColor(42, 130, 130))
            painter.drawRect(outrect)
        else:
            if self.frame:
                pen = QPen(Qt.black,0)
                painter.setPen(pen)
                outrect = self.boundingRect().adjusted(1,1,-1,-1)
                path = QPainterPath()
                path.addRect(outrect)
                painter.fillPath(path,QColor(50,50,50))
                painter.drawRect(outrect)

        if self.used > 0:
            pen = QPen(QColor(50,50,50),1)
            painter.setPen(pen)
            outrect = self.boundingRect().adjusted(2,self.h-(self.used/self.total)*self.h,-2,1)
            path = QPainterPath()
            path.addRect(outrect)   
            painter.fillPath(path,QColor(110,110,110))
            painter.drawRect(outrect)

        pen = QPen(Qt.white,1)
        painter.setPen(pen)
        painter.setFont(QFont("Arial",8))
        trect = self.boundingRect().adjusted(5,self.h-40,-5,-2)
        painter.drawText(trect,Qt.TextWordWrap | Qt.AlignHCenter ,self.dpath)

        if self.used > 0:
            pen = QPen(Qt.white,1)
            painter.setPen(pen)
            painter.setFont(QFont("Arial",8))
            trect = self.boundingRect().adjusted(5,self.h-20,-5,-2)
            stext = str((self.total-self.used)//2**30) + ' GB free / ' + str(self.total//2**30)+' GB'
            painter.drawText(trect,Qt.TextWordWrap | Qt.AlignHCenter ,stext)

        if not self.pic==None:
            s = self.pic.size()
            s.scale(self.w-20, self.h-50, Qt.KeepAspectRatio)
            painter.drawPixmap( int((self.w-s.width())/2) , 10 ,  s.width(), s.height(), self.pic)

    def setpic(self, pic, frame=False):
        self.pic = pic
        self.frame = frame
        self.update()

    def toggle(self):
        if self.sel==True:
            self.sel = False
        else:
            self.sel = True
        self.update()

    def hoverEnterEvent(self, event):
        self.hlite=True
        self.update()

    def hoverLeaveEvent(self, event):
        self.hlite=False
        self.update()


######################################################################################################################################################


class mview(QGraphicsView):
    nmove = pyqtSignal(object, object)
    def __init__(self, parent=None):
        super(mview, self).__init__(parent)
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, e):
        # print('view enter', e)
        if e.mimeData().hasUrls():
            e.setAccepted(True)
        else:
            e.setAccepted(False)

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls():
            e.setAccepted(True)
        else:
            e.setAccepted(False)

    def dropEvent(self, e):
        it = self.itemAt(e.pos())
        if not it==None:
            dest = it.path
            for i in e.mimeData().urls(): 
                self.nmove.emit(i.path(), dest)
                print('move',i.path(), dest)
        

######################################################################################################################################################


class mscene(QGraphicsScene):
    npath=pyqtSignal(object)
    kevin = pyqtSignal(object)
    quit = pyqtSignal()
    segundo = pyqtSignal(object)
    def __init__(self, parent=None):
        super(mscene, self).__init__(parent)
        self.noIndexAction = QAction("No Index",self)
        self.noNameAction = QAction("Ignore Name",self)
        self.noPathAction = QAction("Ignore Path",self)
        self.addHomePathAction = QAction("Add Home Path",self)

        self.ctrlkey = False
        self.shiftkey = False

    def mousePressEvent(self, event):
        if event.button()==1:
            it = self.itemAt(event.scenePos(),QTransform())
            if not it==None:
                self.npath.emit(it.path)
        super(mscene, self).mousePressEvent(event)

    def keyPressEvent(self, event):
        x = event.key()
        # print('ic',x)
        if x==16777248: self.shiftkey=True
        if x==16777249: self.ctrlkey=True

        if self.ctrlkey:
            if x==51: self.segundo.emit(1)
            if x==87: self.quit.emit()
            if x==78:
                if not self.shiftkey:
                    self.segundo.emit(0)
            return

        if x < 93: self.kevin.emit(event)
        super(mscene,self).keyPressEvent(event)

    def keyReleaseEvent(self, event):
        x = event.key()
        if x==16777248: self.shiftkey=False
        if x==16777249: self.ctrlkey=False
        super(mscene,self).keyReleaseEvent(event)

    def focusOutEvent(self, event):
        self.shiftkey = False
        self.ctrlkey = False
        super(mscene, self).focusOutEvent(event)


######################################################################################################################################################


class homeClass(QWidget):
    npath = pyqtSignal(object)
    kevin = pyqtSignal(object)
    nmove = pyqtSignal(object, object)
    quit = pyqtSignal()
    segundo = pyqtSignal(object)
    def __init__(self, core, parent=None):
        super(homeClass, self).__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # self.setFont(QFont("Arial",11))
        self.layout = layout

        self.icmaker = QFileIconProvider()
        self.core = core
        self.set = setter.setter('quickfinder1')

        self.homepaths = self.core.homepaths    

        self.its = []
        self.drv = []

        self.zen1 = mscene()
        self.view1 = mview()
        self.view1.setBackgroundBrush(QBrush(QColor(40,40,40)))
        self.view1.setScene(self.zen1)
        self.view1.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.view1.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view1.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        layout.addWidget(self.view1)

        self.view1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.view1.setMinimumHeight(160)

        self.zen1.npath.connect(self.npath)
        self.zen1.kevin.connect(self.kevin)
        self.view1.nmove.connect(self.nmove)
        self.zen1.quit.connect(self.quit)
        self.zen1.segundo.connect(self.segundo)

        self.label1 = self.zen1.addText('Index Paths')
        self.label2 = self.zen1.addText('Drives')
        self.setup()
        self.setFocusPolicy(Qt.NoFocus)

        self.qoo = SimpleQueue()
        en = (4,(self.qoo))
        self.core.qin.put(en)

        self.dim = QTimer()
        self.dim.setInterval(250)
        self.dim.timeout.connect(self.drivecheck)
        self.dim.start()
        
    def drivecheck(self):
        while 1:
            try:
                path, total, used = self.qoo.get(False)
                if path==0: 
                    self.dim.stop()
                    self.reflow()
                    return
            except:
                self.reflow()
                return
            it = fileitem(path)
            it.total = total 
            it.used = used 
            it.setpic(self.icmaker.icon(QFileInfo(path)).pixmap(256,256))
            self.zen1.addItem(it)
            self.drv.append(it)
            it.update()
        
    def setup(self, path=''):
        self.core.sniffer = node.node()
        for i in self.homepaths: self.core.addSnifPath(i)
        self.core.n = self.core.sniffer
        self.core.scan(rec=7)

        for i in self.its: self.zen1.removeItem(i)
        self.its = []

        for i in self.homepaths:
            it = fileitem(i)
            base, name = os.path.split(i)
            if name=='': 
                it.dpath=base
            else:
                it.dpath=name 

            it.setpic(self.icmaker.icon(QFileInfo(i)).pixmap(256,256))
            self.zen1.addItem(it)
            self.its.append(it)

        self.reflow()

    def reflow(self):
        cols = max(int(self.width() / 200) ,1)
        self.label1.setPos(0,0)
        ycursor = self.label1.boundingRect().height()
        n = 0 
        for i in self.its:
            col = int(n/cols)*150 + ycursor
            row = int(n%cols)*200
            i.setPos(row,col)
            n+=1
        ycursor+= col+150
        self.label2.setPos(0,ycursor)
        ycursor+= self.label2.boundingRect().height()
        n = 0 
        for i in self.drv:
            col = int(n/cols)*150 + ycursor
            row = int(n%cols)*200
            i.setPos(row,col)
            i.update()
            n+=1
        
    def resizeEvent(self, event):
        self.reflow()
        super(homeClass,self).resizeEvent(event)


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
