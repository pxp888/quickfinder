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


def remove_readonly(func, path, exc_info):
    if func not in (os.unlink, os.rmdir) or exc_info[1].winerror != 5:
        raise exc_info[1]
    os.chmod(path, stat.S_IWRITE)
    func(path)

class thumbworker(QObject):
    result = pyqtSignal(object,object)
    def __init__(self, qoo, parent=None):
        super(thumbworker, self).__init__(parent)
        self.qoo = qoo

    def run(self):
        while 1:
            path, im = self.qoo.get(True)
            if path==0: return
            im2 = im.convert("RGBA")
            data = im2.tobytes("raw", "BGRA")
            qim = QImage(data, im.width, im.height, QImage.Format_ARGB32)
            pm = QPixmap.fromImage(qim)
            self.result.emit(path, pm)
        # print('all done')

class thumbmaker(QObject):
    result = pyqtSignal(object, object)
    def __init__(self, parent=None):
        super(thumbmaker, self).__init__(parent)
        self.qin = Queue()
        self.qoo = Queue()

        self.thread = QThread()
        self.worker = thumbworker(self.qoo)
        self.worker.moveToThread(self.thread)
        self.worker.result.connect(self.result)
        self.thread.started.connect(self.worker.run)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

        # self.pro = mp.Process(target=thumbnailpro, args=(self.qin, self.qoo),daemon=True)
        # self.pro.start()

        paths = AppDataPaths('quickfinder1')
        paths.setup()
        self.thumbroot = paths.logs_path

    def cleanup(self):
        pass 
        self.qoo.put((0,0))
        self.thread.exit()
        # self.pro.terminate()

    def getThumb(self, path, mtime):
        # self.qin.put((path,mtime))
        self.qin.put((5,(self.thumbroot, path, mtime, self.qoo)))

######################################################################################################################################################


class fileitem(QGraphicsItem):
    doublenpath = pyqtSignal(object)
    def __init__(self, path='', dir=True, width=200, parent=None):
        super(fileitem, self).__init__(parent)
        self.path = path
        self.pic = None
        self.sel = False
        self.frame = False
        self.w = int(width)
        self.h = int(width*.75)
        self.dir = dir 
        self.size = 0 
        self.msize = 0 

        self.setAcceptHoverEvents(True)
        if self.dir: self.setAcceptDrops(True)

    def boundingRect(self):
        return QRectF(0,0,self.w, self.h)

    def paint(self, painter, option, widget):
        if self.msize > 0:
            pen = QPen(QColor(50,50,50),1)
            painter.setPen(pen)
            outrect = self.boundingRect().adjusted(2,self.h-(self.size/self.msize)*self.h,-2,1)
            path = QPainterPath()
            path.addRect(outrect)   
            painter.fillPath(path,QColor(110,110,110))
            painter.drawRect(outrect)

        if self.sel:
            pen = QPen(QColor(42, 130, 130),1)
            painter.setPen(pen)
            outrect = self.boundingRect().adjusted(1,1,-1,-1)
            path = QPainterPath()
            path.addRect(outrect)
            painter.fillPath(path,QColor(42, 130, 130))
            painter.drawRect(outrect)

        pen = QPen(Qt.white,1)
        painter.setPen(pen)
        painter.setFont(QFont("Arial",8))
        trect = self.boundingRect().adjusted(5,self.h-40,-5,-2)
        painter.drawText(trect,Qt.TextWordWrap | Qt.AlignHCenter ,os.path.split(self.path)[1][:30])

        if not self.pic==None:
            s = self.pic.size()
            s.scale(self.w-20, self.h-50, Qt.KeepAspectRatio)
            painter.drawPixmap( int((self.w-s.width())/2) , 10 ,  s.width(), s.height(), self.pic)

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


class mview(QGraphicsView):
    nmove = pyqtSignal(object, object)
    def __init__(self, parent=None):
        super(mview, self).__init__(parent)
        
        self.copyAction = QAction("Copy",self)
        self.pasteAction = QAction("Paste",self)
        self.zipAction = QAction("ZIP Selection",self)
        self.deleteAction = QAction("Delete Selection",self)
        self.noIndexAction = QAction("No Index",self)
        self.noNameAction = QAction("Ignore Name",self)
        self.noPathAction = QAction("Ignore Path",self)
        self.addHomePathAction = QAction("Add Index Path",self)

        self.setAlignment(Qt.AlignTop | Qt.AlignLeft)

    def contextMenuEvent(self, event):
        if self.scene().selected():
            menu = QMenu(self)
            menu.addAction(self.copyAction)
            menu.addAction(self.pasteAction)
            menu.addAction(self.zipAction)
            menu.addAction(self.deleteAction)
            menu.addSeparator()
            menu.addAction(self.addHomePathAction)
            menu.addAction(self.noIndexAction)
            menu.addAction(self.noNameAction)
            menu.addAction(self.noPathAction)
            menu.exec(event.globalPos())
        else:
            menu = QMenu(self)
            menu.addAction(self.pasteAction)
            menu.exec(event.globalPos())

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
        else:
            dest = self.scene().core.n.fpath()

        for i in e.mimeData().urls(): 
            self.nmove.emit(i.path(), dest)


