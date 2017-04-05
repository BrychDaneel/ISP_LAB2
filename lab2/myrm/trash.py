# -*- coding: utf-8 -*-
import os

class Trash(object):
    
    def __init__(self, cfg):
        self.cfg = cfg
        if not (os.path.exists(cfg.trash_dir)):
            os.makedirs(cfg.trash_dir)
        
    def lockfile(self):
        return os.path.join(self.cfg.trash_dir, self.cfg.trash_lockfile)    
    
    def lock(self):
        lf = self.lockfile()
        open(lf, "w").close()
    
    def unlock(self):
        lf = self.lockfile()
        os.remove(lf)

    def splitpath(self, path):
        spath = []
        p, tk = os.path.split(path)
        while (tk):
            spath.append(tk)
            p, tk = os.path.split(p)    
        spath.append(p)
        spath.reverse()
        
        return spath 

    def toInternal(self, path):
        
        path = os.path.abspath(path) 
        
        spath = self.splitpath(path)
        
        protocol = spath[0]
        spath[0] = ' '.join([str(ord(s)) for s in protocol])
        
        newpath = os.path.join(self.cfg.trash_dir, *spath)
        return newpath
    
    
    def toExternal(self, path):
        newname = os.path.relpath(path,self.cfg.trash_dir)
        spath = self.splitpath(newname)[1:]
        spath[0] = ''.join(chr(int(s)) for s in spath[0].split(' '))
        
        newname = os.path.join(*spath)
        
        if not os.path.isdir(path):
            newname = '.'.join(newname.split('.')[0:-2])
        return newname

        
