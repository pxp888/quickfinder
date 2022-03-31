from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import os
import sys
import time
import pickle
import threading
import multiprocessing
import subprocess

import node
import setter
import iconview
import finder
import preview
# import treeview
import homepage
import mover
import listview 


######################################################################################################################################################


class blabel(QWidget):
    clicked = pyqtSignal()
    npath = pyqtSignal(object)
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

    def mousePressEvent(self, event):
        self.npath.emit('home')
        super(blabel, self).mousePressEvent(event)


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
        self.mover = mover.mover()

        home = os.path.expanduser("~")
        self.core = node.coreClass()
        self.core.setPath(home)

        self.ctrlkey = False

        self.bros = []

        self.homepage = homepage.homeClass(self.core)
        self.homepage.setup()

        self.label = blabel()
        self.fin = finder.finderview(self.core)
        self.view = iconview.iconview(self.core)
        self.prev = preview.prevpane()
        self.stat = QStatusBar()

        self.prev.setFocusPolicy(Qt.NoFocus)

        self.label.clicked.connect(self.setwin)
        self.label.npath.connect(self.setPath)
        self.npath.connect(self.label.setPath)
        self.fin.npath.connect(self.setPath)
        self.fin.searching.connect(self.searching)
        self.homepage.npath.connect(self.setPath)
        self.homepage.kevin.connect(self.kevin)
        self.homepage.nmove.connect(self.mover.move)

        self.fin.line.returnPressed.connect(self.view.view.setFocus)
        self.npath.connect(self.view.setPath)
        self.view.npath.connect(self.setPath)
        self.view.kevin.connect(self.kevin)
        self.view.preview.connect(self.preview)
        self.view.preview.connect(self.prev.preview)
        self.view.nmove.connect(self.mover.move)
        self.view.ncopy.connect(self.mover.copy)
        self.view.segundo.connect(self.segundo)

        self.sbs = QSplitter()
        self.sbs.addWidget(self.view)
        self.sbs.addWidget(self.prev)
        self.sbs.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.sbs.setSizes([int(self.width()*(2/3)), int(self.width()*(1/3))])

        layout.addWidget(self.label)
        layout.addWidget(self.fin)
        layout.addWidget(self.homepage)
        layout.addWidget(self.sbs)
        layout.addWidget(self.stat)

        self.sbs.hide()
        self.front='home'

        self.setupStatButtons()

        self.prev.setVisible(self.set.get('previewvisible',True))

    def focusOutEvent(self, event):
        self.shiftkey = False
        self.ctrlkey = False
        super(primo, self).focusOutEvent(event)

    def setupStatButtons(self):
        icbut = QPushButton('')
        icbut.setIcon(QIcon(':/icons/iconview.png'))
        self.stat.addPermanentWidget(icbut)
        icbut.clicked.connect(self.showIconView)
        icbut.setFocusPolicy(Qt.NoFocus)
        icbut.setToolTip('Ctrl + 1')

        treebut = QPushButton('')
        treebut.setIcon(QIcon(':/icons/treeview.png'))
        self.stat.addPermanentWidget(treebut)
        treebut.clicked.connect(self.showTreeView)
        treebut.setFocusPolicy(Qt.NoFocus)
        treebut.setToolTip('Ctrl + 2')

        prevbut = QPushButton('')
        prevbut.setIcon(QIcon(':/icons/colview.png'))
        self.stat.addPermanentWidget(prevbut)
        prevbut.clicked.connect(self.toggleprev)
        prevbut.setFocusPolicy(Qt.NoFocus)
        prevbut.setToolTip('Ctrl + 3')

        namebut = QPushButton('Name Sort')
        self.stat.addPermanentWidget(namebut)
        namebut.clicked.connect(self.namescan)
        namebut.setFocusPolicy(Qt.NoFocus)
        namebut.setToolTip('Ctrl + 4')

        deepbut = QPushButton('Size Sort')
        self.stat.addPermanentWidget(deepbut)
        deepbut.clicked.connect(self.deepscan)
        deepbut.setFocusPolicy(Qt.NoFocus)
        deepbut.setToolTip('Ctrl + 5')

        timebut = QPushButton('Sort Latest')
        self.stat.addPermanentWidget(timebut)
        timebut.clicked.connect(self.timescan)
        timebut.setFocusPolicy(Qt.NoFocus)
        timebut.setToolTip('Ctrl + 6')

    def toggleprev(self):
        if self.prev.isVisible():
            self.prev.hide()
            self.set.set('previewvisible',False)
        else:
            self.prev.show()
            self.set.set('previewvisible',True)

    def namescan(self):
        self.view.namescan()

    def deepscan(self):
        self.view.deepscan()

    def timescan(self):
        self.view.timescan()

    def showTreeView(self):
        if self.core.n==self.core.sniffer: self.setPath(os.path.expanduser("~"))
        self.view.cleanup()
        self.newview = listview.listview(self.core)
        self.sbs.replaceWidget(0,self.newview)
        self.sbs.setSizes([int(self.width()*(2/3)), int(self.width()*(1/3))])
        self.npath.connect(self.newview.setPath)
        self.fin.line.returnPressed.connect(self.newview.view.setFocus)
        self.newview.npath.connect(self.setPath)
        self.newview.kevin.connect(self.kevin)
        self.newview.preview.connect(self.preview)
        self.newview.preview.connect(self.prev.preview)
        self.newview.nmove.connect(self.mover.move)
        self.newview.ncopy.connect(self.mover.copy)
        self.newview.refresh()
        self.view.deleteLater()
        self.view = self.newview
        self.view.segundo.connect(self.segundo)

    def showIconView(self):
        if self.core.n==self.core.sniffer: self.setPath(os.path.expanduser("~"))
        self.view.cleanup()
        self.newview = iconview.iconview(self.core)
        self.sbs.replaceWidget(0,self.newview)
        self.sbs.setSizes([int(self.width()*(2/3)), int(self.width()*(1/3))])
        self.npath.connect(self.newview.setPath)
        self.fin.line.returnPressed.connect(self.newview.view.setFocus)
        self.newview.npath.connect(self.setPath)
        self.newview.kevin.connect(self.kevin)
        self.newview.preview.connect(self.preview)
        self.newview.preview.connect(self.prev.preview)
        self.newview.nmove.connect(self.mover.move)
        self.newview.ncopy.connect(self.mover.copy)
        self.newview.refresh()
        self.view.deleteLater()
        self.view = self.newview
        self.view.segundo.connect(self.segundo)

    def kevin(self, event):
        self.fin.line.setFocus()
        self.fin.line.keyPressEvent(event)

    def setPath(self, path):
        if path=='home':
            path = os.path.expanduser("~")
            self.sbs.hide()
            self.homepage.show()
            self.homepage.setup()
            self.label.label.setText('')
            self.front='home'
            return
        else:
            self.sbs.show()
            self.homepage.hide()
            self.front='view'

        self.core.setPath(path)
        self.npath.emit(path)

    def searching(self, n):
        if n==1:
            self.sbs.hide()
            self.homepage.hide()
        else:
            if self.front=='home':
                self.homepage.show()
            else:
                self.sbs.show()

    def keyPressEvent(self, event):
        x = event.key()
        # print('primo',x)
        if self.ctrlkey:
            if x==49: self.showIconView()
            if x==50: self.showTreeView()
            if x==51: self.toggleprev()
            if x==52: self.namescan()
            if x==53: self.deepscan()
            if x==54: self.timescan()
            if x==78: self.segundo()
            if x==84: self.terminal1()
            if x==76: self.terminal2()
            return
        if x==16777249: self.ctrlkey=True
        super(primo,self).keyPressEvent(event)

    def terminal1(self):
        path = self.core.n.fpath()
        if path=='': path = os.path.expanduser("~")
        os.chdir(path)
        subprocess.run('start cmd',shell=True)

    def terminal2(self):
        path = self.core.n.fpath()
        if path=='': path = os.path.expanduser("~")
        os.chdir(path)
        subprocess.run('start wsl',shell=True)

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
            msg = '1 Selected,  ' + str(listview.humanSize(n.size)) + '   Modified : ' + str(listview.humanTime(n.mtime))
            self.stat.showMessage(msg)
            return
        size = 0
        for i in paths:
            n = self.core.locate(i)
            size+=n.size
        msg = str(len(paths)) + ' Selected, '+ str(listview.humanSize(size))
        self.stat.showMessage(msg)

    def segundo(self):
        w = mainwin()
        w.show()
        self.bros.append(w)


######################################################################################################################################################


if __name__ == "__main__":
    multiprocessing.freeze_support()

    class mainwin(QMainWindow):
        def __init__(self, parent=None):
            super(mainwin, self).__init__(parent)

            self.setWindowTitle('Speedy Finder')
            frame = QFrame()
            self.setCentralWidget(frame)
            layout = QGridLayout()
            frame.setLayout(layout)
            layout.setContentsMargins(1,1,1,1)
            layout.setSpacing(1)
            self.resize(1400,800)

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
