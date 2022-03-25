from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from queue import Queue
import threading

import os
import sys
import time
import shutil 

def copmove(qin):
	while 1:
		job, src, dest = qin.get(True)
		if job==1:
			print('move',src,dest)
			shutil.move(src, dest)
			print('finished', dest)
		if job==2:
			print('copy',src,dest)
			shutil.copy2(src, dest)
			print('finished', dest)

class mover(QObject):
	def __init__(self, parent=None):
		super(mover, self).__init__(parent)
		self.qin = Queue()
		self.tred = threading.Thread(target=copmove,args=(self.qin,),daemon=True)
		self.tred.start()

	def move(self, src, dest):
		if not dest=='':
			src = QDir.toNativeSeparators(src)
			src = src.strip(os.path.sep)
			self.qin.put((1,src,dest))

	def copy(self, src, dest):
		src = QDir.toNativeSeparators(src)
		src = src.strip(os.path.sep)
		self.qin.put((2,src,dest))
		# shutil.copy2(src, dest)


class renameClass(QDialog):
	def __init__(self, parent=None):
		super(renameClass, self).__init__(parent)
		self.setWindowTitle('Rename Files')
		layout = QGridLayout()
		self.setLayout(layout)
		
		self.srclist = QListWidget()
		self.destlist = QListWidget()
		self.line = QLineEdit()
		self.confirmbut = QPushButton('Rename Files')

		layout.addWidget(self.line,0,1)
		layout.addWidget(QLabel('From'),1,0)
		layout.addWidget(QLabel('To'),1,1)
		layout.addWidget(self.srclist,2,0)
		layout.addWidget(self.destlist,2,1)
		layout.addWidget(self.confirmbut,3,1)

		self.line.setText('* #')
		self.line.textChanged.connect(self.preview)
		
		self.confirmbut.setEnabled(False)
		self.confirmbut.clicked.connect(self.rename)

		self.ipaths = []
		self.opaths = []

	def populate(self, its):
		self.ipaths = its 
		self.srclist.clear()
		for i in its:
			self.srclist.addItem(os.path.split(i)[1])
		self.preview()

	def preview(self):
		t = self.line.text()
		self.destlist.clear()
		self.opaths = []
		
		ok = True

		n = 0
		for i in self.ipaths:
			base, name = os.path.split(i)
			if name=='':
				name = base 
				base = ''
			name, ext = os.path.splitext(name)
			nt = t 
			nt = nt.replace('*',name)
			nt = nt.replace('#',str(n))
			if nt=='': ok=False
			nt = nt + ext 
			np = os.path.join(base,nt)
			self.opaths.append(np)
			self.destlist.addItem(nt)
			n+=1

		test = {}
		for i in self.opaths: test[i]=1
		self.confirmbut.setEnabled(len(test)==len(self.opaths))
		if not ok: self.confirmbut.setEnabled(False)
		
	def rename(self):
		for i in range(len(self.ipaths)):
			shutil.move(self.ipaths[i], self.opaths[i])
		self.close()





