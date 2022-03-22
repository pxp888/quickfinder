from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import os
import sys
import time

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
		self.pic = None
		self.sel = False
		self.frame = False
		self.w = int(width)
		self.h = int(width*.75)

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

		if self.hlite:
			pen = QPen(Qt.gray,1)
			painter.setPen(pen)
			outrect = self.boundingRect()
			painter.drawRect(outrect)


		pen = QPen(Qt.white,1)
		painter.setPen(pen)
		painter.setFont(QFont("Arial",8))
		trect = self.boundingRect().adjusted(5,self.h-40,-5,-2)
		painter.drawText(trect,Qt.TextWordWrap | Qt.AlignHCenter ,self.path)

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


class homebutton(QPushButton):
	npath = pyqtSignal(object)
	def __init__(self, parent=None):
		super(homebutton,self).__init__(parent)
		self.clicked.connect(self.thing)

	def thing(self):
		self.npath.emit(self.text())


class homeClass(QWidget):
	npath = pyqtSignal(object)
	def __init__(self, core, parent=None):
		super(homeClass, self).__init__(parent)
		layout = QVBoxLayout()
		self.setLayout(layout)
		# layout.setContentsMargins(0, 0, 0, 0)
		# layout.setSpacing(0)
		self.setFont(QFont("Arial",13))
		self.layout = layout

		self.core = core
		self.set = setter.setter('quickfinder1')

		self.homepaths = self.core.homepaths
		
		self.its = []
		self.drv = []

		self.zen1 = QGraphicsScene()
		self.zen2 = QGraphicsScene()
		self.view1 = QGraphicsView()
		self.view2 = QGraphicsView()
		self.view1.setScene(self.zen1)
		self.view2.setScene(self.zen2)
		self.view1.setAlignment(Qt.AlignTop | Qt.AlignLeft)
		self.view2.setAlignment(Qt.AlignTop | Qt.AlignLeft)


		layout.addWidget(QLabel('Indexed Paths'))
		layout.addWidget(self.view1)
		layout.addWidget(QLabel('Drives'))
		layout.addWidget(self.view2)

		self.view1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

		# self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
		# verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
		# self.layout.addItem(verticalSpacer)

		self.setup()

	def setup(self, path=''):
		self.core.sniffer = node.node()
		for i in self.homepaths: self.core.addSnifPath(i)
		self.core.n = self.core.sniffer
		self.core.scan(rec=7)

		for i in self.its: self.zen1.removeItem(i)
		self.its = []


		for i in self.homepaths:
			it = fileitem(i)
			it.setpic(QPixmap(':/icons/folder.png'),True)
			self.zen1.addItem(it)
			self.its.append(it)

		if len(self.drv)==0:
			drvlet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
			for i in drvlet:
				path = str(i)+':'+os.path.sep 
				if os.path.exists(path):
					it = fileitem(path)
					it.setpic(QPixmap(':/icons/drive.png'),True)
					self.zen2.addItem(it)
					self.drv.append(it)

		self.reflow()

	def reflow(self):
		cols = max((self.width() / 200)-1 ,1)
		n = 0 
		for i in self.its:
			col = int(n/cols)*150
			row = int(n%cols)*200
			i.setPos(row,col)
			n+=1

		n = 0 
		for i in self.drv:
			col = int(n/cols)*150
			row = int(n%cols)*200
			i.setPos(row,col)
			n+=1

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
