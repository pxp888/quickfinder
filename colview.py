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
import treeview 


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


class cview(QColumnView):
    back = pyqtSignal()
    def mousePressEvent(self, event):
        if event.button()==8:
            self.back.emit()
            return
        super(cview, self).mousePressEvent(event)



class colviewer(treeview.treeviewer):
    def __init__(self, core, parent=None):
        super(QWidget, self).__init__(parent)
        layout = QHBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # self.setFont(QFont("Arial",10))
        # self.setFont(QFont("MS Shell Dlg 2",10))
        self.layout = layout

        self.ctrlkey = False

        self.core = core 

        self.mod = QFileSystemModel()
        self.view = cview()
        self.view.setModel(self.mod)
        self.mod.setRootPath(os.path.expanduser("~"))
        # self.view.setRootIndex(self.mod.index(os.path.expanduser("~")))
        self.view.setRootIndex(self.mod.index(self.core.n.fpath()))
        self.mod.setReadOnly(False)

        # self.view.setSortingEnabled(True)
        self.view.setSelectionMode(3)
        self.view.setEditTriggers(QAbstractItemView.EditKeyPressed)
        # self.view.header().setStretchLastSection(False)
        # self.view.header().setSectionResizeMode(0,1)
        # self.view.header().setSectionResizeMode(1,3)
        # self.view.header().setSectionResizeMode(2,3)
        # self.view.header().setSectionResizeMode(3,3)
        # self.view.setVerticalScrollMode(1)

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







# hello
