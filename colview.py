from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import os
import sys
import time

from queue import Queue
import threading

import node
import setter

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


class TreeModel(QAbstractItemModel):
    def __init__(self, core, parent=None):
        super(TreeModel, self).__init__(parent)

        self.icon = setter.iconMaker()

        self.core = core
        self.base = core.n

    def columnCount(self, parent):
        if parent.isValid():
            return 3
        else:
            return 3

    def data(self, index, role):
        if not index.isValid():
            return None
        if role == 257:
            item = index.internalPointer()
            return item
        if role == 256:
            item = index.internalPointer()
            if index.column()==1: return item.size
            if index.column()==2: return item.mtime
            return item.name
        if role == Qt.DisplayRole:
            item = index.internalPointer()
            if index.column()==1: return humanSize(item.size)
            if index.column()==2: return humanTime(item.mtime)
            return item.name
        if role == Qt.DecorationRole:
            if index.column()==0:
                item = index.internalPointer()
                return QVariant(self.icon.icon(item.name, item.dir))
            return None
        if role == Qt.TextAlignmentRole:
            if index.column()==1:
                return Qt.AlignRight
            return Qt.AlignLeft
        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        if index.internalPointer().dir:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section==0: return "File Name"
            if section==1: return "Size"
            if section==2: return "Last Modified"
        return None

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        if not parent.isValid():
            parentItem = self.base
        else:
            parentItem = parent.internalPointer()
        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
        childItem = index.internalPointer()
        parentItem = childItem.up
        if parentItem == self.base:
            return QModelIndex()
        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent):
        # if parent.column() > 0:
        #     return 0
        if not parent.isValid():
            parentItem = self.base
        else:
            parentItem = parent.internalPointer()
        return len(parentItem.kids)
        # if parentItem.model==True:
        #     return len(parentItem.kids)
        # else:
        #     return 0


######################################################################################################################################################


class colviewer(QWidget):
    npath = pyqtSignal(object)
    preview = pyqtSignal(object)
    hopPath = pyqtSignal(object)
    shortcut = pyqtSignal(object)
    def __init__(self, core, parent=None):
        super(colviewer, self).__init__(parent)
        layout = QHBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setFont(QFont("Arial",10))
        self.layout = layout

        self.core = core

        self.mod = TreeModel(core)
        self.view = QColumnView()
        self.view.setModel(self.mod)
        self.view.setSelectionMode(3)

        self.layout.addWidget(self.view)

        # self.view.selectionModel().currentChanged.connect(self.hop)
        self.view.selectionModel().selectionChanged.connect(self.selupdate)

    def cleanup(self):
        pass

    def setPath(self, path):
        self.mod.beginResetModel()
        self.mod.base = self.mod.core.locate(path)
        self.mod.endResetModel()

    def refresh1(self):
        self.mod.layoutAboutToBeChanged.emit()

    def refresh2(self):
        self.mod.layoutChanged.emit()

    def selupdate(self, a, b):
        cur = self.view.selectedIndexes()
        out = []
        for i in cur:
            n = self.mod.data(i,257)
            out.append(n.fpath())
        self.preview.emit(out)
        if len(out)>0:
            self.hopPath.emit(out[-1])

    def keyPressEvent(self, event):
        x = event.key()
        print('cv',x)

        if x==16777220:  #''' Enter '''
            self.entered()
            return
        if x==16777216:  #''' ESC key '''
            cur = self.view.selectedIndexes()
            if len(cur) > 0:
                self.view.clearSelection()
            else:
                # self.npath.emit(os.path.expanduser("~"))
                self.npath.emit('home')
            return
        if x==16777219:  # backspace
            path = self.core.back()
            self.npath.emit(path)
            return
        super(colviewer, self).keyPressEvent(event)

    def entered(self):
        cur = self.view.selectedIndexes()
        out = []
        for i in cur:
            n = self.mod.data(i,257)
            out.append(n)
        if len(out)==0:
            os.startfile(self.core.n.fpath())
        if len(out)==1:
            if out[0].dir:
                self.npath.emit(out[0].fpath())
            else:
                os.startfile(out[0].fpath())
        if len(out)>1:
            for i in out:
                os.startfile(i.fpath())


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
            self.thing = colviewer(self.core)
            layout.addWidget(self.thing)


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
