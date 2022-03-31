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
from PIL import Image
from appdata import AppDataPaths

import node
import setter
import btree


itemh = 40


class reswatcher(QObject):
    result = pyqtSignal(object)
    def __init__(self, qoo, parent=None):
        super(reswatcher, self).__init__(parent)
        self.qoo = qoo

    def run(self):
        while 1:
            res = self.qoo.get(True)
            self.result.emit(res)


######################################################################################################################################################


class resitem(QGraphicsItem):
    def __init__(self, path='', width=125, parent=None):
        super(resitem, self).__init__(parent)
        self.width = int(width)
        self.path = path
        self.baselen = 0
        self.pic = None
        self.frame = True
        self.sel = False
        self.hlite = False
        self.setAcceptHoverEvents(True)

    def boundingRect(self):
        return QRectF(0,0,self.width, itemh)

    def paint(self, painter, option, widget):
        outrect = self.boundingRect().adjusted(1,1,0,0)
        path = QPainterPath()
        path.addRect(outrect)
        if self.sel:
            painter.setPen(QPen(QColor(42, 130, 130),1))
            painter.fillPath(path,QColor(42, 130, 130))
            # painter.drawRect(outrect)
        else:
            if self.frame:
                painter.setPen(QPen(Qt.black,0))
                painter.fillPath(path,QColor(50,50,50))
                painter.drawRect(outrect)

        pen = QPen(Qt.white,1)
        painter.setPen(pen)
        painter.setFont(QFont("Arial",int(12)))
        trect = self.boundingRect().adjusted(itemh+10,1,-10,-1)
        dpath = self.path[self.baselen:].strip(os.path.sep)
        painter.drawText(trect,Qt.AlignVCenter | Qt.AlignLeft ,dpath)

        if self.hlite:
            pen = QPen(Qt.gray,1)
            painter.setPen(pen)
            outrect = self.boundingRect()
            painter.drawRect(outrect)

        if not self.pic==None:
            s = self.pic.size()
            s.scale(itemh-10, itemh-10, Qt.KeepAspectRatio)
            painter.drawPixmap(  10,5 ,  s.width(),  s.height(), self.pic)

    def hoverEnterEvent(self, event):
        self.hlite=True
        self.update()

    def hoverLeaveEvent(self, event):
        self.hlite=False
        self.update()


######################################################################################################################################################


class fscene(QGraphicsScene):
    npath = pyqtSignal(object)
    search = pyqtSignal(object)
    clearsig = pyqtSignal()
    def __init__(self, core, parent=None):
        super(fscene, self).__init__(parent)

        self.core = core
        # self.maker = setter.iconMaker()
        self.icmaker = QFileIconProvider()

        self.its = []
        self.sel = -1

        self.tree = btree.tree()
        self.target = ''

        self.cols = 1

        for i in range(32):
            it = resitem('it : ' + str(i))
            self.addItem(it)
            self.its.append(it)
            it.setVisible(False)
        self.update()

        self.thread = QThread()
        self.worker = reswatcher(self.core.foo)
        self.worker.moveToThread(self.thread)
        self.worker.result.connect(self.result)
        self.thread.started.connect(self.worker.run)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def result(self, res):
        tar, score, path, dir = res
        if not tar==self.target: return
        base = self.core.n.fpath()
        if path==base: return
        baselen = len(base)
        self.tree.top(score, res, 16)
        out = self.tree.walkdown(2)
        if self.tree.count==1:
            self.sel = 0
            self.showselection()
            self.search.emit(True)

        for i in range(len(out)):
            self.its[i].path = out[i][2]
            self.its[i].baselen = baselen
            # self.its[i].pic = self.maker.pic(out[i][2], out[i][3])
            self.its[i].pic = self.icmaker.icon(QFileInfo(out[i][2])).pixmap(256,256)
            self.its[i].setVisible(True)
            self.its[i].update()
        for j in range(len(self.its))[i+1:]:
            self.its[j].path=''
            self.its[j].baselen = 0
            self.its[j].pic = None
            self.its[j].setVisible(False)
            self.its[j].update()

    def showselection(self):
        for i in range(len(self.its)):
            self.its[i].sel = i==self.sel
            self.its[i].update()

    def blah(self, x):
        if x=='R':
            if self.sel < self.tree.count-1:
                self.sel+=1
                self.showselection()
        if x=='L':
            if self.sel > 0:
                self.sel-=1
                self.showselection()
        if x=='D':
            if self.sel < self.tree.count-self.cols:
                self.sel+=self.cols
                self.showselection()
        if x=='U':
            if self.sel >= self.cols:
                self.sel-=self.cols
                self.showselection()
        if x=='E':
            if self.sel >= 0:
                path = self.its[self.sel].path
                self.npath.emit(path)

    def mousePressEvent(self, event):
        if event.button()==1:
            it = self.itemAt(event.scenePos(),QTransform())
            if not it==None:
                self.npath.emit(it.path)
                self.clearsig.emit()
        super(fscene, self).mousePressEvent(event)


