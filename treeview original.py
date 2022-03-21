from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import os
import sys
import time

from queue import Queue
import threading

from node import *
from setter import *

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
    preview = pyqtSignal(object)
    def __init__(self, core, parent=None):
        super(TreeModel, self).__init__(parent)

        self.icon = iconMaker()

        self.core = core
        self.base = core.n
        self.eye = QFileSystemWatcher()

    def setPath(self, path):
        self.beginResetModel()
        self.base = self.core.setPath(path)
        self.endResetModel()
        self.eye.addPath(path)

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
        childItem = parentItem.kids[row]
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


class treeviewer(QWidget):
    npath = pyqtSignal(object)
    home = pyqtSignal()
    preview = pyqtSignal(object)
    def __init__(self, core, parent=None):
        super(treeviewer, self).__init__(parent)
        layout = QHBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # self.setFont(QFont("Arial",10))
        self.layout = layout

        self.set = setter('quickfinder')

        self.mod = TreeModel(core)
        self.view = QTreeView()
        self.proxmod = QSortFilterProxyModel()
        self.proxmod.setSourceModel(self.mod)
        self.view.setModel(self.proxmod)
        self.view.setSelectionMode(3)
        self.proxmod.setSortRole(256)
        self.proxmod.setDynamicSortFilter(True)
        self.view.setSortingEnabled(True)
        self.view.header().setStretchLastSection(False)
        self.view.header().setSectionResizeMode(0,1)
        self.view.header().setSectionResizeMode(1,3)
        self.view.header().setSectionResizeMode(2,3)

        self.view.selectionModel().currentChanged.connect(self.hop)
        self.view.doubleClicked.connect(self.activated)
        self.layout.addWidget(self.view)

        self.mod.eye.directoryChanged.connect(self.changes)

        self.noIndexAction = QAction("No Index",self)
        self.noNameAction = QAction("Ignore Name",self)
        self.noPathAction = QAction("Ignore Path",self)
        self.noIndexAction.triggered.connect(self.noIndexFunc)
        self.noNameAction.triggered.connect(self.noNameFunc)
        self.noPathAction.triggered.connect(self.noPathFunc)

    def stop(self):
        pass

    def dirSize(self):
        if self.mod.core.qin.qsize()==0:
            self.mod.core.dirSize2(self.mod.base)
            self.proxmod.layoutChanged.emit()

    def activated(self, it):
        # print('act',time.time())
        if it.column()==0:
            path = self.proxmod.data(it,257).fpath()
            os.startfile(path)

    def setPath(self, path):
        name = ''
        if not os.path.isdir(path):
            path, name = os.path.split(path)
        self.mod.setPath(path)

        if not name=='':
            n=self.mod.core.locate(path)
            if n==None:
                print('no n')
                return
            row = n.knames.index(name)
            i = self.mod.index(row,0,self.view.rootIndex())
            i = self.proxmod.mapFromSource(i)
            self.view.setCurrentIndex(i)

    def hop(self, np, p):
        n = self.proxmod.data(np,257)
        # print('hop',n.fpath())
        if n==None: return

        self.mod.core.scan(n,2)
        self.proxmod.layoutChanged.emit()

        for i in self.mod.eye.directories(): self.mod.eye.removePath(i)
        self.mod.eye.addPaths(n.treepath())

        if np.column()==0:
            n = self.proxmod.data(np,257)
            if not n.dir:
                self.preview.emit(n.fpath())
            else:
                self.preview.emit('')

    def changes(self, path):
        # print('chg',time.time(),path)
        n = self.mod.core.locate(path)
        if n==None: return
        if not n.up==None:
            n = n.up
            self.mod.core.scan(n,3)
        else:
            self.mod.core.scan(n,2)
        self.proxmod.layoutChanged.emit()

    def keyPressEvent(self, event):
        x = event.key()
        # print(x)
        if x==16777220:
            self.enter()
        if x==16777216:
            self.escape()
            return
        if x==16777219:
            path, fil = os.path.split(self.mod.base.fpath())
            self.npath.emit(path)
            return
        super(treeviewer, self).keyPressEvent(event)

    def escape(self):
        sel = self.view.selectionModel().selectedIndexes()
        if len(sel)>0:
            self.view.clearSelection()
        else:
            self.home.emit()

    def enter(self):
        sel = self.view.selectionModel().selectedIndexes()
        cur = []
        for i in sel:
            if i.column()==0: cur.append(i)
        if len(cur)==0:
            os.startfile(self.mod.base.fpath())
            return
        if len(cur)==1:
            n = self.proxmod.data(i,257)
            if n.dir:
                self.npath.emit(n.fpath())
                return
            else:
                os.startfile(n.fpath())
                return
        if len(cur)>1:
            for i in cur:
                if i.column()==0:
                    os.startfile(self.proxmod.data(i,257).fpath())

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setPalette(self.palette())
        menu.addAction(self.noIndexAction)
        menu.addAction(self.noNameAction)
        menu.addAction(self.noPathAction)
        menu.exec(event.globalPos())

    def noIndexFunc(self, event):
        cur = self.view.selectedIndexes()
        for it in cur:
            if it.column()==0:
                n = self.proxmod.data(it,257)
                self.mod.core.ff.addNoIndex(n.fpath())
                self.set.set('ff',self.mod.core.ff)

    def noNameFunc(self, event):
        cur = self.view.selectedIndexes()
        for it in cur:
            if it.column()==0:
                n = self.proxmod.data(it,257)
                self.mod.core.ff.addName(n.name)
                self.set.set('ff',self.mod.core.ff)

    def noPathFunc(self, event):
        cur = self.view.selectedIndexes()
        for it in cur:
            if it.column()==0:
                n = self.proxmod.data(it,257)
                self.mod.core.ff.addPath(n.fpath())
                self.set.set('ff',self.mod.core.ff)


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

            self.core = runner()
            self.thing = treeviewer(self.core)
            layout.addWidget(self.thing)

            self.thing.setPath(os.path.expanduser("~"))




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
