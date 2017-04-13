# -*- coding: utf-8 -*-

import os
import utils
import datetime
import logging

class Trash(object):
    
    def __init__(self, cfg):
        self.cfg = cfg
        self.dirpath = None
        self.lockfile = None
        self.size = None
        self.elems = None
        self.locked = False
        
    def fullLockfile(self):
        return os.path.join(self.cfg["trash"]["dir"], self.cfg["trash"]["lockfile"])    
    
    def lock(self):
        if not (os.path.exists(self.cfg["trash"]["dir"])):
            os.makedirs(self.cfg["trash"]["dir"])
        
        lf = self.fullLockfile()
        assert(not os.path.exists(lf))
        open(lf, "w").close()
        self.dirpath  = self.cfg["trash"]["dir"]
        self.elems = utils.filecount(self.dirpath) - utils.filecount(lf)
        self.size = utils.size(self.dirpath) - utils.size(lf)
        self.lockfile = lf
        self.locked = True
    
    def unlock(self):
        lf = self.fullLockfile()
        os.remove(lf)
        self.dirpath = None
        self.lockfile = None
        self.size = None
        self.elems = None
        self.locked = False
        
    def needlock_decodator(f):
        def func(self, *args,**kargs):
            if self.locked:
                f(self, *args,**kargs)
            else:
                assert(False)
        return func 

    def toInternal(self, path):
        
        path = os.path.abspath(path) 
        
        spath = utils.splitpath(path)
        
        protocol = spath[0]
        spath[0] = ' '.join([str(ord(s)) for s in protocol])
        
        newpath = os.path.join(self.dirpath, *spath)
        return newpath
    
    
    def toExternal(self, path):
        newname = os.path.relpath(path, self.dirpath)
        spath = utils.splitpath(newname)[1:]
        spath[0] = ''.join(chr(int(s)) for s in spath[0].split(' '))
        
        newname = os.path.join(*spath)
        
        if (not os.path.isdir(path)):
            filename, removetime = utils.splitstamp(newname)
        else:
            filename, removetime = newname, None
            
        filename = os.path.relpath(filename)
        return filename, removetime
    
    
    @needlock_decodator
    def addFile(self, filename): 
        oldname = os.path.abspath(filename)
        newname =  self.toInternal(filename)
        newname = utils.addstamp(newname, datetime.datetime.utcnow())
        logging.debug("Moving file {} to {}".format(oldname, newname))
        if not os.path.exists(os.path.dirname(newname)):
            os.makedirs(os.path.dirname(newname))
        os.rename(oldname, newname)    
    
    @needlock_decodator
    def addDir(self, dirname):
        oldname = os.path.abspath(dirname)
        newname =  self.toInternal(dirname)
        
        if not os.path.exists(newname):
            logging.debug("Make dir {} ".format( newname))
            os.makedirs(newname)
        
        for f in os.listdir(dirname):
            full = os.path.join(dirname, f)
            isdir = os.path.isdir(full)
            if  isdir:
                self.addDir(full)
            else:
                self.addFile(full)
        os.rmdir(oldname)

    @needlock_decodator        
    def rsfile(self, filename):
        oldname = os.path.abspath(filename)
        newname = self.toExternal(oldname)[0]
            
        
        if not os.path.exists(os.path.dirname(newname)):
            logging.debug("Make dir {} ".format( newname))
            os.makedirs(os.path.dirname(newname))
            
        logging.debug("Moving file {} to {}".format(oldname, newname))
        os.rename(oldname, newname) 
            
    @needlock_decodator        
    def rsdir(self, dirname):
        oldname = os.path.abspath(dirname)
        newname =  self.toExternal(oldname)[0]
        
        
        if not os.path.exists(newname):
            logging.debug("Make dir {} ".format( newname))
            os.makedirs(newname)
        
        for f in os.listdir(dirname):
            full = os.path.join(dirname, f)
            isdir = os.path.isdir(full)
            if  isdir:
                self.rsdir(full)
            else:
                self.rsfile(full)
                
    @needlock_decodator                
    def rs(self, path):
       
        if os.path.isdir(path):
            self.rsdir(path)
        else:
            self.rsfile(path)
        return True
    
    
    @needlock_decodator        
    def add(self, path):
        
        newsize = self.size + utils.size(path)
        newcount = self.elems + utils.filecount(path)
        assert(newsize <= self.cfg["trash"]["max"]["size"])
        assert(newcount <= self.cfg["trash"]["max"]["count"])
        
        if os.path.isdir(path):    
            self.addDir(path)
        else:
            self.addFile(path)
            
        self.size = newsize
        self.elems = newcount
    
        return True
            
    @needlock_decodator           
    def rm(self, path):
       
        newsize = self.size - utils.size(path)
        newcount = self.elems - utils.filecount(path)
       
        if not os.path.isdir(path):
            os.remove(path)
        else:
            for dirpath, dirnames, filenames in os.walk(path, topdown = True):
                for f in filenames:
                    os.remove(f)
                os.rmdir(dirpath)
                
        self.size = newsize
        self.elems = newcount     
        return True
