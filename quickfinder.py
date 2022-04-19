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
import urllib.request


import node
import setter
import finder
import view 
import mover 
import homepage
import preview 


class vchecker(QThread):
    version = pyqtSignal(object)
    def run(self):
        try:
            url = 'https://pxp-globals.s3.ap-southeast-1.amazonaws.com/quickfinderversion.txt'
            v = urllib.request.urlopen(url).read().decode('utf-8')
            if v[-1]=='\n': v = v[:-1]
            self.version.emit(v)
        except:
            print('version check failed')
            return


class blabel(QWidget):
    clicked = pyqtSignal()
    npath = pyqtSignal(object)
    home = pyqtSignal()
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
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        
        layout.addWidget(self.label)
        layout.addStretch()
        layout.addWidget(self.setbut)

    def clear(self):
        self.label.setText('')

    def setPath(self,path):
        if not os.path.isdir(path):
            path, file = os.path.split(path)
        self.label.setText(path)

    def mousePressEvent(self, event):
        self.label.clear()
        self.home.emit()
        super(blabel, self).mousePressEvent(event)


class primo(QWidget):
    npath = pyqtSignal(object)
    quit = pyqtSignal()
    def __init__(self, parent=None):
        super(primo, self).__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # self.setFont(QFont("Arial",10))
        self.layout = layout

        self.bros = []

        self.core = node.coreClass()
        self.core.setPath(os.path.expanduser("~"))
        self.core.scan()
        
        self.top = blabel()
        self.view = view.iconview(self.core)
        self.move = mover.mover()
        self.prev = preview.prevpane()
        self.split = QSplitter()
        self.stat = QStatusBar()

        self.npath.connect(self.view.setPath)
        self.npath.connect(self.top.setPath)
        self.view.npath.connect(self.setPath)
        self.view.ncopy.connect(self.move.copy)
        self.view.nmove.connect(self.move.move)
        self.view.nzip.connect(self.move.zipFunc)
        self.view.nunzip.connect(self.move.unzipFunc)
        self.view.quit.connect(self.quit)
        self.view.home.connect(self.top.clear)
        self.view.preview.connect(self.prev.preview)
        self.view.preview.connect(self.preview)
        self.view.segundo.connect(self.segundo)
        self.top.clicked.connect(self.setwin)
        self.top.home.connect(self.view.homeFunc)

        self.move.fileops.connect(self.fileops)

        self.view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.top.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.prev.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.split.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.view.refresh()

        layout.addWidget(self.top)
        layout.addWidget(self.split)
        layout.addWidget(self.stat)
        self.split.addWidget(self.view)
        self.split.addWidget(self.prev)
        self.split.setSizes([int(self.width()*(2/3)), int(self.width()*(1/3))])

        self.prev.hide()
        self.setupStatButtons()

    def setupStatButtons(self):
        self.joblabel = QLabel()
        self.stat.addPermanentWidget(self.joblabel)

        icbut = QPushButton('icon view')
        icbut.setIcon(QIcon(':/icons/iconview.png'))
        self.stat.addPermanentWidget(icbut)
        icbut.clicked.connect(self.view.zen.viewicons)
        icbut.setFocusPolicy(Qt.NoFocus)
        icbut.setToolTip('Ctrl + 1')

        treebut = QPushButton('list view')
        treebut.setIcon(QIcon(':/icons/treeview.png'))
        self.stat.addPermanentWidget(treebut)
        treebut.clicked.connect(self.view.zen.viewlist)
        treebut.setFocusPolicy(Qt.NoFocus)
        treebut.setToolTip('Ctrl + 2')

        prevbut = QPushButton('preview')
        prevbut.setIcon(QIcon(':/icons/colview.png'))
        self.stat.addPermanentWidget(prevbut)
        prevbut.clicked.connect(self.toggleprev)
        prevbut.setFocusPolicy(Qt.NoFocus)
        prevbut.setToolTip('Ctrl + 3')

        namebut = QPushButton('Name Sort')
        self.stat.addPermanentWidget(namebut)
        namebut.clicked.connect(self.view.zen.namesort)
        namebut.setFocusPolicy(Qt.NoFocus)
        namebut.setToolTip('Ctrl + 4')

        sizebut = QPushButton('Size Sort')
        self.stat.addPermanentWidget(sizebut)
        sizebut.clicked.connect(self.view.zen.sizesort)
        sizebut.setFocusPolicy(Qt.NoFocus)
        sizebut.setToolTip('Ctrl + 5')

        timebut = QPushButton('Sort Latest')
        self.stat.addPermanentWidget(timebut)
        timebut.clicked.connect(self.view.zen.timesort)
        timebut.setFocusPolicy(Qt.NoFocus)
        timebut.setToolTip('Ctrl + 6')

        deepbut = QPushButton('Deep Size')
        self.stat.addPermanentWidget(deepbut)
        deepbut.clicked.connect(self.view.zen.deepsort)
        deepbut.setFocusPolicy(Qt.NoFocus)
        deepbut.setToolTip('Ctrl + 7')

    def fileops(self, j):
        if j ==0: 
            self.joblabel.setText('')
            self.stat.showMessage('File Ops Finished' , 2000)
        else:
            self.joblabel.setText('File Ops : '+str(j))
        
    def setPath(self, path):
        self.core.setPath(path)
        self.npath.emit(path)

    def setwin(self):
        self.setwin = setter.setwin(self.core)
        self.setwin.show()

    def segundo(self, s):
        if s==0:
            w = mainwin()
            w.show()
            self.bros.append(w)
        if s==1:
            if self.prev.isVisible():
                self.prev.hide()
            else:
                self.prev.show()

    def toggleprev(self):
        if self.prev.isVisible():
            self.prev.hide()
        else:
            self.prev.show()        

    def preview(self, paths):
        if len(paths)==1:
            path = paths[0]
            n = self.core.locate(path)
            msg = '1 Selected,  ' + str(view.humanSize(n.size)) + '   Modified : ' + str(view.humanTime(n.mtime))
            self.stat.showMessage(msg)
            return
        size = 0
        for i in paths:
            n = self.core.locate(i)
            size+=n.size
        msg = str(len(paths)) + ' Selected, '+ str(view.humanSize(size))
        self.stat.showMessage(msg)


if __name__ == "__main__":
    multiprocessing.freeze_support()

    class mainwin(QMainWindow):
        def __init__(self, parent=None):
            super(mainwin, self).__init__(parent)

            self.setWindowTitle('Quick Finder 1.4.7')
            self.setWindowIcon(QIcon(':/icons/s7.ico'))
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
            self.thing.quit.connect(self.close)

            self.upper = vchecker(self)
            self.upper.version.connect(self.version)
            self.upper.finished.connect(self.upper.deleteLater)
            self.upper.start()

        def version(self, v):
            vset = setter.setter()
            lastversion = vset.get('aversion','no version')
            vset.set('aversion',v)
            if not v==lastversion:
                msg = QMessageBox()
                msg.setFont(QFont("Arial",14))
                msg.setIcon(QMessageBox.Information)
                msg.setText('Version '+ v + ' is available')
                msg.setInformativeText('Download at www.quickfinder.info')
                msg.setWindowTitle('Update available')
                msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Close)
                msg.setEscapeButton(QMessageBox.Close)
                retval = msg.exec_()
                if retval==1024:
                    import webbrowser
                    webbrowser.open('www.quickfinder.info',autoraise=True)

    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    app.setPalette(setter.darkPalette)

    form = mainwin()
    form.show()
    # form.showFullScreen()
    # form.showMaximized()
    form.raise_()
    app.exec_()
