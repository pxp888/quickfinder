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