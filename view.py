from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import os
import sys
import time

import multiprocessing as mp
from queue import SimpleQueue
import threading
import resources
from PIL import Image, ImageOps
import base64
import hashlib
import shutil 
import subprocess 
import stat 
import zipfile 

import node
import setter
import mover 
import btree 
import finder
import homepage

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
        self.qin = SimpleQueue()
        self.qoo = SimpleQueue()

        self.thread = QThread()
        self.worker = thumbworker(self.qoo)
        self.worker.moveToThread(self.thread)
        self.worker.result.connect(self.result)
        self.thread.started.connect(self.worker.run)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

        # self.pro = mp.Process(target=thumbnailpro, args=(self.qin, self.qoo),daemon=True)
        # self.pro.start()

        thpath = os.path.join(os.path.expanduser("~"),'quickfinder')
        self.thumbroot = os.path.join(thpath, 'thumbnails')
        if not os.path.exists(self.thumbroot): os.mkdir(self.thumbroot)

    def cleanup(self):
        pass 
        self.qoo.put((0,0))
        self.thread.exit()
        # self.pro.terminate()

    def getThumb(self, path, mtime):
        # self.qin.put((path,mtime))
        self.qin.put((5,(self.thumbroot, path, mtime, self.qoo)))


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


class fileitem(QGraphicsItem):
    doublenpath = pyqtSignal(object)
    def __init__(self, path='', dir=True, width=200, parent=None):
        super(fileitem, self).__init__(parent)
        self.path = path
        self.pic = None
        self.sel = False
        self.w = int(width)
        self.h = int(width*1)
        self.dir = dir 
        self.size = 0 
        self.msize = 0 
        self.mtime = 0

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

        # txtheight = int((40/160)*self.h)
        txtheight = 45

        pen = QPen(Qt.white,1)
        painter.setPen(pen)
        painter.setFont(QFont("Arial",8))
        trect = self.boundingRect().adjusted(5,self.h-txtheight,-5,-2)
        painter.drawText(trect, Qt.TextWrapAnywhere | Qt.AlignHCenter , os.path.split(self.path)[1])

        if not self.pic==None:
            s = self.pic.size()
            s.scale(self.w-5, self.h-txtheight-5, Qt.KeepAspectRatio)
            painter.drawPixmap( int((self.w-s.width())/2) , 5 ,  s.width(), s.height(), self.pic)

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
        self.renameAction = QAction("Rename",self)
        self.zipAction = QAction("ZIP Selection",self)
        self.unzipAction = QAction("unZIP Selection",self)
        self.deleteAction = QAction("Delete Selection",self)
        self.noIndexAction = QAction("No Index",self)
        self.noNameAction = QAction("Ignore Name",self)
        self.noPathAction = QAction("Ignore Path",self)
        self.addHomePathAction = QAction("Add Index Path",self)
        self.newFolderAction = QAction("Create new Folder",self)
        self.md5Action = QAction("MD5 Hash", self)
        self.sha256Action = QAction("SHA256 Hash", self)

        self.setAlignment(Qt.AlignTop | Qt.AlignLeft)

    def contextMenuEvent(self, event):
        sel = self.scene().selected()
        if sel:
            menu = QMenu(self)
            menu.addAction(self.copyAction)
            menu.addAction(self.pasteAction)
            menu.addAction(self.renameAction)
            menu.addAction(self.zipAction)
            if len(sel)==1: 
                if sel[0][-3:]=='zip':
                    menu.addAction(self.unzipAction)
                menu.addAction(self.md5Action)
                menu.addAction(self.sha256Action)
            menu.addAction(self.newFolderAction)
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
            menu.addAction(self.newFolderAction)
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
    npath = pyqtSignal(object)
    ncopy = pyqtSignal(object, object)
    quit = pyqtSignal()
    preview = pyqtSignal(object)
    kevin = pyqtSignal(object)
    segundo = pyqtSignal(object)
    home = pyqtSignal()
    nzip = pyqtSignal(object, object)
    nunzip = pyqtSignal(object)
    def __init__(self, core, parent=None):
        super(mscene, self).__init__(parent)

        self.core = core
        # self.maker = setter.iconMaker()
        self.icmaker = QFileIconProvider()

        self.thunder = thumbmaker()
        self.thunder.result.connect(self.seticonslot)
        self.thunder.qin = self.core.qin 

        self.its = {}

        self.w = 1 
        self.h = 1 
        self.iconwidth = 150
        self.iconheight = 150
        self.fsize = 9 
        self.listheight = 30

        self.ctrlkey = False
        self.shiftkey = False
        self.cursA = ''
        self.cursB = ''
        self.clickbuffer = False

        self.sortmode = 0 
        self.sortdir = 0
        self.viewmode = 0
        
    def refresh(self, w=None, h=None):
        if w==None:
            w = self.w 
            h = self.h 
        sortmode = self.sortmode
        if sortmode==4: sortmode=1
        self.core.n.sort(sortmode, self.sortdir)

        self.w = w 
        self.h = h 
        cols = max(int(w/self.iconwidth),1)
        
        curnodes = self.core.n.children()
        rows = int(len(curnodes)/cols)+1

        if self.viewmode==0:

            self.setSceneRect(0,0,cols*self.iconwidth, rows*self.iconheight)
            i = 0
            curit = {}
            for n in curnodes:
                path = n.fpath()
                if not path in self.its:
                    it = fileitem(path, n.dir)
                    self.thunder.getThumb(path, n.mtime)
                    it.setpic(self.icmaker.icon(QFileInfo(path)).pixmap(256,256))
                    it.w = self.iconwidth
                    it.h = self.iconheight
                    it.size = n.size 
                    self.addItem(it)
                    self.its[path] = it 
                else:
                    it = self.its[path]
                curit[path] = it 
                row = int(i/cols) * self.iconheight
                col = (i%cols) * self.iconwidth
                it.setPos(col,row)
                i+=1

        if self.viewmode==1:
            font = QFont("Arial",self.fsize)
            fm = QFontMetrics(font)
            ch = fm.capHeight()
            self.listheight = int(ch*1.8)
            cols = 1 
            self.setSceneRect(0,0,self.w, len(curnodes)*self.listheight)

            i = 0
            curit = {}
            for n in curnodes:
                path = n.fpath()
                if not path in self.its:
                    it = listitem(path, n.dir)
                    # self.thunder.getThumb(path, n.mtime)
                    it.setpic(self.icmaker.icon(QFileInfo(path)).pixmap(256,256))
                    it.mtime = n.mtime 
                    it.w = self.w-30
                    it.h = self.listheight
                    it.fsize = self.fsize
                    it.size = n.size 
                    self.addItem(it)
                    self.its[path] = it 
                else:
                    it = self.its[path]
                curit[path] = it 
                row = int(i/cols) * self.listheight
                col = 0 
                it.setPos(col,row)
                i+=1

        kill = []
        for i in self.its: 
            if not i in curit: kill.append(i)
        for i in kill:
            self.removeItem(self.its[i])
            del self.its[i]
        self.its = curit 

    def reflow(self, w=None, h=None):
        if w==None:
            w = self.w 
            h = self.h 
        if self.viewmode==0:
            self.w = w 
            self.h = h 
            cols = max(int(w/self.iconwidth),1)

            rows = int(len(self.its)/cols)+1
            self.setSceneRect(0,0,cols*self.iconwidth, rows*self.iconheight)

            i = 0
            for it in self.its.values():
                row = int(i/cols) * self.iconheight
                col = (i%cols) * self.iconwidth
                it.w = self.iconwidth
                it.h = self.iconheight
                it.setPos(col,row)
                it.update()
                i +=1


        if self.viewmode==1:
            font = QFont("Arial",self.fsize)
            fm = QFontMetrics(font)
            ch = fm.capHeight()
            self.listheight = int(ch*1.8)

            self.w = w 
            self.h = h 
            cols = 1
            rows = len(self.its)
            self.setSceneRect(0,0,self.w, rows*self.listheight)

            i = 0
            for it in self.its.values():
                row = int(i/cols) * self.listheight
                col = 0
                it.w = self.w - 30
                it.h = self.listheight
                it.fsize = self.fsize
                it.setPos(col,row)
                it.update()
                i +=1

    def select(self, path):
        if self.ctrlkey:
            if path in self.its: self.its[path].toggle()
            self.cursA = path 
            self.cursB = path 
            self.preview.emit(self.selected())
            return
        
        if self.shiftkey:
            s = 0
            self.cursB = path 
            for i in self.its:
                if s==3:
                    self.its[i].sel=False
                if s==0:
                    self.its[i].sel=False
                    if i==self.cursA: s=1
                    if i==path: s=2
                if s==1: 
                    self.its[i].sel=True 
                    if i==path: s=3
                if s==2:
                    self.its[i].sel=True
                    if i==self.cursA: s=3
                self.its[i].update()
            self.preview.emit(self.selected())
            return

        for i in self.its:
            self.its[i].sel = i==path
            self.its[i].update()
        self.cursA = path
        self.cursB = path
        self.preview.emit(self.selected())
        if not path=='':
            self.its[path].ensureVisible(xMargin=0, yMargin=0)

    def selected(self):
        out = []
        for i in self.its:
            if self.its[i].sel: out.append(i)
        return out 

    def keyPressEvent(self, event):
        x = event.key()
        # print('ic',x)
        if x==16777248: self.shiftkey=True
        if x==16777249: self.ctrlkey=True
        if x==16777216: self.escaped()
        if x==16777220: self.entered()
        if x==16777219: self.back()
        if x==16777265: self.rename()
        if x==16777223: self.deleteFiles()

        if self.ctrlkey:
            if x==65: self.selectAll()
            if x==73: self.selectInvert()
            if x==67: self.copyToClip()
            if x==86: self.pasteFromClip()
            if x==87: self.quit.emit()
            if x==84: self.terminal1()
            if x==76: self.terminal2()
            if x==49: self.viewicons()
            if x==50: self.viewlist()
            if x==52: self.namesort()
            if x==53: self.sizesort()
            if x==54: self.timesort()
            if x==55: self.deepsort()
            if x==51: self.segundo.emit(1)
            if x==43: self.zoom(True)
            if x==45: self.zoom(False)
            if x==78:
                if self.shiftkey:
                    self.newFolderFunc()
                else:
                    self.segundo.emit(0)
            return

        if x >= 16777234:
            if x <=  16777237:
                if x==16777234: self.dirkey('L')
                if x==16777235: self.dirkey('U')
                if x==16777236: self.dirkey('R')
                if x==16777237: self.dirkey('D')
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
        
    def viewlist(self):
        for i in self.its: self.removeItem(self.its[i])
        self.its = {}
        self.viewmode=1
        self.refresh()

    def viewicons(self):
        for i in self.its: self.removeItem(self.its[i])
        self.its = {}
        self.viewmode=0
        self.refresh()        

    def namesort(self):
        if self.sortmode==0: 
            self.sortdir = (self.sortdir +1)%2 
        else:
            self.sortmode=0
            self.sortdir=1
        self.refresh()

    def sizesort(self):
        if self.sortmode==1: 
            self.sortdir = (self.sortdir +1)%2 
        else:
            self.sortmode=1
            self.sortdir=0
        for i in self.core.n.children():
            if i.dir: i.size=0
        msize = 0 
        for i in self.core.n.children():
            path = i.fpath()
            msize = max(i.size, msize)
            self.its[path].size = i.size 
        for i in self.its:
            self.its[i].msize = msize
            self.its[i].update()
        self.refresh()

    def timesort(self):
        if self.sortmode==2: 
            self.sortdir = (self.sortdir +1)%2 
        else:
            self.sortmode=2
            self.sortdir=0
        self.refresh()

    def deepsort(self):
        self.core.n.getsize()
        if self.sortmode==4: 
            self.sortdir = (self.sortdir +1)%2 
        else:
            self.sortmode=4
            self.sortdir=0

        msize = 0 
        for i in self.core.n.children():
            path = i.fpath()
            msize = max(i.size, msize)
            self.its[path].size = i.size 
        for i in self.its:
            self.its[i].msize = msize 
            self.its[i].update()
        self.refresh()
        
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

    def mouseDoubleClickEvent(self, event):    
        it = self.itemAt(event.scenePos(),QTransform())
        if it==None: return
        if os.path.isdir(it.path):
            self.npath.emit(it.path)
        else:
            os.startfile(it.path)
        self.clickbuffer = True 

    def mouseMoveEvent(self, event):
        if not event.buttons()&1: return 
        dx = (event.buttonDownScenePos(1)-event.scenePos()).manhattanLength()
        if dx < 100: return 

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

    def entered(self):
        cur = self.selected()
        if len(cur)==0:
            os.startfile(self.core.n.fpath())
        if len(cur)==1:
            if os.path.isdir(cur[0]):
                self.npath.emit(cur[0])
            else:
                os.startfile(cur[0])
        if len(cur)>1:
            for i in cur:
                os.startfile(i)

    def escaped(self):
        home = True
        for i in self.its:
            if self.its[i].sel == True: home = False 
            self.its[i].sel = False 
            self.its[i].update()
        if home:
            self.home.emit()

    def back(self):
        path = self.core.back()
        self.npath.emit(path)

    def dirkey(self, k):
        if not self.cursB in self.its:
            self.cursB = list(self.its)[0]
            self.select(self.cursB)
            return

        paths = list(self.its)
        cols = max(int(self.w/self.iconwidth),1)
        if self.viewmode==1: cols=1
        if k==('L'):
            i = paths.index(self.cursB)
            i = (i-1)%len(paths)
            p = paths[i]
            self.select(p)
        if k==('R'):
            i = paths.index(self.cursB)
            i = (i+1)%len(paths)
            p = paths[i]
            self.select(p)
        if k==('U'):
            i = paths.index(self.cursB)
            if i < cols: return 
            i = (i-cols)%len(paths)
            p = paths[i]
            self.select(p)
        if k==('D'):
            i = paths.index(self.cursB)
            if i >= len(paths)-cols: return 
            i = (i+cols)%len(paths)
            p = paths[i]
            self.select(p)

    def selectAll(self):
        for i in self.its:
            self.its[i].sel = True
            self.its[i].update()
        self.preview.emit(self.selected())

    def selectInvert(self):
        for i in self.its:
            if self.its[i].sel:
                self.its[i].sel=False
            else:
                self.its[i].sel=True 
            self.its[i].update()
        self.preview.emit(self.selected())

    def seticonslot(self, path, pic):
        if path in self.its:
            self.its[path].setpic(pic)

    def copyToClip(self):
        cur = self.selected()
        if not cur: return 
        urls = []
        for i in cur:
            urls.append(QUrl().fromLocalFile(i))
        mimedata = QMimeData()
        mimedata.setUrls(urls)
        QGuiApplication.clipboard().setMimeData(mimedata)

    def pasteFromClip(self):
        mimedata = QGuiApplication.clipboard().mimeData()
        if mimedata.hasUrls():
            dest = self.core.n.fpath()
            urls = mimedata.urls()
            for i in urls:
                self.ncopy.emit(i.path(), dest)

    def terminal1(self):
        path = self.core.n.fpath()
        if path=='': path = os.path.expanduser("~")
        os.chdir(path)
        subprocess.run('start cmd',shell=True)
        self.ctrlkey = False

    def terminal2(self):
        path = self.core.n.fpath()
        if path=='': path = os.path.expanduser("~")
        os.chdir(path)
        subprocess.run('start wsl',shell=True)
        self.ctrlkey = False

    def rename(self):
        cur = self.selected()
        if not cur: return 
        self.namer = mover.renameClass()
        self.namer.populate(cur)
        self.namer.show()

    def deleteFiles(self):
        cur = self.selected()
        if not cur: return 
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
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

    def newFolderFunc(self):
        n = 1
        prename = os.path.join(self.core.n.fpath(), 'New Folder ')
        while 1:
            name = prename+str(n)
            if not os.path.exists(name): break
            n+=1
        os.mkdir(name)

    def zipFunc(self):
        src = self.selected()
        curpath = self.core.n.fpath()
        # self.core.qin.put( (7,(src, curpath)) )
        self.nzip.emit(src, curpath)

    def unzipFunc(self):
        src = self.selected()
        self.nunzip.emit(src)
        # for s in src:
        #     with zipfile.ZipFile(s, 'r') as zipper:
        #         zipper.extractall(os.path.splitext(s)[0])

    def zoom(self, f):
        if self.viewmode==0:
            if f:
                self.iconwidth+=4
                self.iconheight+=4
            else:
                self.iconwidth-=4
                self.iconheight-=4
            self.reflow()
            return
        if self.viewmode==1:
            if f:
                self.fsize+=1
            else:
                self.fsize-=1
            self.reflow()
            return

    def md5Func(self):
        n = self.selected()
        if not len(n)==1: return 
        try:
            with open(n[0],'rb') as fin:
                h = hashlib.md5(fin.read()).hexdigest()
        except:
            msg = QMessageBox()
            # msg.setIcon(QMessageBox.Information)
            msg.setText('Hash Failed for :'+n[0])
            # msg.setInformativeText(str(i))
            # msg.setWindowTitle('MD5 Hash : ' + n[0])
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setEscapeButton(QMessageBox.Ok)
            retval = msg.exec_()
            return 
        msg = QMessageBox()
        msg.setFont(QFont("Arial",14))
        # msg.setIcon(QMessageBox.Information)
        msg.setText(str(h))
        # msg.setInformativeText(str(i))
        msg.setWindowTitle('MD5 Hash : ' + n[0])
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setEscapeButton(QMessageBox.Ok)
        retval = msg.exec_()

    def sha256Func(self):
        n = self.selected()
        if not len(n)==1: return 
        try:
            with open(n[0],'rb') as fin:
                h = hashlib.sha256(fin.read()).hexdigest()
        except:
            msg = QMessageBox()
            # msg.setIcon(QMessageBox.Information)
            msg.setText('Hash Failed for :'+n[0])
            # msg.setInformativeText(str(i))
            # msg.setWindowTitle('MD5 Hash : ' + n[0])
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setEscapeButton(QMessageBox.Ok)
            retval = msg.exec_()
            return 
        msg = QMessageBox()
        msg.setFont(QFont("Arial",14))
        # msg.setIcon(QMessageBox.Information)
        msg.setText(str(h))
        # msg.setInformativeText(str(i))
        msg.setWindowTitle('SHA256 Hash : ' + n[0])
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setEscapeButton(QMessageBox.Ok)
        retval = msg.exec_()




