from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from queue import SimpleQueue
import threading

import os
import sys
import time
import shutil 
import zipfile 

############################################################################################################




def copmove(qin, lock, jobs):
	while 1:
		job, src, dest = qin.get(True)
		if job==1:
			try:
				if os.path.isdir(src):
					target = os.path.join(dest, os.path.split(src)[1])
					while os.path.exists(target):
						target = target + ' Copy'
					shutil.move(src, target)
				else:
					target = os.path.join(dest, os.path.split(src)[1])
					while os.path.exists(target):
						base, ext = os.path.splitext(target) 
						base = base + ' Copy'
						target = base + ext 
					shutil.move(src, target)
				lock.acquire()
				jobs[0] -=1
				lock.release()
			except:
				print('move error : ', src, dest)
				continue

		if job==2:
			try:
				if os.path.isdir(src):
					target = os.path.join(dest, os.path.split(src)[1])
					while os.path.exists(target):
						target = target + ' Copy'
					shutil.copytree(src, target)
				else:
					target = os.path.join(dest, os.path.split(src)[1])
					while os.path.exists(target):
						base, ext = os.path.splitext(target) 
						base = base + ' Copy'
						target = base + ext 
					shutil.copy2(src, target)
				lock.acquire()
				jobs[0] -=1
				lock.release()
			except:
				print('copy error : ', src, dest)


class mover(QObject):
	fileops = pyqtSignal(object)
	def __init__(self, parent=None):
		super(mover, self).__init__(parent)
		self.qin = SimpleQueue()
		self.lock = threading.Lock()
		self.jobs = []
		self.jobs.append(0)

		self.tred = threading.Thread(target=copmove,args=(self.qin, self.lock, self.jobs),daemon=True)
		self.tred.start()

		self.tim = QTimer()
		self.tim.setInterval(500)
		self.tim.timeout.connect(self.report)

	def report(self):
		self.lock.acquire()
		j = self.jobs[0]
		self.lock.release()
		self.fileops.emit(j)
		if j==0: self.tim.stop()

	def move(self, src, dest):
		if not self.tim.isActive(): self.tim.start()
		if not dest=='':
			self.lock.acquire()
			self.jobs[0] +=1
			self.lock.release()

			src = QDir.toNativeSeparators(src)
			src = src.strip(os.path.sep)
			self.qin.put((1,src,dest))

	def copy(self, src, dest):
		if not self.tim.isActive(): self.tim.start()
		self.lock.acquire()
		self.jobs[0] +=1
		self.lock.release()

		src = QDir.toNativeSeparators(src)
		src = src.strip(os.path.sep)
		self.qin.put((2,src,dest))
		# shutil.copy2(src, dest)






############################################################################################################




# def copmove(qin):
# 	while 1:
# 		job, src, dest = qin.get(True)
# 		if job==1:
# 			if os.path.isdir(src):
# 				target = os.path.join(dest, os.path.split(src)[1])
# 				while os.path.exists(target):
# 					target = target + ' Copy'
# 				shutil.move(src, target)
# 			else:
# 				target = os.path.join(dest, os.path.split(src)[1])
# 				while os.path.exists(target):
# 					base, ext = os.path.splitext(target) 
# 					base = base + ' Copy'
# 					target = base + ext 
# 				shutil.move(src, target)
# 		if job==2:
# 			if os.path.isdir(src):
# 				target = os.path.join(dest, os.path.split(src)[1])
# 				while os.path.exists(target):
# 					target = target + ' Copy'
# 				shutil.copytree(src, target)
# 			else:
# 				target = os.path.join(dest, os.path.split(src)[1])
# 				while os.path.exists(target):
# 					base, ext = os.path.splitext(target) 
# 					base = base + ' Copy'
# 					target = base + ext 
# 				shutil.copy2(src, target)


# class mover(QObject):
# 	def __init__(self, parent=None):
# 		super(mover, self).__init__(parent)
# 		self.qin = SimpleQueue()
# 		self.tred = threading.Thread(target=copmove,args=(self.qin,),daemon=True)
# 		self.tred.start()

# 	def move(self, src, dest):
# 		if not dest=='':
# 			src = QDir.toNativeSeparators(src)
# 			src = src.strip(os.path.sep)
# 			self.qin.put((1,src,dest))

