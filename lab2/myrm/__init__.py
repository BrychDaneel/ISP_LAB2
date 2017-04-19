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
from acsess_manage import AcsessManager


class MyRm(object):
    
    def __init__(self, cfg):
        self.cfg = cfg
        self.trash = Trash(cfg)
        self.acsess_manager = AcsessManager(cfg)
        
    def lock_decodator(f):
        def func(self, *args,**kargs):
            self.trash.lock()
            try:
                return f(self, *args,**kargs)
            finally:
                self.trash.unlock()
        return func 
                                
        
    @lock_decodator
    def rm(self, path_mask, recursive=False):
        directory, mask = os.path.split(path_mask)
        found = utils.search(directory, mask, mask, recursive=recursive)
        for path in found:
            if  self.acsess_manager.removeAcsess(path):
                self.trash.add(path)                        
        
        
    @lock_decodator
    def ls(self, path_mask='*', recursive=False, versions=True):
        result = []
        path_mask = self.trash.toInternal(path_mask)
        directory, mask = os.path.split(path_mask)
        file_mask = utils.extend_mask_by_stamp(mask)
        found  = utils.search(path, mask, file_mask, 
                              recursive=recursive, findall=True)
        vfiles = utils.timefilesToFileDict(files)
        for path in vfiles:      
            for dtime in vfiles[path]:
                isdir = os.path.isdir(path)
                if isdir:
                    result.extend((path, None))
                else:
                    f, time = self.trash.toExternal(path)
                    result.extend((path, dtime))
                
                if not versions:
                    break
        return res
            
    @lock_decodator
    def rs(self, filename, recursive=False, old=0):
        filename = self.trash.toInternal(filename)
        path, filemask = os.path.split(filename) 
        
        files = utils.search(path, filemask, utils.extend_mask_by_stamp(filemask), recursive=recursive)
        vfiles = utils.timefilesToFileDict(files)
        
        for path in vfiles:
            if  self.acsess_manager.restoreAcsess(self.trash.toExternal(filename)):
                self.trash.rs(path, old=old)
        

    @lock_decodator
    def clean(self, path=None, recursive=False, old=-1):    
        path, filemask = os.path.split(path)
        path = self.trash.toInternal(path)
        
        files = utils.search(path, filemask, utils.extend_mask_by_stamp(filemask),  recursive=recursive)
        vfiles = utils.timefilesToFileDict(files)
        
        for path in vfiles:
            if  self.acsess_manager.cleanAcsess(self.trash.toExternal(filename)):
                self.trash.rm(path, old=old)
                
                
    @lock_decodator            
    def autoclean(self): 
        if  self.acsess_manager.autocleanAcsess():
            autoclean.autoclean(self.trash)


def getDefaultMyRm():
    cfg = config.getDefaultConfig()
    return MyRm(cfg)



def main(rm_only=False):
    parser = argparse.ArgumentParser(prog='myrm')
    
    if not rm_only:
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
    
    if rm_only:
        mrm.rm(args.filemask, recursive=args.recursive) 
    else:
        cmd = args.command
        if cmd == 'rm':
            mrm.rm(args.filemask, recursive=args.recursive)
        elif cmd == 'rs':
            mrm.rs(args.filemask, recursive=args.recursive, old=args.old)
        elif cmd== 'ls':
            files = mrm.ls(args.filemask, recursive=args.recursive)
            print(files)
        elif cmd == 'clear':
            mrm.clean(args.filemask, recursive=args.recursive, old=args.old)
        elif cmd == 'autoclear':
            mrm.autoclean()
        
def mrm():
    main(rm_only=True)
      
    
if __name__ == "__main__":
    main() 

        
        
