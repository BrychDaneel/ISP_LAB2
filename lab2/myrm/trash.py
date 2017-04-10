# -*- coding: utf-8 -*-
import os
import utils
import datetime

class Trash(object):
    
    def __init__(self, cfg):
        self.cfg = cfg
        self._dirpath = None
        self._lockfile = None
        self._size = None
        self._elems = None

        
    def lockfile(self):
        return os.path.join(self.cfg.trash_dir, self.cfg.trash_lockfile)    
    
    def lock(self):
        if not (os.path.exists(self.cfg.trash_dir)):
            os.makedirs(self.cfg.trash_dir)
        
        lf = self.lockfile()
        assert(not os.path.exists(lf))
        self._dirpath  = self.cfg.trash_dir
        self._elems = utils.filecount(self._dirpath)
        self._size = utils.size(self._dirpath)
        self._lockfile = lf
        open(lf, "w").close()
    
    def unlock(self):
        self._dirpath = None
        self._lockfile = None
        self._size = None
        self._elems = None
        lf = self.lockfile()
        os.remove(lf)

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
    
    

    def addFile(self, filename): 
        oldname = os.path.abspath(filename)
        newname =  self.toInternal(filename)
        newname = utils.addstamp(newname, datetime.datetime.utcnow())
        if utils.acsess(oldname, "Moving file {} to {}".format(oldname, newname), self.cfg):
            if not os.path.exists(os.path.dirname(newname)):
                os.makedirs(os.path.dirname(newname))
            os.rename(oldname, newname)    
            
    def addDir(self, dirname):
        oldname = os.path.abspath(dirname)
        newname =  self.toInternal(dirname)
        
        if utils.acsess(oldname, "Moving dir {} to {}".format(oldname, newname), self.cfg):
            if not os.path.exists(newname):
                os.makedirs(newname)
            
            for f in os.listdir(dirname):
                full = os.path.join(dirname, f)
                isdir = os.path.isdir(full)
                if  isdir:
                    self.addDir(full)
                else:
                    self.addFile(full)
            os.rmdir(oldname)

            
    def rsfile(self, filename):
        oldname = os.path.abspath(filename)
        newname = self.toExternal(oldname)[0]
            
        if utils.acsess(oldname, "Moving file {} to {}".format(oldname, newname), self.cfg):
            if not os.path.exists(os.path.dirname(newname)):
                os.makedirs(os.path.dirname(newname))
            os.rename(oldname, newname) 
            
            
    def rsdir(self, dirname):
        oldname = os.path.abspath(dirname)
        newname =  self.toExternal(oldname)[0]
        
        if utils.acsess(oldname, "Moving dir {} to {}".format(oldname, newname), self.cfg):
            if not os.path.exists(newname):
                os.makedirs(newname)
            
            for f in os.listdir(dirname):
                full = os.path.join(dirname, f)
                isdir = os.path.isdir(full)
                if  isdir:
                    self._rsdir(full)
                else:
                    self._rsfile(full)
                    
    def rs(self, path):
        if os.path.isdir(path):
            self.rsdir(path)
        else:
            self.rsfile(path)
            
    def add(self, path):
        
        newsize = self._size + utils.size(path)
        newcount = self._elems + utils.filecount(path)
        assert(newsize <= self.cfg.trash_maxsize)
        assert(newcount <= self.cfg.trash_maxelems)
        
        if os.path.isdir(path):    
            self.addDir(path)
        else:
            self.addFile(path)
            
        self._size = newsize
        self._elems = newcount
            
            
                    
                    
    def rm(self, path):
        if not utils.acsess(path, "Delete {}".format(path), self.cfg):
            return
        
        if not os.path.isdir(path):
            os.remove(path)
        else:
            for dirpath, dirnames, filenames in os.walk(path, topdown = True):
                for f in filenames:
                    os.remove(f)
                os.rmdir(dirpath)
                
    
    def cleanOld(self, file_time):        
        now = datetime.datetime.utcnow()
        print(file_time)
        oldfiles = filter(lambda f, t: datetime.timedelta(t, now).days  > self.cfg.trash_maxdays,  file_time)
                
        for f, t in oldfiles:
            self.rm(f)
        return list(set(file_time).difference(oldfiles)) 
    
    
    def cleanLot(self, files):
        file_time.sort(key=lambda f, t: t, reversed=True)
        
        while (self.cfg.trash_maxcount < self._cleanelems or self.cfg.trash_cleansize < self._size):
            self.rm(file_time[-1][0])
            file_time.pop(-1)
    
    def cleanSame(self, files):
        file_time.sort(key=lambda f, t: t)
        
        d = {}
        for f, t in file_time:
            if not f in d:
                d[f]=[]
            d[f].append(t)
        
        nf = files[:]
        for key, val in d.iteritems:
            val.sort(reversed=True)
            if len(val) > cfg.trash_maxsame:
                for dt in val[trash_maxsize:-1]:
                    rm(utils.addstamp(key, dt))
                    nf.remove(key, dt)
        return nf
                    
    
    def autoclean(self):
        
        files = []
        for dirpath, dirnames, filenames in os.walk(self._dirpath):
            files.extend([os.path.join(dirpath, f) for f in filenames])
            
        files = filter(lambda fn: not os.path.samefile(fn, self._lockfile), files)
                
        file_time = [utils.splitstamp(f) for f in files]
        file_time = self.cleanOld(file_time)
        file_time = self.cleanLot(file_time)
        file_time = self.cleanSame(file_time)
        
