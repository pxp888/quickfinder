from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import pickle

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


######################################################################################################


class iconMaker():
    def __init__(self):
        self.foldermap = QPixmap(':/icons/folder.png')
        self.docmap = QPixmap(':/icons/doc.png')
        self.photomap = QPixmap(':/icons/photo.png')
        self.moviemap = QPixmap(':/icons/video.png')
        self.musicmap = QPixmap(':/icons/music.png')

        self.data = {}
        for i in ['jpg','png','webp','bmp','jpeg']: self.data[i]=self.photomap
        for i in ['mp4','avi','mpg','mpeg','mkv','mov','webm','flv']: self.data[i] = self.moviemap
        for i in ['mp3','flac','ogg','wav']: self.data[i] = self.musicmap
        # for i in ['xls','xlsx']: self.data[i] = self.sheetmap
        # for i in ['doc','docx']: self.data[i] = self.wordmap
        # for i in ['pdf']: self.data[i] = self.pdfmap

    def pic(self, name, dir):
        if dir: return self.foldermap

        f = name.split('.')[-1].lower()
        if f in self.data: return self.data[f]

        return self.docmap

    def icon(self, name, dir):
        return QIcon(self.pic(name,dir))


######################################################################################################


class setter():
    def __init__(self, name=None):
        path = os.path.join(os.path.expanduser("~"),'quickfinder')
        if not os.path.exists(path): os.mkdir(path)
        self.path = path 

    def set(self, key, val):
        kpath = os.path.join(self.path, key)
        with open(kpath, 'wb') as foo:
            pickle.dump(val, foo)

    def get(self, key, default=None):
        kpath = os.path.join(self.path, key)
        try:
            with open(kpath, 'rb') as foo:
                val = pickle.load(foo)
            return val 
        except:
            return default


######################################################################################################


class listthing(QWidget):
    save = pyqtSignal()
    def __init__(self, title='List Here', parent=None,):
        super(listthing, self).__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)
        # layout.setContentsMargins(0, 0, 0, 0)
        # layout.setSpacing(0)
        self.label = QLabel(title)
        self.label.setFont(QFont("Arial",12))
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
        if isinstance(self.data, dict):
            self.data[t]=None
        else:
            self.data.append(t)
        self.update()
        self.save.emit()

    def removepath(self, it):
        if isinstance(self.data, dict):
            del self.data[it.text()]
        else:
            self.data.remove(it.text())
        self.update()
        self.save.emit()


class vchecker(QThread):
    version = pyqtSignal(object)
    def run(self):
        import urllib.request
        try:
            url = 'https://pxp-globals.s3.ap-southeast-1.amazonaws.com/quickfinderversion.txt'
            v = urllib.request.urlopen(url).read().decode('utf-8')
            if v[-1]=='\n': v = v[:-1]
            self.version.emit(v)
        except:
            print('version check failed')
            return

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
        self.setFont(QFont("Arial",11))

        self.core = core

        self.leftlist = listthing(title='Exclude Names Starting with')
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
        explain1.setFont(QFont("Arial",11))

        self.helper = QLabel()
        self.sethelper()

        self.sitebut = QPushButton('www.quickfinder.info')
        self.sitebut.clicked.connect(self.opensite)

        self.updatebut = QPushButton('Check for Updates')
        self.updatebut.clicked.connect(self.versioncheck)

        layout.addWidget(self.leftlist,1,1)
        layout.addWidget(self.namelist,1,2)
        layout.addWidget(self.pathlist,1,3)
        layout.addWidget(self.indexlist,1,4)
        layout.addWidget(explain1,2,0)
        layout.addWidget(self.sitebut,3,0)
        layout.addWidget(self.updatebut,4,0)
        layout.addWidget(self.helper,5,3,1,2)
        # layout.addWidget(self.dark,2,3)

        self.leftlist.data = self.core.ff.left
        self.namelist.data = self.core.ff.names
        self.pathlist.data = self.core.ff.paths
        self.indexlist.data = self.core.ff.noIndex
        self.leftlist.update()
        self.namelist.update()
        self.pathlist.update()
        self.indexlist.update()
        
        self.homelist = listthing(title='Index paths')
        self.homelist.save.connect(self.savehomes)
        self.homelist.data = self.core.homepaths
        layout.addWidget(self.homelist,1,0)
        self.homelist.update()

        darkPalette = QPalette()
        darkPalette.setColor(QPalette.Base, QColor(40, 42, 54));
        darkPalette.setColor(QPalette.Text, QColor(200, 200, 200));
        self.leftlist.setPalette(darkPalette)
        self.namelist.setPalette(darkPalette)
        self.pathlist.setPalette(darkPalette)
        self.homelist.setPalette(darkPalette)
        self.indexlist.setPalette(darkPalette)

    def versioncheck(self):
        self.upper = vchecker(self)
        self.upper.version.connect(self.version)
        self.upper.finished.connect(self.upper.deleteLater)
        self.upper.start()

    def version(self, v):
        if not v=='1.4.7':
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
        else:
            msg = QMessageBox()
            msg.setFont(QFont("Arial",14))
            msg.setIcon(QMessageBox.Information)
            msg.setText(v + ' is the current version')
            # msg.setInformativeText('Download at www.quickfinder.info')
            msg.setWindowTitle('Quickfinder is current')
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setEscapeButton(QMessageBox.Ok)
            retval = msg.exec_()

    def opensite(self):
        import webbrowser
        webbrowser.open('www.quickfinder.info',autoraise=True)

    def sethelper(self):
        fin = QFile(':/icons/helptext.md')
        fin.open(QIODevice.ReadOnly | QIODevice.Text)
        a = fin.read(10000).decode('utf-8')
        self.helper.setText(a)
        # self.helper.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)

    def save(self):
        self.set = setter('quickfinder1')
        self.set.set('ff',self.core.ff)

    def savehomes(self):
        self.set = setter('quickfinder1')
        self.set.set('homepaths',self.core.homepaths)