######################################################################################################################################################


class iconview(QWidget):
    npath =pyqtSignal(object)
    ncopy =pyqtSignal(object, object)
    nmove =pyqtSignal(object, object)
    nzip = pyqtSignal(object, object)
    nunzip = pyqtSignal(object)
    quit = pyqtSignal()
    preview = pyqtSignal(object)
    home = pyqtSignal()
    segundo = pyqtSignal(object)
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

        self.fin = finder.finderview(self.core)
        self.fin.searching.connect(self.searching)
        self.fin.npath.connect(self.npath)
        self.fin.quit.connect(self.quit)
        self.fin.segundo.connect(self.segundo)

        self.zen.npath.connect(self.npath)
        self.zen.kevin.connect(self.kevin)
        self.zen.ncopy.connect(self.ncopy)
        self.zen.nzip.connect(self.nzip)
        self.zen.nunzip.connect(self.nunzip)
        self.zen.quit.connect(self.quit)
        self.zen.preview.connect(self.preview)
        self.zen.segundo.connect(self.segundo)

        self.view.nmove.connect(self.nmove)
        self.view.copyAction.triggered.connect(self.zen.copyToClip)
        self.view.pasteAction.triggered.connect(self.zen.pasteFromClip)
        self.view.zipAction.triggered.connect(self.zen.zipFunc)
        self.view.unzipAction.triggered.connect(self.zen.unzipFunc)
        self.view.noIndexAction.triggered.connect(self.noIndexFunc)
        self.view.noNameAction.triggered.connect(self.noNameFunc)
        self.view.noPathAction.triggered.connect(self.noPathFunc)
        self.view.addHomePathAction.triggered.connect(self.addHomePathFunc)
        self.view.deleteAction.triggered.connect(self.zen.deleteFiles)
        self.view.md5Action.triggered.connect(self.zen.md5Func)
        self.view.sha256Action.triggered.connect(self.zen.sha256Func)

        self.homepage = homepage.homeClass(self.core)
        self.homepage.npath.connect(self.npath)
        self.fin.home.connect(self.homeFunc)
        self.zen.home.connect(self.homeFunc)
        self.zen.home.connect(self.home)
        self.homepage.kevin.connect(self.kevin)
        self.homepage.quit.connect(self.quit)
        self.homepage.segundo.connect(self.segundo)

        layout.addWidget(self.fin)
        layout.addWidget(self.view)
        layout.addWidget(self.homepage)
        self.homemode=1
        self.homeFunc()

    def searching(self, s):
        if s:
            self.view.hide()
            self.homepage.hide()
        else:
            if self.homemode==1:
                self.homepage.show()
                self.view.hide()
            else:
                self.view.show()
                self.homepage.hide()

    def kevin(self,event):
        self.fin.line.setFocus()
        self.fin.line.keyPressEvent(event)

    def changes(self):
        self.core.scan()
        self.refresh()

    def refresh(self):
        self.zen.refresh(self.width(), self.height())

    def homeFunc(self, h=True):
        if h:
            self.homemode = 1
            self.view.hide()
            self.homepage.show()
            self.homepage.setup()
        else:
            self.homemode = 0
            self.view.show()
            self.homepage.hide()

    def hidehome(self):
        self.homeFunc(False)

    def setPath(self, path):
        self.homeFunc(False)

        self.zen.refresh(self.width(), self.height())
        if not os.path.isdir(path):
            self.zen.select(path)
            base, fil = os.path.split(path)
        else:
            base = path 

        dirs = self.eye.directories()
        if dirs: self.eye.removePaths(dirs)
        self.eye.addPath(base)
        self.view.setFocus()

    def resizeEvent(self, event):
        self.zen.reflow(self.width(), self.height())
        super(iconview,self).resizeEvent(event)

    def wheelEvent(self, event):
        if self.zen.viewmode==0:
            if self.zen.ctrlkey:
                if event.angleDelta().y() > 0:
                    self.zen.iconwidth += 4
                    self.zen.iconheight += 4
                else:
                    self.zen.iconwidth -= 4
                    self.zen.iconheight -= 4 
                self.zen.reflow(self.width(), self.height())
                return
        if self.zen.viewmode==1:
            if self.zen.ctrlkey:
                if event.angleDelta().y() > 0:
                    self.zen.fsize += 1
                else:
                    self.zen.fsize -= 1
                self.zen.reflow(self.width(), self.height())
                return
        super(iconview, self).wheelEvent(event)

    def cleanup(self):
        self.zen.thunder.cleanup()

    def noIndexFunc(self):
        for i in self.zen.selected():
            self.core.ff.addNoIndex(i)
            self.set.set('ff',self.core.ff)
            self.core.scan()
            self.refresh()

    def noNameFunc(self):
        for i in self.zen.selected():
            path, name = os.path.split(i)
            self.core.ff.addName(name)
            self.set.set('ff',self.core.ff)
            self.core.scan()
            self.refresh()

    def noPathFunc(self):
        for i in self.zen.selected():
            self.core.ff.addPath(i)
            self.set.set('ff',self.core.ff)
            self.core.scan()
            self.refresh()

    def addHomePathFunc(self):
        for i in self.zen.selected():
            self.core.addHomePath(i)


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

            self.thing.refresh()

        def setPath(self, path):
            self.core.setPath(path)
            self.thing.setPath(path)

    app = QApplication(sys.argv)
    # app.setStyle(QStyleFactory.create("Plastique"))
    app.setStyle(QStyleFactory.create("Fusion"))

    form = mainwin()
    form.show()
    # form.showFullScreen()
    # form.showMaximized()
    form.raise_()
    app.exec_()


