from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import os
import sys
import time
import shutil 


class mover(QObject):
	def __init__(self, parent=None):
		super(mover, self).__init__(parent)

	def move(self, src, dest):
		src = QDir.toNativeSeparators(src)
		src = src.strip(os.path.sep)
		print('move',src,dest)
		shutil.move(src, dest)


	def copy(self, src, dest):
		print('copy',src,dest)
