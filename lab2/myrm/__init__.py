#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
import os
import re

import config
import trash
import utils
import datetime
import fnmatch
import logging
import acsess_manager
import autoclean

from trash import Trash
from acsess_manager import AcsessManager



class MyRm(object):
    
    def __init__(self, cfg):
        self.cfg = cfg
        self.tr = Trash(cfg)
        self.ascmanager = AcsessManager(cfg)
        
    def lock_decodator(f):
        def func(self, *args,**kargs):
            self.tr.lock()
            try:
                f(self, *args,**kargs)
            finally:
                self.tr.unlock()
        return func 
                                
        
    @lock_decodator
    def rm(self, filename, recursive=False):
        path, filemask = os.path.split(filename)
        for path in utils.search(path, fnmatch.translate(filemask), fnmatch.translate(filemask), recursive):
            if  self.ascmanager.removeAcsess(path):
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
        for path in utils.search(path, fnmatch.translate(filemask), fnmatch.translate(filemask+'.*.*'), recursive=recursive):
            if  self.ascmanager.restoreAcsess(self.tr.toExternal(path)):
                self.tr.rs(path)
        

    @lock_decodator
    def clean(self, path=None, recursive=False, old=0):    
        path, filemask = os.path.split(path)
        path = self.tr.toInternal(path)
        
        for path in utils.search(path, fnmatch.translate(filemask), fnmatch.translate(filemask + '.*.*'),  recursive):
            if  self.ascmanager.cleanAcsess(self.tr.toExternal(path)):
                self.tr.rm(path)
                
                
    @lock_decodator            
    def autoclean(self, path=None, recursive=False): 
        if  self.ascmanager.autocleanAcsess():
            autoclean.autoclean(self.tr)


def getrm():
    logging.basicConfig(level = logging.DEBUG)
    cfg = config.getDefaultConfig()
    return MyRm(cfg)   
    
def main():
    cfg = config.getDefaultConfig()
    mrm = MyRm(cfg)
    
    
if __name__ == "__main__":
    main()
        
        