######################################################################################################################################################


class fline(QLineEdit):
    blah = pyqtSignal(object)
    home = pyqtSignal()
    back = pyqtSignal()
    clearsig = pyqtSignal()

    # def __init__(self, parent=None):
    #     super(fline, self).__init__(parent)
        # self.ctrlkey = False

    def keyPressEvent(self, event):
        x = event.key()
        # print(x)
        # if x==16777249:
        #     self.ctrlkey=True
            # return
        if x==16777234:
            self.blah.emit('L')
            return
        if x==16777235:
            self.blah.emit('U')
            return
        if x==16777236:
            self.blah.emit('R')
            return
        if x==16777237:
            self.blah.emit('D')
            return
        if x==16777220:  #''' Enter '''
            self.blah.emit('E')
            self.clearsig.emit()
        if x==16777216:  #''' ESC key '''
            if len(self.text()) > 0:
                self.clearsig.emit()
            else:
                self.home.emit()
                self.clearsig.emit()
            return
        if x==16777219:  #''' backspace '''
            if len(self.text())==0:
                self.back.emit()
                self.clearsig.emit()
        super(fline, self).keyPressEvent(event)


######################################################################################################################################################


class finderview(QWidget):
    npath = pyqtSignal(object)
    searching = pyqtSignal(object)
    def __init__(self, core, parent=None):
        super(finderview, self).__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # self.setFont(QFont("Arial",10))
        self.layout = layout

        self.set = setter.setter('quickfinder1')

        self.core = core

        self.line = fline()
        self.line.setFont(QFont("Arial",14))
        self.line.setPlaceholderText('Search here ...')

        self.zen = fscene(core)
        self.view = QGraphicsView(self.zen)
        self.view.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.view.setBackgroundBrush(QBrush(QColor(40,40,40)))
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setFocusPolicy(Qt.NoFocus)

        self.line.textChanged.connect(self.lookup)
        self.line.back.connect(self.back)
        self.line.home.connect(self.home)
        self.line.blah.connect(self.zen.blah)
        self.line.clearsig.connect(self.clear)

        self.zen.search.connect(self.view.setVisible)
        self.zen.npath.connect(self.npath)
        self.zen.clearsig.connect(self.clear)

        layout.addWidget(self.line)
        layout.addWidget(self.view)

        self.view.hide()
        self.reflow()

    def reflow(self):
        cols = int(self.width() / 600)
        cols = max(cols,1)
        cols = min(cols,4)
        self.zen.cols = cols
        itemw = int(self.width() / cols)
        n = 0
        for i in self.zen.its:
            i.width = itemw
            row = int(n / cols) * itemh
            col = (n % cols) * itemw
            i.setPos(col,row)
            i.update()
            n+=1

    def search(self, n):
        if n==1:
            self.view.show()
            self.searching.emit(True)
        else:
            self.view.hide()
            self.searching.emit(False)

    def clear(self):
        self.zen.sel = -1
        self.line.clear()
        self.view.hide()
        self.searching.emit(False)

    def resizeEvent(self, event):
        self.reflow()
        super(finderview,self).resizeEvent(event)

    def lookup(self):
        t = str(self.line.text())
        if len(t) > 1:
            self.zen.target=t
            self.zen.tree = btree.tree()
            self.zen.sel = -1
            for i in self.zen.its:
                i.setVisible(False)
                i.sel=False

            self.core.find(str(t))
            self.view.show()
            self.searching.emit(True)
        if len(t)==0:
            self.clear()

    def back(self):
        path = self.core.back()
        self.npath.emit(path)

    def home(self):
        # self.npath.emit(os.path.expanduser("~"))
        self.npath.emit('home')


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
            self.core.scan(rec=9)

            self.thing = finderview(self.core)
            layout.addWidget(self.thing)

            self.thing.npath.connect(self.setPath)

            # self.thing.refresh()

        def setPath(self, path):
            print(path)
            
        # def setPath(self, path):
        #     self.core.setPath(path)
        #     self.thing.refresh()

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
