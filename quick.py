from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import os
import sys
import time
import pickle
from queue import Queue
import threading
import multiprocessing

import node
import setter
import iconview
import finder
import preview
import colview
import treeview

######################################################################################################################################################


class blabel(QWidget):
    clicked = pyqtSignal()
    def __init__(self, parent=None):
        super(blabel, self).__init__(parent)
        layout = QHBoxLayout()
        self.setLayout(layout)
        # layout.setContentsMargins(0, 0, 0, 0)
        # layout.setSpacing(0)
        self.label = QLabel()
        self.label.setFont(QFont("Arial",14))

        self.settingicon = QIcon(':/icons/settings.png')
        self.setbut = QPushButton()
        self.setbut.setIcon(self.settingicon)
        self.setbut.clicked.connect(self.clicked)
        self.setbut.setFocusPolicy(Qt.NoFocus)

        layout.addWidget(self.label)
        layout.addStretch()
        layout.addWidget(self.setbut)

    def setPath(self,path):
        if not os.path.isdir(path):
            path, file = os.path.split(path)
        self.label.setText(path)


######################################################################################################################################################


class primo(QWidget):
    npath = pyqtSignal(object)
    def __init__(self, parent=None):
        super(primo, self).__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # self.setFont(QFont("Arial",10))
        self.layout = layout

        self.set = setter.setter('quickfinder1')

        home = os.path.expanduser("~")
        self.core = node.coreClass()
        self.core.setPath(home)
        # self.core.scan()

        self.eye = QFileSystemWatcher()
        self.ctrlkey = False

        self.core.addSnifPath(home)
        self.core.addSnifPath('D:\\')
        self.core.n = self.core.sniffer
        self.core.scan()


        self.label = blabel()
        self.fin = finder.finderview(self.core)
        self.view = iconview.iconview(self.core)
        self.prev = preview.prevpane()
        self.stat = QStatusBar()

        self.eye.directoryChanged.connect(self.changes)
        self.label.clicked.connect(self.setwin)
        self.npath.connect(self.label.setPath)
        self.fin.npath.connect(self.setPath)
        self.fin.searching.connect(self.searching)

        self.fin.line.returnPressed.connect(self.view.view.setFocus)
        self.npath.connect(self.view.setPath)
        self.view.npath.connect(self.setPath)
        self.view.kevin.connect(self.kevin)
        self.view.preview.connect(self.preview)
        self.view.preview.connect(self.prev.preview)
        self.view.zen.shortcut.connect(self.shortcut)

        self.sbs = QSplitter()
        self.sbs.addWidget(self.view)
        self.sbs.addWidget(self.prev)
        self.sbs.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.sbs.setStretchFactor(0,2)

        layout.addWidget(self.label)
        layout.addWidget(self.fin)
        layout.addWidget(self.sbs)
        layout.addWidget(self.stat)

        # self.setPath(home)
        # self.view.refresh2()

        icbut = QPushButton('Icon View')
        self.stat.addPermanentWidget(icbut)
        icbut.clicked.connect(self.icview)
        icbut.setFocusPolicy(Qt.NoFocus)

        colbut = QPushButton('Column View')
        self.stat.addPermanentWidget(colbut)
        colbut.clicked.connect(self.colview)
        colbut.setFocusPolicy(Qt.NoFocus)

        treebut = QPushButton('Tree View')
        self.stat.addPermanentWidget(treebut)
        treebut.clicked.connect(self.treeview)
        treebut.setFocusPolicy(Qt.NoFocus)

        deepbut = QPushButton('Size Scan')
        self.stat.addPermanentWidget(deepbut)
        deepbut.clicked.connect(self.deepscan)
        deepbut.setFocusPolicy(Qt.NoFocus)

        prevbut = QPushButton('Preview')
        self.stat.addPermanentWidget(prevbut)
        prevbut.clicked.connect(self.toggleprev)
        prevbut.setFocusPolicy(Qt.NoFocus)

        self.prev.setFocusPolicy(Qt.NoFocus)

    def toggleprev(self):
        if self.prev.isVisible():
            self.prev.hide()
        else:
            self.prev.show()

    def deepscan(self):
        self.core.fullscan()
        self.view.refresh1()
        self.core.n.getsize()
        self.core.n.sort(1,0)
        self.view.refresh2()

    def colview(self):
        old = self.view
        old.cleanup()
        self.view = colview.colviewer(self.core)
        self.sbs.replaceWidget(0,self.view)
        self.sbs.setStretchFactor(0,2)
        self.fin.line.returnPressed.connect(self.view.view.setFocus)
        self.npath.connect(self.view.setPath)
        self.view.npath.connect(self.setPath)
        self.view.hopPath.connect(self.hopPath)
        self.view.preview.connect(self.preview)
        self.view.preview.connect(self.prev.preview)
        old.deleteLater()

    def icview(self):
        self.view.cleanup()
        self.newview = iconview.iconview(self.core)
        self.sbs.replaceWidget(0,self.newview)
        self.sbs.setStretchFactor(0,2)
        self.npath.connect(self.newview.setPath)
        self.fin.line.returnPressed.connect(self.newview.view.setFocus)
        self.newview.npath.connect(self.setPath)
        self.newview.kevin.connect(self.kevin)
        self.newview.preview.connect(self.preview)
        self.newview.preview.connect(self.prev.preview)
        self.newview.refresh2()
        self.view.deleteLater()
        self.view = self.newview
        self.view.zen.shortcut.connect(self.shortcut)

    def treeview(self):
        self.view.cleanup()
        self.newview = treeview.treeviewer(self.core)
        self.sbs.replaceWidget(0,self.newview)
        self.sbs.setStretchFactor(0,2)
        self.fin.line.returnPressed.connect(self.newview.view.setFocus)
        self.npath.connect(self.newview.setPath)
        self.newview.npath.connect(self.setPath)
        self.newview.hopPath.connect(self.hopPath)
        self.newview.preview.connect(self.preview)
        self.newview.preview.connect(self.prev.preview)
        self.view.deleteLater()
        self.view = self.newview

    def changes(self, path):
        # print('chg',time.time(), path)
        n = self.core.locate(path)
        if not n.up==None: n = n.up
        self.view.refresh1()
        self.core.scan(n)
        self.view.refresh2()

    def kevin(self, event):
        self.fin.line.setFocus()
        self.fin.line.keyPressEvent(event)

    def setPath(self, path):
        self.core.setPath(path)
        self.npath.emit(path)
        dirs = self.eye.directories()
        if len(dirs)==0:
            self.eye.addPath(path)
        else:
            if not path in dirs:
                self.eye.removePaths(dirs)
                self.eye.addPath(path)

    def hopPath(self, path):
        n = self.core.locate(path)
        self.view.refresh1()
        self.core.scan(n)
        self.view.refresh2()
        dirs = self.eye.directories()
        cpath = self.core.n.fpath()
        for i in dirs:
            if not i==cpath: self.eye.removePath(i)
        while 1:
            self.eye.addPath(path)
            path, name = os.path.split(path)
            if path==cpath: break

    def searching(self, n):
        if n==1:
            self.sbs.hide()
        else:
            self.sbs.show()

    def keyPressEvent(self, event):
        x = event.key()
        # print('primo',x)
        if self.ctrlkey:
            if x==49: self.icview()
            if x==50: self.colview()
            if x==51: self.treeview()
            if x==52: self.deepscan()
            if x==53: self.toggleprev()
            return
        if x==16777249:
            self.ctrlkey=True
            # return
        super(primo,self).keyPressEvent(event)

    def keyReleaseEvent(self, event):
        x = event.key()
        if x==16777249:
            self.ctrlkey=False
            # return
        super(primo,self).keyReleaseEvent(event)

    def setwin(self):
        self.setwin = setter.setwin(self.core)
        self.setwin.show()

    def preview(self, paths):
        if len(paths)==1:
            path = paths[0]
            n = self.core.locate(path)
            msg = '1 Selected,  ' + str(colview.humanSize(n.size)) + '   Modified : ' + str(colview.humanTime(n.mtime))
            self.stat.showMessage(msg)
            return
        size = 0
        for i in paths:
            n = self.core.locate(i)
            size+=n.size
        msg = str(len(paths)) + ' Selected, '+ str(colview.humanSize(size))
        self.stat.showMessage(msg)

    def shortcut(self, n):
        if n==0: self.icview()
        if n==1: self.colview()
        if n==2: self.treeview()
        if n==3: self.deepscan()
        if n==4: self.toggleprev()


######################################################################################################################################################


if __name__ == "__main__":
    multiprocessing.freeze_support()

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
            self.resize(1600,900)

            self.thing = primo()
            layout.addWidget(self.thing)
            self.thing.npath.connect(self.setWindowTitle)


    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    app.setPalette(setter.darkPalette)

    form = mainwin()
    form.show()
    # form.showFullScreen()
    # form.showMaximized()
    form.raise_()
    app.exec_()
