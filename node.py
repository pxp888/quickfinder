import os
import sys
import time
from queue import Queue
import threading
import pickle
import shutil
from PIL import Image, ImageOps
import hashlib
import base64

from fuzzywuzzy import fuzz
import setter
import btree


def chain(path):
    out = []
    while 1:
        path, name = os.path.split(path)
        if name=='': break
        out.insert(0,name)
    out.insert(0,path)
    return out

def fash(path, tim=0):
    m = hashlib.md5()
    m.update(str(path).encode('utf-8'))
    m.update(str(tim).encode('utf-8'))
    b = base64.b32encode(m.digest())
    # b = m.digest()
    return str(b)[:-4]


######################################################################################################################################################


class filefilter():
    def __init__(self):
        self.noIndex = {}
        self.names = {}
        self.paths = {}
        self.left = {}

    def test(self, path, name):
        if name in self.names: return 0
        if path in self.paths: return 0
        if path in self.noIndex: return 2
        for i in self.left:
            if name[:len(i)]==i: return 0
        return 1
        # 0 hide item
        # 1 show item
        # 2 show, but don't index

    def growtest(self, path):
        for i in self.noIndex:
            if path[:len(i)]==i: return False
        return True

    def addNoIndex(self, path):
        self.noIndex[path]=None

    def addName(self, name):
        self.names[name]=None

    def addPath(self, path):
        self.paths[path]=None

    def addLeft(self, path):
        self.left[path]=None


######################################################################################################################################################


class node():
    def __init__(self):
        self.name = ''
        self.up = None
        self.kids = {}
        self.dir = True
        self.size = 0
        self.mtime = 0
        self.lock = threading.Lock()

    def fpath(self):
        if self.name=='': return ''
        path = self.name
        n = self
        while 1:
            if n.up.name=='': break
            n = n.up
            path = os.path.join(n.name, path)
        return path

    def scan(self, ff):
        if self.name=='':
            next = list(self.kids.values())
            return next
        path = self.fpath()
        kids = {}
        next = []
        try:
            with os.scandir(path) as it:
                for entry in it:
                    test = ff.test(entry.path, entry.name)
                    if test==0: continue
                    if entry.name in self.kids:
                        n = self.kids[entry.name]
                    else:
                        n = node()
                        n.name = entry.name
                        n.up = self
                    n.dir = entry.is_dir()
                    n.size = (entry.stat(follow_symlinks=False).st_size)
                    n.mtime = (entry.stat(follow_symlinks=False).st_mtime)
                    kids[n.name] = n
                    if not test==2:
                        if n.dir:
                            next.append(n)
        except:
            self.lock.acquire()
            self.kids = {}
            self.lock.release()
            next = []
        self.lock.acquire()
        self.kids = kids
        self.lock.release()
        return next

    def child(self, i):
        self.lock.acquire()
        n = list(self.kids.values())[i]
        self.lock.release()
        return n 

    def childCount(self):
        self.lock.acquire()
        n = len(self.kids)
        self.lock.release()
        return n 

    def row(self):
        if self.up==None: return 0
        sibs = list(self.up.kids.values())
        row = sibs.index(self)
        return row

    def sort(self,i,order=1):
        tree = btree.leaf()
        if i==0:
            for i in self.kids: tree.add(str(i).lower(),self.kids[i])
        if i==1:
            for i in self.kids: tree.add(int(self.kids[i].size), self.kids[i])
        if i==2:
            for i in self.kids: tree.add(int(self.kids[i].mtime), self.kids[i])

        self.kids = {}
        if order==0:
            for v in tree.walkdown(2): self.kids[v.name]=v
        if order==1:
            for v in tree.walkup(2): self.kids[v.name]=v

    def getsize(self):
        if self.dir: self.size = 0
        for i in self.kids:
            self.size += self.kids[i].getsize()
        return self.size


######################################################################################################################################################


def threadwork(qin, ff, foo):
    while 1:
        job, detail = qin.get(True)
        if job==1: scan1(detail, qin, ff)
        if job==2: find1(detail, qin, foo)
        if job==3: find2(detail, foo)
        if job==4: drivecheck(detail)
        if job==5: thumbnail(detail)
    
def scan1(detail, qin, ff):
    n, rec = detail 
    nxt = n.scan(ff)
    if not rec==0:
        for i in nxt:
            en = (1,(i,rec-1))
            qin.put(en)

def find1(detail, qin, foo):
    tar, n, rec = detail
    if len(n.name) >= len(tar):
        if tar.lower() in n.name.lower():
            if tar.lower()==n.name.lower()[:len(tar)]:
                score = 110 - rec 
                entry = (tar, score, n.fpath(), n.dir)
                foo.put(entry)
            else:
                qin.put((3,(tar,n)))
    for i in list(n.kids.values()):
        en = (2,(tar, i, rec+1))
        qin.put(en)

def find2(detail, foo):
    tar, i = detail 
    if len(tar)==1: return 
    # score = fuzz.ratio(tar.lower(), k.name.lower())
    # score = fuzz.partial_ratio(tar.lower(), k.name.lower())
    # score = fuzz.token_sort_ratio(tar.lower(), k.name.lower())
    score = fuzz.token_set_ratio(tar.lower(), i.name.lower())
    if score > 50:
        entry = (tar, score, i.fpath(), i.dir)
        foo.put(entry)

