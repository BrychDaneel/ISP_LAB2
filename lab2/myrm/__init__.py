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
import argparse

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
        for path in utils.search(path, filemask, filemask, recursive=recursive):
            if  self.ascmanager.removeAcsess(path):
                self.tr.add(path)                        
        
        
    @lock_decodator
    def ls(self, filename='.', recursive=False, versions=True):
        filename = self.tr.toInternal(filename)
        path, filemask = os.path.split(filename)
    
        files  = utils.search(path, filemask, filemask+'.*.*', 
                              recursive=recursive, findall=True)
        vfiles = utils.timefilesToFileDict(files)
        for path in vfiles:
            
            for dtime in vfiles[path]:
                isdir = os.path.isdir(path)
                if isdir:
                    print('dir: ' + path)
                else:
                    f, time = self.tr.toExternal(path)
                    print('file: ' +  path + ' ' + dtime.isoformat())
                
                if not versions:
                    break
            
    @lock_decodator
    def rs(self, filename, recursive=False, old=0):
        filename = self.tr.toInternal(filename)
        path, filemask = os.path.split(filename) 
        
        files = utils.search(path, filemask, filemask+'.*.*', recursive=recursive)
        vfiles = utils.timefilesToFileDict(files)
        
        for path in vfiles:
            ln = len(vfiles[path])
            vers = old if old < ln  else ln - 1 
            filename = utils.addstamp(path, vfiles[path][vers])
            if  self.ascmanager.restoreAcsess(self.tr.toExternal(filename)):
                self.tr.rs(filename)
        

    @lock_decodator
    def clean(self, path=None, recursive=False, old=0):    
        path, filemask = os.path.split(path)
        path = self.tr.toInternal(path)
        
        files = utils.search(path, filemask, filemask + '.*.*',  recursive=recursive)
        vfiles = utils.timefilesToFileDict(files)
        
        for path in vfiles:
            ln = len(vfiles[path])
            vers = old if old < ln  else ln - 1 
            filename = utils.addstamp(path, vfiles[path][vers])
            if  self.ascmanager.cleanAcsess(self.tr.toExternal(filename)):
                self.tr.rm(filename)
                
                
    @lock_decodator            
    def autoclean(self): 
        if  self.ascmanager.autocleanAcsess():
            autoclean.autoclean(self.tr)


def getDefaultMyRm():
    cfg = config.getDefaultConfig()
    return MyRm(cfg)



def main():
    parser = argparse.ArgumentParser(prog='myrm')
    
    parser.add_argument('command',choices=['rm', 'rs', 'ls', 'clear', 'autoclear'])
    parser.add_argument('filemask')
    parser.add_argument('-r','-R','--recursive',dest='recursive', action='store_true')
    parser.add_argument('-o','--old',dest='old', default=0)
    
    parser.add_argument('--config', default=None)
    parser.add_argument('--jsonconfig', default=None)
    
    parser.add_argument('-v','--verbose',dest='verbose', action='store_const', const=True)
    parser.add_argument('-d','--dryrun',dest='dryrun', action='store_const', const=True)
    parser.add_argument('-f','--force',dest='force', action='store_const', const=True)
    parser.add_argument('-i','--interactive',dest='interactive', action='store_const', const=True)
    
    
    args = parser.parse_args()
    cfg = config.getDefaultConfig()
    
    if not args.config is None:
        cfg = config.loadFromCFG(args.config)
        
    if not args.jsonconfig is None:
        cfg = config.loadFromJSON(args.config)
        
    
    if not args.force is None:
        cfg['force'] = args.force
    if not args.dryrun is None:
        cfg['dryrun'] = args.dryrun
    if not args.verbose is None:
        cfg['verbose'] = args.verbose
    if not args.interactive is None:
        cfg['interactive'] = args.interactive
        
    mrm = MyRm(cfg)
    
    cmd = args.command
    if cmd == 'rm':
        mrm.rm(args.filemask, recursive=args.recursive)
    elif cmd == 'rs':
        mrm.rs(args.filemask, recursive=args.recursive, old=args.old)
    elif cmd== 'ls':
        mrm.ls(args.filemask, recursive=args.recursive)
    elif cmd == 'clear':
        mrm.clean(args.filemask, recursive=args.recursive, old=args.old)
    elif cmd == 'autoclear':
        mrm.autoclean()
        
def mrm():
    parser = argparse.ArgumentParser(prog='myrm')
    
    parser.add_argument('filemask')
    parser.add_argument('-r','-R','--recursive',dest='recursive', action='store_true')
    
    parser.add_argument('--config', default=None)
    parser.add_argument('--jsonconfig', default=None)
    
    parser.add_argument('-v','--verbose',dest='verbose', action='store_const', const=True)
    parser.add_argument('-d','--dryrun',dest='dryrun', action='store_const', const=True)
    parser.add_argument('-f','--force',dest='force', action='store_const', const=True)
    parser.add_argument('-i','--interactive',dest='interactive', action='store_const', const=True)
    
    
    args = parser.parse_args()
    cfg = config.getDefaultConfig()
    
    if not args.config is None:
        cfg = config.loadFromCFG(args.config)
        
    if not args.jsonconfig is None:
        cfg = config.loadFromJSON(args.config)
        
    
    if not args.force is None:
        cfg['force'] = args.force
    if not args.dryrun is None:
        cfg['dryrun'] = args.dryrun
    if not args.verbose is None:
        cfg['verbose'] = args.verbose
    if not args.interactive is None:
        cfg['interactive'] = args.interactive
        
    mrm = MyRm(cfg)
    mrm.rm(args.filemask, recursive=args.recursive)   
    
if __name__ == "__main__":
    main() 

        
        