######################################################################################################################################################


class mscene(QGraphicsScene):
    npath=pyqtSignal(object)
    kevin=pyqtSignal(object)
    home=pyqtSignal()
    preview = pyqtSignal(object)
    shortcut = pyqtSignal(object)
    ncopy = pyqtSignal(object, object)
    segundo = pyqtSignal()
    def __init__(self, core, parent=None):
        super(mscene, self).__init__(parent)

        self.core = core
        self.maker = setter.iconMaker()
        self.icmaker = QFileIconProvider()

        self.thunder = thumbmaker()
        self.thunder.result.connect(self.seticonslot)
        self.thunder.qin = self.core.qin 

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
        self.iconheight = 120

    def seticonslot(self, path, pic):
        if path in self.paths:
            i = self.paths.index(path)
            self.its[i].setpic(pic)

    def refresh(self):
        for i in self.its: self.removeItem(i)
        self.its = []
        self.paths = []

        self.cursA = -1
        self.cursB = -1
        self.shiftkey = False
        self.ctrlkey = False
        self.cols = 1

        while 1:
            try:
                job, detail = self.thunder.qin.get(False)
                if not job==5: self.thunder.qit.put((job,detail))
            except:
                break

        for n in list(self.core.n.kids.values()):
            path = n.fpath()
            self.thunder.getThumb(path, n.mtime)
            it = fileitem(path, n.dir)
            it.setpic(self.icmaker.icon(QFileInfo(path)).pixmap(256,256))
            it.size = n.size 
            it.msize = 0 
            self.addItem(it)
            self.its.append(it)
            self.paths.append(path)

    def showsizes(self):
        msize = 0 
        for n in list(self.core.n.kids.values()): msize = max(msize, n.size)
        for i in self.its:
            i.msize = msize
            i.update()

    def reflow(self, wide=0):
        if wide==0: wide=self.wide
        self.wide = wide
        cols = max((int(wide / self.iconwidth)),1)
        self.cols = cols
        itemw = self.iconwidth 
        n = 0
        for i in self.its:
            i.w = itemw
            i.h = self.iconheight
            row = int(n / cols) * i.h
            col = (n % cols ) * itemw
            i.setPos(col,row)
            n+=1
        self.setSceneRect(self.itemsBoundingRect())

    def select(self, path):
        if self.shiftkey:
            if not path=='':
                i = self.paths.index(path)
                self.cursA = i
                a = min(self.cursA, self.cursB)
                b = max(self.cursA, self.cursB)
                for i in range(len(self.its)):
                    self.its[i].sel= i >=a and i <= b
                    self.its[i].update()
                self.its[self.cursA].ensureVisible(xMargin=0,yMargin=0)
            self.preview.emit(self.selected())
            return

        if self.ctrlkey:
            if not path=='':
                i = self.paths.index(path)
                self.cursA = i
                self.cursB = i
                self.its[i].toggle()
                self.its[self.cursA].ensureVisible(xMargin=0,yMargin=0)
            self.preview.emit(self.selected())
            return

        if path=='':
            self.cursA = -1
            self.cursB = -1
            for i in range(len(self.its)):
                self.its[i].sel = False
                self.its[i].update()
        else:
            i = self.paths.index(path)
            self.cursA = i
            self.cursB = i
            for i in range(len(self.its)):
                self.its[i].sel = i==self.cursA
                self.its[i].update()
            self.its[self.cursA].ensureVisible(xMargin=0,yMargin=0)

        self.preview.emit(self.selected())

    def selected(self):
        out = []
        for i in range(len(self.its)):
            if self.its[i].sel:
                out.append(self.paths[i])
        return out

    def mousePressEvent(self, event):
        if event.button()==8:
            path = self.core.back()
            self.npath.emit(path)
        super(mscene, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.clickbuffer:
            self.clickbuffer=False
            return
        if event.button()==1:
            it = self.itemAt(event.scenePos(),QTransform())
            if not it==None:
                self.select(it.path)
            else:
                self.select('')
        super(mscene, self).mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if not event.buttons()&1: return 
        dx = (event.buttonDownScenePos(1)-event.scenePos()).manhattanLength()
        if dx < 60: return 

        cur = self.selected()
        if not cur:
            # return 
            it = self.itemAt(event.buttonDownScenePos(1),QTransform())
            if it==None: return
            cur = [it.path]

        urls = []
        for i in cur:
            urls.append(QUrl().fromLocalFile(i))
        mimedata = QMimeData()
        mimedata.setUrls(urls)
        drag = QDrag(self)
        drag.setMimeData(mimedata)
        drag.exec(Qt.MoveAction | Qt.CopyAction)

    def copyToClip(self):
        # print('icon copy')
        cur = self.selected()
        if not cur: return 
        urls = []
        for i in cur:
            urls.append(QUrl().fromLocalFile(i))
        mimedata = QMimeData()
        mimedata.setUrls(urls)

        QGuiApplication.clipboard().setMimeData(mimedata)

    def pasteFromClip(self):
        # print('icon paste')
        mimedata = QGuiApplication.clipboard().mimeData()
        if mimedata.hasUrls():
            dest = self.core.n.fpath()
            urls = mimedata.urls()
            for i in urls:
                name = os.path.split(i.path())[1]
                target = os.path.join(dest, name)
                if os.path.exists(target):
                    if not os.path.isdir(target):
                        fname, ext = os.path.splitext(name)
                        fname = fname + ' Copy'
                        name = fname + ext 
                        target = os.path.join(dest, name)
                        self.ncopy.emit(i.path(), dest)
                    else:
                        target = os.path.join(dest, name) + ' Copy'
                        self.ncopy.emit(i.path(), dest)
                else:
                    self.ncopy.emit(i.path(), dest)

    def mouseDoubleClickEvent(self, event):
        self.clickbuffer = True
        if event.button()==1:
            it = self.itemAt(event.scenePos(),QTransform())
            if not it==None:
                if os.path.isdir(it.path):
                    self.npath.emit(it.path)
                else:
                    os.startfile(it.path)
        super(mscene, self).mouseDoubleClickEvent(event)

    def keyPressEvent(self, event):
        x = event.key()
        # print('ic',x)
        if self.ctrlkey:
            if x==65: self.selectAll()
            if x==73: self.selectInvert()
            if x==49: self.shortcut.emit(0)
            if x==50: self.shortcut.emit(1)
            if x==51: self.shortcut.emit(2)
            if x==52: self.shortcut.emit(3)
            if x==53: self.shortcut.emit(4)
            if x==54: self.shortcut.emit(5)
            if x==67: self.copyToClip() # C
            if x==86: self.pasteFromClip() # V 
            if x==78: self.segundo.emit()
            if x==84:  # T  
                path = self.core.n.fpath()
                if path=='': path = os.path.expanduser("~")
                os.chdir(path)
                subprocess.run('start cmd',shell=True)
                self.ctrlkey = False
            if x==76:  # L
                path = self.core.n.fpath()
                if path=='': path = os.path.expanduser("~")
                os.chdir(path)
                subprocess.run('start wsl',shell=True)
                self.ctrlkey = False
            return

        if x==16777248: self.shiftkey=True
        if x==16777249: self.ctrlkey=True
        if x==16777265: self.rename()
        if x==16777268: self.changes()
        if x==16777223:  # DELETE
            self.deleteFiles()
            return
        if x==16777234:  # LEFT
            self.cursA = (self.cursA -1 )%len(self.its)
            self.select(self.paths[self.cursA])
            return
        if x==16777235:  # UP
            if self.cursA >= self.cols:
                self.cursA = (self.cursA - self.cols )%len(self.its)
                self.select(self.paths[self.cursA])
            return
        if x==16777236:  # RIGHT
            self.cursA = (self.cursA + 1)%len(self.its)
            self.select(self.paths[self.cursA])
            return
        if x==16777237:  # DOWN
            if self.cursA < len(self.its)-self.cols:
                self.cursA = (self.cursA + self.cols )%len(self.its)
                self.select(self.paths[self.cursA])
            return
        if x==16777220:  #''' Enter '''
            cur = self.selected()
            if len(cur)==0: os.startfile(self.core.n.fpath())
            if len(cur)==1:
                if os.path.isdir(cur[0]):
                    self.npath.emit(cur[0])
                else:
                    os.startfile(cur[0])
                return
            for i in cur: os.startfile(i)
            return
        if x==16777219:  # backspace
            path = self.core.back()
            self.npath.emit(path)
            return
        if x==16777216:  #''' ESC key '''
            cur = self.selected()
            if len(cur)==0:
                self.home.emit()
                return
            else:
                self.select('')
                return
        if x < 93: self.kevin.emit(event)
        super(mscene,self).keyPressEvent(event)

    def keyReleaseEvent(self, event):
        x = event.key()
        if x==16777248:
            self.shiftkey=False
            # return
        if x==16777249:
            self.ctrlkey=False
            # return
        super(mscene,self).keyReleaseEvent(event)

    def selectAll(self):
        for i in self.its:
            i.sel = True
            i.update()
        self.preview.emit(self.selected())

    def selectInvert(self):
        for i in self.its:
            i.sel = not i.sel
            i.update()
        self.preview.emit(self.selected())

    def deleteFiles(self):
        cur = self.selected()
        if not cur: return 
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("Are you sure?")
        msg.setInformativeText("This cannot be undone.")
        msg.setWindowTitle("Confirm Delete")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg.setEscapeButton(QMessageBox.Cancel)
        retval = msg.exec_()
        if retval==1024:
            for i in cur:
                try:
                    if os.path.isdir(i):
                        shutil.rmtree(i,onerror=remove_readonly)
                    else:
                        os.remove(i)
                except:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setText("Delete Failed (it may be busy)")
                    msg.setInformativeText(str(i))
                    msg.setWindowTitle("Delete failed")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.setEscapeButton(QMessageBox.Ok)
                    retval = msg.exec_()

    def rename(self):
        cur = self.selected()
        if not cur: return 
        self.namer = mover.renameClass()
        self.namer.populate(cur)
        self.namer.show()


######################################################################################################################################################


class iconview(QWidget):
    npath = pyqtSignal(object)
    preview = pyqtSignal(object)
    kevin = pyqtSignal(object)
    nmove = pyqtSignal(object, object)
    ncopy = pyqtSignal(object, object)
    segundo = pyqtSignal()
    def __init__(self, core, parent=None):
        super(iconview, self).__init__(parent)
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

        self.zen = mscene(core)
        self.view = mview(self.zen)
        self.view.setBackgroundBrush(QBrush(QColor(40,40,40)))
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

    def refresh1(self, path=''):
        pass

    def refresh2(self, path=''):
        self.zen.refresh()
        self.zen.reflow(self.width())

    def changes(self):
        # print('change', self.core.n.fpath())    
        self.core.scan()
        self.refresh2()

    def setPath(self, path):
        eyedirs = self.eye.directories()
        if eyedirs: self.eye.removePaths(self.eye.directories())

        self.refresh2()
        if not os.path.isdir(path):
            self.zen.select(path)
            path = os.path.split(path)[0]
        self.eye.addPath(path)

    def resizeEvent(self, event):
        self.zen.reflow(self.width())

        super(iconview,self).resizeEvent(event)

    def wheelEvent(self, event):
        if self.zen.ctrlkey:
            if event.angleDelta().y() > 0:
                self.zen.iconwidth += 8
                self.zen.iconheight += 4
            else:
                self.zen.iconwidth -= 8
                self.zen.iconheight -= 4 
            self.zen.reflow()
            self.zen.update()
            return
        super(iconview, self).wheelEvent(event)

    def noIndexFunc(self):
        for i in self.zen.selected():
            self.core.ff.addNoIndex(i)
            self.set.set('ff',self.core.ff)
            self.core.scan()
            self.refresh2()

    def noNameFunc(self):
        for i in self.zen.selected():
            path, name = os.path.split(i)
            self.core.ff.addName(name)
            self.set.set('ff',self.core.ff)
            self.core.scan()
            self.refresh2()

    def noPathFunc(self):
        for i in self.zen.selected():
            self.core.ff.addPath(i)
            self.set.set('ff',self.core.ff)
            self.core.scan()
            self.refresh2()

    def addHomePathFunc(self):
        for i in self.zen.selected():
            self.core.addHomePath(i)

    def zipFunc(self):
        src = self.zen.selected()
        zname = src[0]+'.zip'
        os.chdir(self.core.n.fpath())
        with zipfile.ZipFile(zname, 'w') as zipper:
            for i in src:
                if os.path.isdir(i):
                    for root, dirs, files in os.walk(i, topdown=False):
                        for name in files:
                            zipper.write(os.path.relpath(os.path.join(root, name)))
                else:
                    zipper.write(os.path.relpath(i))

    def home(self):
        # self.npath.emit(os.path.expanduser("~"))
        self.npath.emit('home')

    def cleanup(self):
        self.zen.thunder.cleanup()

    def deepscan(self):
        self.core.fullscan()
        # self.view.refresh1()
        self.core.n.getsize()
        self.core.n.sort(1,0)
        self.refresh2()
        self.zen.showsizes()

    def timescan(self):
        self.core.n.sort(2,0)
        self.refresh2()

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

            self.thing = iconview(self.core)
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
