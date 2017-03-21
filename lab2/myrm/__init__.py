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
        
    def lock_decodator(f):
        def func(self, *args,**kargs):
            self.tr.lock()
            f(self, *args,**kargs)
            self.tr.unlock()
        return func 
        
    @lock_decodator
    def rm(self, filename):
        oldname = os.path.abspath(filename)
        newname =  self.tr.toInternal(filename)       
        os.renames(oldname, newname)
        
    @lock_decodator
    def ls(self, direct='.'):
        int_direct = self.tr.toInternal(direct)
        if os.path.isdir(int_direct): 
            for s in os.listdir(int_direct):
                print(s)
        
    @lock_decodator
    def restore(self, filename):
        oldname =  self.tr.toInternal(filename)
        newname = os.path.abspath(filename)
        os.renames(oldname, newname)
    
    
    def _clean_(self, path, recursive=False):
        if (os.path.isdir(path) and (not recursive)):
            return
        
        if (os.path.isdir(path)):
            for f in os.listdir(path):
                f = os.path.join(path, f)
                self._clean_(f, recursive)
            os.rmdir(path)
        else:
            os.remove(path)
                

    @lock_decodator
    def clean(self, path=None, recursive=False):    
        if path is None:
            path = self.cfg.trash_dir
            for f in os.listdir(path):
                f = os.path.join(path, f)
                if not os.path.samefile(f, self.tr.lockfile()):
                    self._clean_(f, True)
            return
            
        path = self.tr.toInternal(path)
        self._clean_(path, recursive)
        


def getrm():
    cfg = Config()
    return MyRm(cfg)   
    
def main():
    cfg = Config()
    mrm = MyRm(cfg)
    
    
if __name__ == "__main__":
    main()
        
        
