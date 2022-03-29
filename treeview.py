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
    hopPath = pyqtSignal(object)
    nmove = pyqtSignal(object, object)
    def __init__(self, core, parent=None):
        super(treeviewer, self).__init__(parent)
        layout = QHBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # self.setFont(QFont("Arial",10))
        # self.setFont(QFont("MS Shell Dlg 2",10))
        self.layout = layout

        self.core = core 

        self.mod = QFileSystemModel()
        self.view = tview()
        self.view.setModel(self.mod)
        self.mod.setRootPath(os.path.expanduser("~"))
        self.view.setRootIndex(self.mod.index(os.path.expanduser("~")))
        self.mod.setReadOnly(False)

        self.view.setSortingEnabled(True)
        self.view.setSelectionMode(3)
        self.view.setEditTriggers(QAbstractItemView.EditKeyPressed)
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

    def keyPressEvent(self, event):
        x = event.key()
        # print(x)
        if x==16777220: self.entered()
        if x==16777219: self.back()
        if x==16777223: self.deleteFiles()
        if x==16777216: self.escaped()
        super(treeviewer, self).keyPressEvent(event)

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


    def refresh1(self):
        pass 
    def refresh2(self):
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
