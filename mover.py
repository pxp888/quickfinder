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
        job, detail = qin.get(True)
        if job==1:
            src, dest = detail
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
            src, dest = detail
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

        if job==3:
            src, curpath = detail
            zname = src[0]+'.zip'
            if len(src)==1:
                zname = src[0]+'.zip'
            else:
                # zname = os.path.split(src[0])[0] + '.zip' 
                zname = os.path.join(curpath, os.path.split(curpath)[1]) + '.zip'
            os.chdir(curpath)
            with zipfile.ZipFile(zname, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=4) as zipper:
                for i in src:
                    if os.path.isdir(i):
                        for root, dirs, files in os.walk(i, topdown=False):
                            for name in files:
                                zipper.write(os.path.relpath(os.path.join(root, name)))
                    else:
                        zipper.write(os.path.relpath(i))
            lock.acquire()
            jobs[0] -=1
            lock.release()

        if job==4:
            src = detail
            try:
                for s in src:
                    with zipfile.ZipFile(s, 'r') as zipper:
                        zipper.extractall(os.path.splitext(s)[0])
            except:
                print('unzip failed : ',s)                
            lock.acquire()
            jobs[0] -=1
            lock.release()

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
            self.qin.put((1,(src,dest)))

    def copy(self, src, dest):
        if not self.tim.isActive(): self.tim.start()
        self.lock.acquire()
        self.jobs[0] +=1
        self.lock.release()

        src = QDir.toNativeSeparators(src)
        src = src.strip(os.path.sep)
        self.qin.put((2,(src,dest)))
        # shutil.copy2(src, dest)

    def zipFunc(self, src, curpath):
        if not self.tim.isActive(): self.tim.start()
        self.lock.acquire()
        self.jobs[0] +=1
        self.lock.release()

        self.qin.put( (3,(src, curpath)) )

    def unzipFunc(self, src):
        if not self.tim.isActive(): self.tim.start()
        self.lock.acquire()
        self.jobs[0] +=1
        self.lock.release()

        self.qin.put( (4,(src)) )


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