# 	def copy(self, src, dest):
# 		src = QDir.toNativeSeparators(src)
# 		src = src.strip(os.path.sep)
# 		self.qin.put((2,src,dest))
# 		# shutil.copy2(src, dest)





############################################################################################################





# def tmove(src, dest, lock, jobs):
# 	src = QDir.toNativeSeparators(src)
# 	src = src.strip(os.path.sep)
# 	if os.path.isdir(src):
# 		target = os.path.join(dest, os.path.split(src)[1])
# 		while os.path.exists(target):
# 			target = target + ' Copy'
# 		shutil.move(src, target)
# 	else:
# 		target = os.path.join(dest, os.path.split(src)[1])
# 		while os.path.exists(target):
# 			base, ext = os.path.splitext(target) 
# 			base = base + ' Copy'
# 			target = base + ext 
# 		shutil.move(src, target)
# 	lock.acquire()
# 	jobs[0] -=1
# 	lock.release()

# def tcopy(src, dest, lock, jobs):
# 	src = QDir.toNativeSeparators(src)
# 	src = src.strip(os.path.sep)
# 	if os.path.isdir(src):
# 		target = os.path.join(dest, os.path.split(src)[1])
# 		while os.path.exists(target):
# 			target = target + ' Copy'
# 		shutil.copytree(src, target)
# 	else:
# 		target = os.path.join(dest, os.path.split(src)[1])
# 		while os.path.exists(target):
# 			base, ext = os.path.splitext(target) 
# 			base = base + ' Copy'
# 			target = base + ext 
# 		shutil.copy2(src, target)
# 	lock.acquire()
# 	jobs[0] -=1
# 	lock.release()

# class mover(QObject):
# 	def __init__(self, parent=None):
# 		super(mover, self).__init__(parent)
# 		self.pros = []
# 		self.lock = threading.Lock()
# 		self.jobs = []
# 		self.jobs.append(0)

# 		self.tim = QTimer()
# 		self.tim.setInterval(500)
# 		self.tim.timeout.connect(self.report)
# 		self.tim.start()

# 	def report(self):
# 		self.cleanup()

# 		self.lock.acquire()
# 		j = self.jobs[0]
# 		self.lock.release()
# 		print(j, len(self.pros), self)

# 	def cleanup(self):
# 		kill = []
# 		for i in self.pros:
# 			if not i.is_alive():
# 				kill.append(i)
# 		for i in kill:
# 			self.pros.remove(i)

# 	def move(self, src, dest):
# 		if dest=='': return 
# 		self.lock.acquire()
# 		self.jobs[0] +=1
# 		self.lock.release()

# 		t = threading.Thread(target=tmove, args=(src, dest, self.lock, self.jobs), daemon=True)
# 		self.pros.append(t)
# 		t.start()
# 		# self.cleanup()

# 	def copy(self, src, dest):
# 		if dest=='': return 
# 		self.lock.acquire()
# 		self.jobs[0] +=1
# 		self.lock.release()

# 		t = threading.Thread(target=tcopy, args=(src, dest, self.lock, self.jobs), daemon=True)
# 		self.pros.append(t)
# 		t.start()
# 		# self.cleanup()






############################################################################################################





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

		layout.addWidget(self.line,2,1)
		layout.addWidget(QLabel('From'),3,0)
		layout.addWidget(QLabel('To'),3,1)
		layout.addWidget(self.srclist,4,0)
		layout.addWidget(self.destlist,4,1)
		layout.addWidget(self.confirmbut,5,1)

		layout.addWidget(QLabel('# - insert sequence number'),0,1)
		layout.addWidget(QLabel('* - original filename'),1,1)

		self.line.setText('* #')
		self.line.textChanged.connect(self.preview)
		
		self.confirmbut.setEnabled(False)
		self.confirmbut.clicked.connect(self.rename)

		self.ipaths = []
		self.opaths = []

	def populate(self, its):
		self.ipaths = its 
		self.srclist.clear()
		for i in its: self.srclist.addItem(os.path.split(i)[1])
		if len(self.ipaths)==1: self.line.setText(os.path.splitext( os.path.split( self.ipaths[0] )[1] )[0] )
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







