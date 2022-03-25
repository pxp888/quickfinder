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


class TreeModel(QAbstractItemModel):
    preview = pyqtSignal(object)
    nmove = pyqtSignal(object, object)
    def __init__(self, core, parent=None):
        super(TreeModel, self).__init__(parent)

        self.icon = setter.iconMaker()
        self.icmaker = QFileIconProvider()
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
                # return QVariant(self.icon.icon(item.name, item.dir))
                return QVariant(self.icmaker.icon(QFileInfo(index.internalPointer().fpath())))
            return None
        if role == Qt.TextAlignmentRole:
            if index.column()==1:
                return Qt.AlignRight
            return Qt.AlignLeft
        if role == Qt.SizeHintRole and index.column()==0: return QSize(200,20)
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
        return parentItem.childCount()
        # if parentItem.model==True:
        #     return len(parentItem.kids)
        # else:
        #     return 0

    def dropMimeData(self, data, action, row, column, parent):
        dest = parent.internalPointer().fpath()
        if data.hasUrls():
            for i in data.urls():
                self.nmove.emit(i.path(), dest)
        return True

    def supportedDropActions(self):
        return Qt.CopyAction | Qt.MoveAction 

    def mimeTypes(self):
        return ['text/plain','text/uri-list']

    def mimeData(self, indexes):
        urls = []
        for i in indexes:
            if i.column()==0:
                path = i.internalPointer().fpath()
                urls.append(QUrl().fromLocalFile(path))
        mimedata = QMimeData()
        mimedata.setUrls(urls)
        return mimedata


######################################################################################################################################################


class tview(QTreeView):
    back = pyqtSignal()
    def mousePressEvent(self, event):
        if event.button()==8:
            self.back.emit()
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
        self.set = setter.setter('quickfinder1')

        self.core = core
        self.reset = False

        self.mod = TreeModel(core)
        self.mod.nmove.connect(self.nmove)

        self.view = tview()
        self.view.back.connect(self.back)

        self.ctrlkey = False

        self.view.setModel(self.mod)
        self.view.setSortingEnabled(True)
        self.view.setSelectionMode(3)
        self.view.header().setStretchLastSection(False)
        self.view.header().setSectionResizeMode(0,1)
        self.view.header().setSectionResizeMode(1,3)
        self.view.header().setSectionResizeMode(2,3)
        self.view.setVerticalScrollMode(1)
        
        self.layout.addWidget(self.view)

        self.view.selectionModel().currentChanged.connect(self.selupdate)
        self.view.header().sortIndicatorChanged.connect(self.sortclicked)

        self.copyAction = QAction("Copy",self)
        self.pasteAction = QAction("Paste",self)
        self.noIndexAction = QAction("No Index",self)
        self.noNameAction = QAction("Ignore Name",self)
        self.noPathAction = QAction("Ignore Path",self)
        self.addHomePathAction = QAction("Add Index Path",self)

        self.copyAction.triggered.connect(self.copyToClip)
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

    def cleanup(self):
        pass

    def setPath(self, path):
        self.mod.beginResetModel()
        self.mod.base = self.mod.core.locate(path)
        self.mod.endResetModel()

    def refresh1(self):
        self.reset = False
        for i in self.view.selectedIndexes():
            path = self.mod.data(i,257).fpath()
            if not os.path.exists(path):
                self.reset = True 
        if self.reset:
            self.view.clearSelection()
            self.mod.beginResetModel()
        else:
            self.mod.layoutAboutToBeChanged.emit()

    def refresh2(self):
        if self.reset:
            self.mod.endResetModel()
            self.reset = False
        else:
            self.mod.layoutChanged.emit()

    def selectedPaths(self):
        cur = self.view.selectedIndexes()
        out = []
        for i in cur:
            if i.column()==0:
                n = self.mod.data(i,257)
                out.append(n.fpath())
        return out 

    def selupdate(self, a, b):
        out = self.selectedPaths()
        self.preview.emit(out)
        if len(out)>0:
            self.hopPath.emit(out[-1])

    def sortclicked(self, i, order):
        self.mod.layoutAboutToBeChanged.emit()
        self.core.n.sort(i,order)
        self.mod.layoutChanged.emit()

    def keyPressEvent(self, event):
        x = event.key()
        # print('tv',x)
        if self.ctrlkey:
            if x==67: self.copyToClip()
        if x==16777249: self.ctrlkey=True 
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
        if x==16777223:  # DELETE
            self.deleteFiles()
            return
        if x==16777219:  # backspace
            self.back()
            return
        if x==16777265: self.rename()
        super(treeviewer, self).keyPressEvent(event)

    def keyReleaseEvent(self, event):
        x = event.key()
        if x==16777249: self.ctrlkey=False
        super(treeviewer,self).keyReleaseEvent(event)

    def entered(self):
        cur = self.view.selectedIndexes()
        out = []
        for i in cur:
            if i.column()==0:
                n = self.mod.data(i,257)
                out.append(n)
                print(n.fpath())
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

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setPalette(self.palette())
        menu.addAction(self.copyAction)
        menu.addAction(self.addHomePathAction)
        menu.addAction(self.noIndexAction)
        menu.addAction(self.noNameAction)
        menu.addAction(self.noPathAction)
        menu.exec(event.globalPos())

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
        
    def back(self):
        path = self.core.back()
        self.npath.emit(path)

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
                if os.path.isdir(i):
                    for root, dirs, files in os.walk(i, topdown=False):
                        for name in files:
                            os.remove(os.path.join(root, name))
                        for name in dirs:
                            os.rmdir(os.path.join(root, name))
                    os.rmdir(i)
                else:
                    os.remove(i)
            
    def rename(self):
        cur = self.selectedPaths()
        self.namer = mover.renameClass()
        self.namer.populate(cur)
        self.namer.show()

    def copyToClip(self):
        cur = self.selectedPaths()
        if not cur: return 
        urls = []
        for i in cur: urls.append(QUrl().fromLocalFile(i))
        mimedata = QMimeData()
        mimedata.setUrls(urls)
        QGuiApplication.clipboard().setMimeData(mimedata)


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
