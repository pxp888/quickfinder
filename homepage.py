from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import os
import sys
import time
import shutil 

import multiprocessing as mp
from queue import Queue
import threading
import resources
from PIL import Image, ImageOps
from appdata import AppDataPaths

import node
import setter

class fileitem(QGraphicsItem):
	doublenpath = pyqtSignal(object)
	def __init__(self, path='', width=200, parent=None):
		super(fileitem, self).__init__(parent)
		self.path = path
		self.dpath = path 
		self.pic = None
		self.sel = False
		self.frame = False
		self.w = int(width)
		self.h = int(width*.75)
		self.total = 0 
		self.used = 0

		self.setAcceptHoverEvents(True)
		self.hlite = False

	def boundingRect(self):
		return QRectF(0,0,self.w, self.h)

	def paint(self, painter, option, widget):
		if self.sel:
			pen = QPen(QColor(42, 130, 130),1)
			painter.setPen(pen)
			outrect = self.boundingRect().adjusted(1,1,-1,-1)
			path = QPainterPath()
			path.addRect(outrect)
			painter.fillPath(path,QColor(42, 130, 130))
			painter.drawRect(outrect)
		else:
			if self.frame:
				pen = QPen(Qt.black,0)
				painter.setPen(pen)
				outrect = self.boundingRect().adjusted(1,1,-1,-1)
				path = QPainterPath()
				path.addRect(outrect)
				painter.fillPath(path,QColor(50,50,50))
				painter.drawRect(outrect)

		if self.used > 0:
			pen = QPen(QColor(50,50,50),1)
			painter.setPen(pen)
			outrect = self.boundingRect().adjusted(2,self.h-(self.used/self.total)*self.h,-2,1)
			path = QPainterPath()
			path.addRect(outrect)	
			painter.fillPath(path,QColor(50,50,50))
			painter.drawRect(outrect)

		pen = QPen(Qt.white,1)
		painter.setPen(pen)
		painter.setFont(QFont("Arial",8))
		trect = self.boundingRect().adjusted(5,self.h-40,-5,-2)
		painter.drawText(trect,Qt.TextWordWrap | Qt.AlignHCenter ,self.dpath)

		if self.used > 0:
			pen = QPen(Qt.white,1)
			painter.setPen(pen)
			painter.setFont(QFont("Arial",8))
			trect = self.boundingRect().adjusted(5,self.h-20,-5,-2)
			stext = str(self.used//2**30) + ' GB  / ' + str(self.total//2**30)+' GB'
			painter.drawText(trect,Qt.TextWordWrap | Qt.AlignHCenter ,stext)

		if not self.pic==None:
			s = self.pic.size()
			s.scale(self.w-20, self.h-50, Qt.KeepAspectRatio)
			painter.drawPixmap( int((self.w-s.width())/2) , 10 ,  s.width(), s.height(), self.pic)

	def setpic(self, pic, frame=False):
		self.pic = pic
		self.frame = frame
		self.update()

	def toggle(self):
		if self.sel==True:
			self.sel = False
		else:
			self.sel = True
		self.update()

	def hoverEnterEvent(self, event):
		self.hlite=True
		self.update()

	def hoverLeaveEvent(self, event):
		self.hlite=False
		self.update()


######################################################################################################################################################


class mscene(QGraphicsScene):
	npath=pyqtSignal(object)
	kevin = pyqtSignal(object)
	def __init__(self, parent=None):
		super(mscene, self).__init__(parent)

		self.noIndexAction = QAction("No Index",self)
		self.noNameAction = QAction("Ignore Name",self)
		self.noPathAction = QAction("Ignore Path",self)
		self.addHomePathAction = QAction("Add Home Path",self)


	def mousePressEvent(self, event):
		if event.button()==1:
			it = self.itemAt(event.scenePos(),QTransform())
			if not it==None:
				self.npath.emit(it.path)
		
		super(mscene, self).mousePressEvent(event)


	def keyPressEvent(self, event):
		x=event.key()
		if x < 93: self.kevin.emit(event)
		super(mscene, self).keyPressEvent(event)


def drivecheck(qoo):
	drvlet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
	for i in drvlet:
		path = str(i)+':'+os.path.sep 
		if os.path.exists(path):
			it = fileitem(path)
			total, used, free = shutil.disk_usage(path)
			entry = (path, total, used)
			qoo.put(entry)
	qoo.put((0,0,0))

class homeClass(QWidget):
	npath = pyqtSignal(object)
	kevin = pyqtSignal(object)
	def __init__(self, core, parent=None):
		super(homeClass, self).__init__(parent)
		layout = QVBoxLayout()
		self.setLayout(layout)
		# layout.setContentsMargins(0, 0, 0, 0)
		# layout.setSpacing(0)
		# self.setFont(QFont("Arial",11))
		self.layout = layout

		self.icmaker = QFileIconProvider()
		self.core = core
		self.set = setter.setter('quickfinder1')

		self.homepaths = self.core.homepaths	

		self.its = []
		self.drv = []

		self.zen1 = mscene()
		self.zen2 = mscene()
		self.view1 = QGraphicsView()
		self.view2 = QGraphicsView()
		self.view1.setScene(self.zen1)
		self.view2.setScene(self.zen2)
		self.view1.setAlignment(Qt.AlignTop | Qt.AlignLeft)
		self.view2.setAlignment(Qt.AlignTop | Qt.AlignLeft)
		self.view1.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.view2.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.view1.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.view2.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

		layout.addWidget(QLabel(''))
		layout.addWidget(QLabel('Index Paths'))
		layout.addWidget(self.view1)
		layout.addWidget(QLabel('Drives'))
		layout.addWidget(self.view2)

		self.view1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
		self.view2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
		self.view1.setMinimumHeight(180)
		self.view2.setMinimumHeight(180)

		self.zen1.npath.connect(self.npath)
		self.zen2.npath.connect(self.npath)
		self.zen1.kevin.connect(self.kevin)

		# self.driveset()
		self.setup()
		self.setFocusPolicy(Qt.NoFocus)

		self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
		verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
		self.layout.addItem(verticalSpacer)

		self.qoo = Queue()
		self.dthread = threading.Thread(target=drivecheck, args=(self.qoo,),daemon=True)
		self.dthread.start()
		self.dim = QTimer()
		self.dim.setInterval(100)
		self.dim.timeout.connect(self.drivecheck)
		self.dim.start()

	def drivecheck(self):
		while 1:
			try:
				path, total, used = self.qoo.get(False)
				if path==0: 
					self.dim.stop()
					return
			except:
				return
			it = fileitem(path)
			it.total = total 
			it.used = used 
			it.setpic(self.icmaker.icon(QFileInfo(path)).pixmap(256,256))
			self.zen2.addItem(it)
			self.drv.append(it)
			it.setPos(len(self.drv)*200,0)
			it.update()

		# self.reflow()

	def setup(self, path=''):
		self.core.sniffer = node.node()
		for i in self.homepaths: self.core.addSnifPath(i)
		self.core.n = self.core.sniffer
		self.core.scan(rec=7)

		for i in self.its: self.zen1.removeItem(i)
		self.its = []

		for i in self.homepaths:
			it = fileitem(i)
			base, name = os.path.split(i)
			if name=='': 
				it.dpath=base
			else:
				it.dpath=name 

			it.setpic(self.icmaker.icon(QFileInfo(i)).pixmap(256,256))
			self.zen1.addItem(it)
			self.its.append(it)

		self.reflow()

	def driveset(self):   # NOT USED
		if len(self.drv)==0:
			drvlet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
			for i in drvlet:
				path = str(i)+':'+os.path.sep 
				if os.path.exists(path):
					it = fileitem(path)
					it.total, it.used, free = shutil.disk_usage(path)
					it.setpic(self.icmaker.icon(QFileInfo(path)).pixmap(256,256))
					self.zen2.addItem(it)
					self.drv.append(it)

	def reflow(self):
		cols = max((self.width() / 200)-1 ,1)
		n = 0 
		for i in self.its:
			# col = int(n/cols)*150
			# row = int(n%cols)*200
			col = 0
			row = 200*n 
			i.setPos(row,col)
			n+=1

		n = 0 
		for i in self.drv:
			# col = int(n/cols)*150
			# row = int(n%cols)*200
			col = 0
			row = 200*n 
			i.setPos(row,col)
			i.update()
			n+=1
		self.zen2.setSceneRect(self.zen2.itemsBoundingRect())

	def resizeEvent(self, event):
		self.reflow()
		super(homeClass,self).resizeEvent(event)


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
			self.resize(1600,1200)

			self.core = node.coreClass()
			self.home = homeClass(self.core)


	app = QApplication(sys.argv)
	# app.setStyle(QStyleFactory.create("Plastique"))
	app.setStyle(QStyleFactory.create("Fusion"))

	form = mainwin()
	form.show()
	# form.showFullScreen()
	# form.showMaximized()
	form.raise_()
	app.exec_()
