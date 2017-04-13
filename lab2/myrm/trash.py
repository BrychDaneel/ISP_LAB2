# -*- coding: utf-8 -*-
import os
import utils
import datetime
import logging

class Trash(object):
    
    def __init__(self, cfg):
        self.cfg = cfg
        self._dirpath = None
        self._lockfile = None
        self._size = None
        self._elems = None
        self._locked = False
        
    def lockfile(self):
        return os.path.join(self.cfg["trash"]["dir"], self.cfg["trash"]["lockfile"])    
    
    def lock(self):
        if not (os.path.exists(self.cfg["trash"]["dir"])):
            os.makedirs(self.cfg["trash"]["dir"])
        
        lf = self.lockfile()
        assert(not os.path.exists(lf))
        open(lf, "w").close()
        self._dirpath  = self.cfg["trash"]["dir"]
        self._elems = utils.filecount(self._dirpath) - utils.filecount(lf)
        self._size = utils.size(self._dirpath) - utils.size(lf)
        self._lockfile = lf
        self._locked = True
    
    def unlock(self):
        lf = self._lockfile
        os.remove(lf)
        self._dirpath = None
        self._lockfile = None
        self._size = None
        self._elems = None
        self._locked = False
        
    def needlock_decodator(f):
        def func(self, *args,**kargs):
            if self._locked:
                f(self, *args,**kargs)
            else:
                assert(False)
        return func 

    def toInternal(self, path):
        
        path = os.path.abspath(path) 
        
        spath = utils.splitpath(path)
        
        protocol = spath[0]
        spath[0] = ' '.join([str(ord(s)) for s in protocol])
        
        newpath = os.path.join(self._dirpath, *spath)
        return newpath
    
    
    def toExternal(self, path):
        newname = os.path.relpath(path, self._dirpath)
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
        
        newsize = self._size + utils.size(path)
        newcount = self._elems + utils.filecount(path)
        assert(newsize <= self.cfg["trash"]["max"]["size"])
        assert(newcount <= self.cfg["trash"]["max"]["count"])
        
        if os.path.isdir(path):    
            self.addDir(path)
        else:
            self.addFile(path)
            
        self._size = newsize
        self._elems = newcount
        
        return True
            
    @needlock_decodator           
    def rm(self, path):
       
        newsize = self._size - utils.size(path)
        newcount = self._elems - utils.filecount(path)
       
        if not os.path.isdir(path):
            os.remove(path)
        else:
            for dirpath, dirnames, filenames in os.walk(path, topdown = True):
                for f in filenames:
                    os.remove(f)
                os.rmdir(dirpath)
                
        self._size = newsize
        self._elems = newcount     
        return True
    
    
    
    def _autocleanByDate(self, file_time):        
        now = datetime.datetime.utcnow()
        oldfiles = filter(lambda (f, t): (now - t).days  > self.cfg.trash_maxdays,  file_time)
                
        for f, t in oldfiles:
            logging.debug("{} is too old".format(utils.addstamp(f, t)))
            self.rm(utils.addstamp(f, t))
        return list(set(file_time).difference(oldfiles)) 
    
    
    
    def _autocleanByTrashCount(self, file_time):
        nft = sorted(file_time,key=lambda (f, t): t, reverse=True) 
         
        while self.cfg["trash"]["clean"]["count"] <= self._elems:
            f, t = nft[-1]
            logging.debug("Removing {} to free bukkit({} files excess)".format(
                utils.addstamp(f, t), self._elems - self.cfg["trash"]["clean"]["count"] + 1))
            self.rm(utils.addstamp(f, t))
            nft.pop(-1)
        return nft
    
    def _autocleanByTrashSize(self, file_time):
        nft = sorted(file_time,key=lambda (f, t): t, reverse=True) 
         
        while self.cfg.trash_cleansize <= self._size:
            f, t = nft[-1]
            logging.debug("Removing {} to free bukkit({} bytes excess)".format(
                utils.addstamp(f, t), self._size - self.cfg["trash"]["clean"]["size"]))
            self.rm(utils.addstamp(f, t))
            nft.pop(-1)
        return nft
    
    def _cleanBySameCount(self, file_time):
        nf = file_time[:]
    
        d = {}
        for f, t in nf:            
            if not f in d:
                d[f]=[]
            d[f].append(t)
        
        
        for key, val in d.iteritems():
            val.sort(reverse=True)
            if len(val) > self.cfg["trash"]["clean"]["samename"]:
                for dt in val[self.cfg["trash"]["clean"]["samename"]:]:
                    logging.debug("Removing {} becouse  there are a lot of same file".format(utils.addstamp(key, dt)))
                    self.rm(utils.addstamp(key, dt))
                    nf.remove((key, dt))
        return nf
                    
    @needlock_decodator
    def autoclean(self):
        
        files = []
        for dirpath, dirnames, filenames in os.walk(self._dirpath):
            files.extend([os.path.join(dirpath, f) for f in filenames])
            
        files = filter(lambda fn: not os.path.samefile(fn, self._lockfile), files)
                
        file_time = [utils.splitstamp(f) for f in files]
        file_time = self._autocleanByDate(file_time)
        file_time = self._autocleanByTrashCount(file_time)
        file_time = self._autocleanByTrashSize(file_time)
        file_time = self._cleanBySameCount(file_time)
        
