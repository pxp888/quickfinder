from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import os
import sys
import time
import stat 
import shutil 
import zipfile 

from queue import Queue
import threading

import node
import setter
import mover 

def humanTime(t):
    lt = time.localtime(t)
    # n = str(lt[0]) + '-'+ str(lt[1]) +'-'+ str(lt[2]) + '   ' + str(lt[3]) + ':' + str(lt[4])
    n = str(lt[0]) + '-'+ str(lt[1]).zfill(2) +'-'+ str(lt[2]).zfill(2) + '      ' + str(lt[3]).zfill(2) + ':' + str(lt[4]).zfill(2) + ' '
    return str(n)

def humanSize(s):
    if s > 1073741824: return str(round(s/1073741824,2))+'  G  '
    if s > 1048576: return str(int(round(s/1048576,0)))+'  m  '
    if s > 1024: return str(int(round(s/1024,0)))+'  k  '
    if s < 10: return '  '
    return str(s)+'  b  '


######################################################################################################################################################


class tview(QTreeView):
    back = pyqtSignal()
    def mousePressEvent(self, event):
        if event.button()==8:
            self.back.emit()
            return
        super(tview, self).mousePressEvent(event)


######################################################################################################################################################


class treeviewer(QWidget):
    npath = pyqtSignal(object)
    preview = pyqtSignal(object)
    nmove = pyqtSignal(object, object)
    ncopy = pyqtSignal(object, object)
    def __init__(self, core, parent=None):
        super(treeviewer, self).__init__(parent)
        layout = QHBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # self.setFont(QFont("Arial",12))
        # self.setFont(QFont("MS Shell Dlg 2",10))
        self.layout = layout

        self.ctrlkey = False

        self.core = core 

        self.mod = QFileSystemModel()
        self.view = tview()
        self.view.setModel(self.mod)
        self.mod.setRootPath(os.path.expanduser("~"))
        # self.view.setRootIndex(self.mod.index(os.path.expanduser("~")))
        self.view.setRootIndex(self.mod.index(self.core.n.fpath()))
        self.mod.setReadOnly(False)

        self.view.setSortingEnabled(True)
        self.view.setSelectionMode(3)
        self.view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.view.header().setStretchLastSection(False)
        self.view.header().setSectionResizeMode(0,1)
        self.view.header().setSectionResizeMode(1,3)
        self.view.header().setSectionResizeMode(2,3)
        self.view.header().setSectionResizeMode(3,3)
        self.view.setVerticalScrollMode(1)

        self.view.doubleClicked.connect(self.doubleClicked)
        self.view.back.connect(self.back)
        self.view.selectionModel().selectionChanged.connect(self.updatepreview)
        
        layout.addWidget(self.view)

        self.copyAction = QAction("Copy",self)
        self.pasteAction = QAction("Paste",self)
        self.zipAction = QAction("ZIP Selection",self)
        self.deleteAction = QAction("Delete Selection",self)
        self.noIndexAction = QAction("No Index",self)
        self.noNameAction = QAction("Ignore Name",self)
        self.noPathAction = QAction("Ignore Path",self)
        self.addHomePathAction = QAction("Add Index Path",self)

        self.deleteAction.triggered.connect(self.deleteFiles)
        self.copyAction.triggered.connect(self.copyToClip)
        self.zipAction.triggered.connect(self.zipFunc)
        self.deleteAction.triggered.connect(self.deleteFiles)
        self.noIndexAction.triggered.connect(self.noIndexFunc)
        self.noNameAction.triggered.connect(self.noNameFunc)
        self.noPathAction.triggered.connect(self.noPathFunc)
        self.addHomePathAction.triggered.connect(self.addHomePathFunc)

        self.setAcceptDrops(True)
        self.view.setAcceptDrops(True)
        self.view.setDragEnabled(True)
        self.view.setDragDropMode(4)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        dest = self.core.n.fpath()
        for i in e.mimeData().urls():
            self.nmove.emit(i.path(), dest)

    def keyPressEvent(self, event):
        x = event.key()
        # print(x)
        if self.ctrlkey:
            if x==67: self.copyToClip()
            if x==86: self.pasteFromClip()
        if x==16777249: self.ctrlkey=True
        if x==16777220: self.entered()
        if x==16777219: self.back()
        if x==16777223: self.deleteFiles()
        if x==16777216: self.escaped()
        if x==16777265: self.rename()
        super(treeviewer, self).keyPressEvent(event)

    def keyReleaseEvent(self, event):
        x = event.key()
        if x==16777249: self.ctrlkey=False
        super(treeviewer,self).keyReleaseEvent(event)

    def wheelEvent(self, event):
        font = self.font()
        fsize = font.pointSize()
        if self.ctrlkey:
            if event.angleDelta().y() > 0:
                fsize+=1
            else:
                fsize-=1
        font.setPointSize(fsize)
        self.setFont(font)

    def escaped(self):
        cur = self.view.selectedIndexes()
        if len(cur) > 0:
            self.view.clearSelection()
        else:
            self.npath.emit('home')

    def selectedPaths(self):
        idx = self.view.selectedIndexes()
        cur = []
        for i in idx:
            if i.column()==0:
                cur.append(self.mod.fileInfo(i).filePath())
        return cur 

    def entered(self):
        cur = self.selectedPaths()
        if len(cur)==0:
            os.startfile(self.core.n.fpath())
            return
        if len(cur)==1:
            if os.path.isdir(cur[0]):
                self.npath.emit(cur[0])
                return
        for i in cur: os.startfile(i)
        print(cur)

    def setPath(self, path):
        self.view.clearSelection()
        if os.path.isdir(path):
            i = self.mod.index(path)
            self.view.setRootIndex(i)
        else:
            bpath, file = os.path.split(path)
            i = self.mod.index(bpath)
            self.view.setRootIndex(i)
            target = self.mod.index(path)
            self.view.selectionModel().setCurrentIndex(target,QItemSelectionModel.Select)

    def back(self):
        path = self.core.back()
        self.npath.emit(path)

    def doubleClicked(self, idx):
        path = self.mod.fileInfo(idx).filePath()
        if os.path.isdir(path): self.npath.emit(path)

    def contextMenuEvent(self, event):
        cur = self.selectedPaths()
        if len(cur)>0:
            menu = QMenu(self)
            menu.setPalette(self.palette())
            menu.addAction(self.copyAction)
            menu.addAction(self.pasteAction)
            menu.addAction(self.zipAction)
            menu.addAction(self.deleteAction)
            menu.addAction(self.addHomePathAction)
            menu.addAction(self.noIndexAction)
            menu.addAction(self.noNameAction)
            menu.addAction(self.noPathAction)
            menu.exec(event.globalPos())
        else:
            menu = QMenu(self)
            menu.setPalette(self.palette())
            menu.addAction(self.pasteAction)
            menu.exec(event.globalPos())
    
    def copyToClip(self):
        print('tree copy')
        cur = self.selectedPaths()
        if not cur: return 
        urls = []
        for i in cur: urls.append(QUrl().fromLocalFile(i))
        mimedata = QMimeData()
        mimedata.setUrls(urls)
        QGuiApplication.clipboard().setMimeData(mimedata)

    def pasteFromClip(self):
        print('tree paste')
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
                        self.ncopy.emit(i.path(), target)
                    else:
                        target = os.path.join(dest, name) + ' Copy'
                        self.ncopy.emit(i.path(), target)
                else:
                    self.ncopy.emit(i.path(), target)

    def updatepreview(self):
        cur = self.selectedPaths()
        self.preview.emit(cur)

    def deleteFiles(self):
        cur = self.selectedPaths()
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
        cur = self.selectedPaths()
        if not cur: return 
        self.namer = mover.renameClass()
        self.namer.populate(cur)
        self.namer.show()

    def zipFunc(self):
        src = self.selectedPaths()
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

    def noIndexFunc(self, event):
        cur = self.view.selectedIndexes()
        for it in cur:
            if it.column()==0:
                n = self.mod.data(it,257)
                self.mod.core.ff.addNoIndex(n.fpath())
                self.set.set('ff',self.mod.core.ff)

    def noNameFunc(self, event):
        cur = self.view.selectedIndexes()
        for it in cur:
            if it.column()==0:
                n = self.mod.data(it,257)
                self.mod.core.ff.addName(n.name)
                self.set.set('ff',self.mod.core.ff)

    def noPathFunc(self, event):
        cur = self.view.selectedIndexes()
        for it in cur:
            if it.column()==0:
                n = self.mod.data(it,257)
                self.mod.core.ff.addPath(n.fpath())
                self.set.set('ff',self.mod.core.ff)

    def addHomePathFunc(self):
        cur = self.view.selectedIndexes()
        for it in cur:
            if it.column()==0:
                n = self.mod.data(it,257)
                self.mod.core.addHomePath(n.fpath())
                self.set.set('ff',self.mod.core.ff)

    def refresh1(self):
        pass 
    def refresh2(self):
        pass 
    def cleanup(self):
        pass 
    def deepscan(self):
        self.view.header().setSortIndicator(1,1)
    def timescan(self):
        self.view.header().setSortIndicator(3,1)

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
            self.resize(900,600)

            self.core = node.coreClass()
            self.core.setPath(os.path.expanduser("~"))
            self.core.scan()
            self.thing = treeviewer(self.core)
            layout.addWidget(self.thing)

            self.thing.npath.connect(self.thing.setPath)


            self.setPalette(setter.darkPalette)



    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))

    form = mainwin()
    form.show()
    # form.showFullScreen()
    # form.showMaximized()
    form.raise_()
    app.exec_()












# hello
