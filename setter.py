from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import pickle
from appdata import AppDataPaths

import resources
from node import *

darkPalette = QPalette()
darkPalette.setColor(QPalette.Window, QColor(32, 32, 32));
darkPalette.setColor(QPalette.WindowText, Qt.white);
darkPalette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(127, 127, 127));
darkPalette.setColor(QPalette.Base, QColor(25, 25, 25));
darkPalette.setColor(QPalette.AlternateBase, QColor(66, 66, 66));
darkPalette.setColor(QPalette.ToolTipBase, Qt.white);
darkPalette.setColor(QPalette.ToolTipText, QColor(32, 32, 32));
darkPalette.setColor(QPalette.Text, Qt.white);
darkPalette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127));
darkPalette.setColor(QPalette.Dark, QColor(35, 35, 35));
darkPalette.setColor(QPalette.Shadow, QColor(20, 20, 20));
darkPalette.setColor(QPalette.Button, QColor(32, 32, 32));
darkPalette.setColor(QPalette.ButtonText, Qt.white);
darkPalette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127));
darkPalette.setColor(QPalette.BrightText, Qt.red);
darkPalette.setColor(QPalette.Link, QColor(42, 130, 218));
# darkPalette.setColor(QPalette.Highlight, QColor(42, 130, 218));
# darkPalette.setColor(QPalette.Active, QPalette.Highlight, QColor(50, 65, 84));
darkPalette.setColor(QPalette.Active, QPalette.Highlight, QColor(42, 130, 130));
darkPalette.setColor(QPalette.Inactive, QPalette.Highlight, QColor(80, 170, 160));
darkPalette.setColor(QPalette.Disabled, QPalette.Highlight, QColor(80, 80, 80));
darkPalette.setColor(QPalette.HighlightedText, Qt.white);
darkPalette.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor(127, 127, 127));



class iconMaker():
    def __init__(self):
        self.foldermap = QPixmap(':/icons/folder.png')
        self.docmap = QPixmap(':/icons/icon.ico')
        self.photomap = QPixmap(':/icons/photo.png')
        self.moviemap = QPixmap(':/icons/movie.png')
        self.musicmap = QPixmap(':/icons/music.png')
        self.wordmap = QPixmap(':/icons/word.png')
        self.sheetmap = QPixmap(':/icons/sheet.png')
        self.pdfmap = QPixmap(':/icons/pdf.png')

        self.data = {}
        for i in ['jpg','png','webp','bmp','jpeg']: self.data[i]=self.photomap
        for i in ['mp4','avi','mpg','mpeg','mkv','mov','webm','flv']: self.data[i] = self.moviemap
        for i in ['mp3','flac','ogg']: self.data[i] = self.musicmap
        for i in ['xls','xlsx']: self.data[i] = self.sheetmap
        for i in ['doc','docx']: self.data[i] = self.wordmap
        for i in ['pdf']: self.data[i] = self.pdfmap

    def pic(self, name, dir):
        if dir: return self.foldermap

        f = name.split('.')[-1].lower()
        if f in self.data: return self.data[f]

        return self.docmap

    def icon(self, name, dir):
        return QIcon(self.pic(name,dir))




class setter():
    def __init__(self, name):
        self.paths = AppDataPaths(name)
        self.paths.setup()
        try:
            with open(self.paths.config_path, 'rb') as fin:
                self.data = pickle.load(fin)
        except:
            self.data = {}

    def get(self, key, default=None):
        if key in self.data:
            return self.data[key]
        else:
            return default

    def set(self, key, val):
        self.data[key] = val
        with open(self.paths.config_path, 'wb') as foo:
            pickle.dump(self.data, foo)



class listthing(QWidget):
    save = pyqtSignal()
    def __init__(self, title='List Here', parent=None,):
        super(listthing, self).__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)
        # layout.setContentsMargins(0, 0, 0, 0)
        # layout.setSpacing(0)
        self.label = QLabel(title)
        self.label.setFont(QFont("Arial",14))
        self.list = QListWidget()
        self.line = QLineEdit()
        self.data = {}

        layout.addWidget(self.label)
        layout.addWidget(self.list)
        layout.addWidget(self.line)
        self.line.setPlaceholderText('New Entry')

        self.line.returnPressed.connect(self.newentry)
        self.list.itemDoubleClicked.connect(self.removepath)

    def update(self):
        self.list.clear()
        for i in self.data:
            self.list.addItem(i)

    def newentry(self):
        t = self.line.text()
        if len(t)==0: return
        self.line.clear()
        self.data[t]=None
        self.update()
        self.save.emit()

    def removepath(self, it):
        del self.data[it.text()]
        self.update()
        self.save.emit()


class setwin(QDialog):
    color = pyqtSignal()
    def __init__(self, core=None, parent=None):
        super(setwin, self).__init__(parent)
        self.setWindowTitle('Settings')
        # frame = QFrame()
        # self.setCentralWidget(frame)
        layout = QGridLayout()
        self.setLayout(layout)
        # layout.setContentsMargins(0, 0, 0, 0)
        # layout.setSpacing(0)
        # self.resize(1200,900)

        self.core = core

        self.leftlist = listthing(title='Name starts with')
        self.namelist = listthing(title='Excluded Names')
        self.pathlist = listthing(title='Excluded Paths')
        self.indexlist = listthing(title='No Index Paths')

        self.leftlist.save.connect(self.save)
        self.namelist.save.connect(self.save)
        self.pathlist.save.connect(self.save)
        self.indexlist.save.connect(self.save)

        self.dark = QPushButton('Change Theme')
        self.dark.setFont(QFont("Arial",14))
        self.dark.clicked.connect(self.color)
        self.dark.setFocusPolicy(Qt.NoFocus)

        explain1 = QLabel('Double click list items to remove.')
        explain1.setFont(QFont("Arial",13))

        layout.addWidget(self.leftlist,1,0)
        layout.addWidget(self.namelist,1,1)
        layout.addWidget(self.pathlist,1,2)
        layout.addWidget(self.indexlist,1,3)
        layout.addWidget(explain1,0,0)
        layout.addWidget(self.dark,2,3)

        self.leftlist.data = self.core.ff.left
        self.namelist.data = self.core.ff.names
        self.pathlist.data = self.core.ff.paths
        self.indexlist.data = self.core.ff.noIndex
        self.leftlist.update()
        self.namelist.update()
        self.pathlist.update()
        self.indexlist.update()

    def save(self):
        self.set = setter('quickfinder1')
        self.set.set('ff',self.core.ff)
