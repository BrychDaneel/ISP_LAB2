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

    def toInternal(self, path):
        
        path = os.path.abspath(path) 
        
        spath = []
        p, tk = os.path.split(path)
        while (tk):
            spath.append(tk)
            p, tk = os.path.split(p)    
        spath.append(p)
        spath.reverse()
        
        protocol = spath[0]
        spath[0] = ' '.join([str(ord(s)) for s in protocol])
        
        newpath = os.path.join(self.cfg.trash_dir, *spath)
        return newpath
