#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
import os
import re

import config
import trash
import utils
import datetime
import fnmatch

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
    def rm(self, filename, recursive=False):
        path, filemask = os.path.split(filename)
        for path in utils.search(path, filemask, filemask, recursive):
            self.tr.add(path)                        
        
        
    @lock_decodator
    def ls(self, filename='.', recursive=False, old=0):
        filename = self.tr.toInternal(filename)
        path, filemask = os.path.split(filename)
    
        for path in utils.search(path, fnmatch.translate(filemask), fnmatch.translate(filemask+'.*.*'), recursive=recursive, findall=True):
            
            isdir = os.path.isdir(path)
            f, time = self.tr.toExternal(path)
            if isdir:
                print('dir: ' + f)
            else:
                f, time = self.tr.toExternal(path)
                print('file: ' +  f + ' ' + time.isoformat())
        
    @lock_decodator
    def rs(self, filename, recursive=False, old=0):
        filename = self.tr.toInternal(filename)
        path, filemask = os.path.split(filename) 
        print(path, fnmatch.translate(filemask+'.*.*'))
        for path in utils.search(path, fnmatch.translate(filemask), fnmatch.translate(filemask+'.*.*'), recursive=recursive):
            self.tr.rs(path)
        

    @lock_decodator
    def clean(self, path=None, recursive=False, old=0):    
        path, filemask = os.path.split(path)
        path = self.tr.toInternal(path)
        
        for path in utils.search(path, fnmatch.translate(filemask), fnmatch.translate(filemask + '.*.*'),  recursive):
            self.tr.rm(path)
        


def getrm():
    cfg = Config()
    return MyRm(cfg)   
    
def main():
    cfg = Config()
    mrm = MyRm(cfg)
    
    
if __name__ == "__main__":
    main()
        
        