def drivecheck(detail):
    qoo = detail 
    drvlet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    for i in drvlet:
        path = str(i)+':'+os.path.sep 
        if os.path.exists(path):
            total, used, free = shutil.disk_usage(path)
            entry = (path, total, used)
            qoo.put(entry)
    qoo.put((0,0,0))

def thumbnail(detail):
    thumbroot, path, mtime, qoo = detail
    if not path.split('.')[-1].lower() in ['jpg','png','webp','gif','jpeg']: return 

    try:
        tpath = os.path.join(thumbroot,fash(path, mtime))
        if os.path.exists(tpath):
            im = Image.open(tpath)
            qoo.put((path,im))
        else:
            im = Image.open(path)
            im = ImageOps.exif_transpose(im)
            im.thumbnail((200,200))
            qoo.put((path, im))
            im.save(tpath,"JPEG")
    except:
        if os.path.exists(path):
            im = Image.open(path)
            im = ImageOps.exif_transpose(im)
            im.thumbnail((200,200))
            qoo.put((path, im))


######################################################################################################################################################


class coreClass():
    def __init__(self):
        self.set = setter.setter('quickfinder1')

        self.base = node()
        self.n = None
        self.ff = self.set.get('ff',None)
        if self.ff==None:
            self.ff = filefilter()
            self.ff.addLeft('ntuser.dat')
            self.ff.addLeft('NTUSER.DAT')
            self.ff.addName('desktop.ini')
            self.ff.addName('ntuser.ini')

        self.sniffer = node()

        self.homepaths = self.set.get('homepaths',[])
        if len(self.homepaths)==0:
            # self.homepaths.append(os.path.expanduser("~"))
            self.homepaths.append(os.path.join(os.path.expanduser("~"),'Desktop'))
            self.homepaths.append(os.path.join(os.path.expanduser("~"),'Documents'))
            self.homepaths.append(os.path.join(os.path.expanduser("~"),'Downloads'))
            self.homepaths.append(os.path.join(os.path.expanduser("~"),'Pictures'))
            self.homepaths.append(os.path.join(os.path.expanduser("~"),'Videos'))
            self.homepaths.append(os.path.join(os.path.expanduser("~"),'Music'))
            self.set.set('homepaths',self.homepaths)

        self.qin = Queue()
        self.foo = Queue()
        self.pros = []
        for i in range(8):
            t = threading.Thread(target=threadwork, args=(self.qin, self.ff, self.foo),daemon=True)
            self.pros.append(t)
            t.start()

    def addHomePath(self, path):
        self.homepaths.append(path)
        self.set.set('homepaths',self.homepaths)

    def addSnifPath(self, path):
        while 1:
            if os.path.exists(path): break
            path, name = os.path.split(path)
        if not os.path.isdir(path):
            path, name = os.path.split(path)

        c = chain(path)
        n = self.base
        for i in c:
            if i in n.kids:
                n = n.kids[i]
            else:
                k = node()
                k.name = i
                k.up = n
                k.dir = True
                n.kids[i] = k
                n = k
        self.sniffer.kids[n.name]=n

    def locate(self, path):
        c = chain(path)
        n = self.base
        for i in c:
            if i in n.kids:
                n = n.kids[i]
            else:
                return n
        return n

    def setPath(self, path):
        while 1:
            if os.path.exists(path): break
            path, name = os.path.split(path)
        if not os.path.isdir(path):
            path, name = os.path.split(path)

        c = chain(path)
        n = self.base
        for i in c:
            if i in n.kids:
                n = n.kids[i]
            else:
                k = node()
                k.name = i
                k.up = n
                k.dir = True
                n.kids[i] = k
                n = k
        self.n = n
        self.scan()
        return self.n

    def scan(self, n=None, rec=4):
        if n==None: n=self.n
        check = [n]
        nc = []
        for i in range(3):
            for j in check: nc += j.scan(self.ff)
            check = nc
            nc = []
        for j in check: 
            en = (1,(j, rec))
            self.qin.put(en)

    def find(self, tar, n=None):
        if n==None: n = self.n 
        en = (2,(tar,n,0))
        self.qin.put(en)

    def back(self):
        if self.n==self.sniffer:
            return list(self.n.kids.values())[0].fpath()
        if not self.n.up.name=='':
            return self.n.up.fpath()
        return self.n.fpath()

    def fullscan(self, n=None):
        if n==None: n=self.n
        check = [n]
        nc = []
        while 1:
            for j in check: nc += j.scan(self.ff)
            check = nc
            nc = []
            if len(check)==0: break

######################################################################################################################################################


if __name__ == "__main__":
    home = os.path.expanduser("~")
    core = coreClass()
    n = core.setPath(home)
    core.scan()
    time.sleep(1)

    target = 'looking'
    core.find(target)
    while 1:
        try:
            res = core.foo.get(True, 1)
            print(res)
        except:
            break
















#hello
