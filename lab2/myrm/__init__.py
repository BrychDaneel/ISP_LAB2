#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
import os

import config
import trash

from config import Config
from trash import Trash

class MyRm(object):
    
    def __init__(self, cfg):
        self.cfg = cfg
        self.tr = Trash(cfg)
    
    def rm(self, filename):
        self.tr.lock()
        oldname = os.path.abspath(filename)
        newname =  self.tr.toInternal(filename)       
        os.renames(oldname, newname)
        self.tr.unlock()
    
    def ls(self, direct='.'):
        self.tr.lock()
        int_direct = self.tr.toInternal(direct)
        if os.path.isdir(int_direct): 
            for s in os.listdir(int_direct):
                print(s)
        self.tr.unlock()
    
    def restore(self, filename):
        self.tr.lock()
        oldname =  self.tr.toInternal(filename)
        newname = os.path.abspath(filename)
        os.renames(oldname, newname)
        self.tr.unlock()
    
    def clean(self, path=None, recursive=False):
        
        if path is None:
            path = self.cfg.trash_dir
            recursive = True
        
        if not(os.path.samefile(os.path.commonprefix([path, self.cfg.trash_dir]))): 
            path = self.tr.toInternal(path)
        
        if (os.path.isdir(path) and (not recursive)):
            return
        
        if (os.path.isdir(path)):
            for f in os.listdir(path):
                f = os.path.join(path, f)
                if os.path.isdir(f):
                    self.clean(f, recursive)
            os.rmdir(path)
        else:
            if not os.path.samefile(path, self.tr.lockfile()):
                os.remove(f)
                    
    

def getrm():
    cfg = Config()
    return MyRm(cfg)   
    
def main():
    cfg = Config()
    mrm = MyRm(cfg)
    
    
if __name__ == "__main__":
    main()
        
        
