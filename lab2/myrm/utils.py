# -*- coding: utf-8 -*- 
import os
import re
import datetime
import fnmatch  

def search(path, dirmask, filemask, recursive=False, findall=False):

        fm = re.compile(filemask)
        dm = re.compile(dirmask)
        for f in os.listdir(path):
            full = os.path.join(path, f)
            isdir = os.path.isdir(full)
            
            if not isdir and fm.match(f): 
                yield  full
            
            if isdir and dm.match(f):
                yield full
                
            if isdir and recursive and (not dm.match(f) or findall):
                for match in search(full, dirmask, filemask, recursive, findall):
                    yield match    
            
                    
                    
def timestamp(d):
    return (d.toordinal() - datetime.date(1970, 1, 1).toordinal())*24*60*60 + d.hour*60*60 + d.minute * 60 + d.second, d.microsecond

def addstamp(path, dt):
    ts, msec = timestamp(dt)
    return "{name}.{timestamp}.{msec}".format(name=path, timestamp=ts, msec=msec)

def splitstamp(path):

    spl =  path.split('.')
    if not os.path.isdir(path):
        newname = '.'.join(spl[0:-2])
        
    sec = int(spl[-2])
    msec = int(spl[-1])
   
    
    time = datetime.datetime.utcfromtimestamp(sec)
    time += datetime.timedelta(microseconds = msec)
    return newname, time


def splitpath(path):
    spath = []
    p, tk = os.path.split(path)
    while (tk):
        spath.append(tk)
        p, tk = os.path.split(p)    
    spath.append(p)
    spath.reverse()
    
    return spath 

def filecount(path):
    if (not os.path.isdir(path)):
        return 1
    
    ans = 0
    for dirpath, dirnames, filenames in os.walk(path):
        ans += len(filenames)
    return ans
    
    
def size(path):
    if (not os.path.isdir(path)):
        return os.path.getsize(path)
    
    ans = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            full = os.path.join(dirpath,f)
            ans += os.path.getsize(full)
    return ans
