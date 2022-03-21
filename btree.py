import random
import time

class leaf():
    def __init__(self, val=None, dat=None):
        self.val = val
        self.dat = dat

        self.r = None
        self.l = None
        self.up = None

    def add(self, val, dat=None):
        if self.val==None:
            self.val = val
            self.dat = dat
            return

        k = leaf(val,dat)
        n = self
        while 1:
            if k.val >= n.val:
                if n.r == None:
                    n.r = k
                    k.up = n
                    return
                else:
                    n = n.r
                    continue
            else:
                if n.l == None:
                    n.l = k
                    k.up = n
                    return
                else:
                    n = n.l
                    continue

    def walkup(self, ret=0):
        n = self
        d = 0
        out = []
        while 1:
            if d==0:
                if not n.l==None:
                    n = n.l
                    d = 0
                    continue
                else:
                    d = 1
            if d==1:
                if ret==0: out.append((n.val, n.dat))
                if ret==1: out.append(n.val)
                if ret==2: out.append(n.dat)
                if not n.r==None:
                    n = n.r
                    d = 0
                    continue
                else:
                    d = 2
            if d==2:
                if n.up==None: return out
                if n.up.l == n:
                    n = n.up
                    d = 1
                    continue
                else:
                    n = n.up
                    d = 2
                    continue

    def walkdown(self,ret=0):
        n = self
        d = 0
        out = []
        while 1:
            if d==0:
                if not n.r==None:
                    n = n.r
                    d = 0
                    continue
                else:
                    d = 1
            if d==1:
                if ret==0: out.append((n.val, n.dat))
                if ret==1: out.append(n.val)
                if ret==2: out.append(n.dat)
                if not n.l==None:
                    n = n.l
                    d = 0
                    continue
                else:
                    d = 2
            if d==2:
                if n.up==None: return out
                if n.up.r == n:
                    n = n.up
                    d = 1
                    continue
                else:
                    n = n.up
                    d = 2
                    continue

    def dropmin(self):
        n = self
        p = self
        while not n.l==None:
            p = n
            n = n.l
        if n==p:
            if not n.r==None:
                n.val = n.r.val
                n.dat = n.r.dat
                n.l = n.r.l
                n.r = n.r.r
                if not n.r==None: n.r.up = n
        else:
            if not n.r==None: n.r.up = p
            p.l = n.r
        return (n.val, n.dat)

    def find(self, val):
        n = self
        if n.val==None: return None
        while 1:
            if val == n.val: return n.dat
            if val > n.val:
                if n.r == None:
                    return None
                else:
                    n = n.r
                    continue
            else:
                if n.l == None:
                    return None
                else:
                    n = n.l
                    continue


class tree(leaf):
    def __init__(self, val=None, dat=None):
        super(tree, self).__init__(val,dat)
        self.count=0
        self.min = 0

    def add(self, val, dat=None):
        super(tree, self).add(val,dat)
        self.count+=1

    def top(self, val, dat=None, top=20):
        if self.count==top:
            if val < self.min: return
        super(tree, self).add(val,dat)
        self.count+=1
        while self.count > top:
            self.min = self.dropmin()[0]
            self.count-=1





if __name__ == "__main__":
    n = tree()
    for i in range(100):
        v = random.randint(0,100)
        d = i
        n.top(v,d,10)
        s = n.walkup(1)
        print(s)
    # print(n.walkup(1))
