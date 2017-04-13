# -*- coding: utf-8 -*- 

import os
import logging
import utils
import datetime

def _autocleanByDate(trash, file_time):        
    now = datetime.datetime.utcnow()
    oldfiles = filter(lambda (f, t): (now - t).days  > trash.cfg["trash"]["autoclean"]["days"],  file_time)
            
    for f, t in oldfiles:
        logging.debug("{} is too old".format(utils.addstamp(f, t)))
        trash.rm(utils.addstamp(f, t))
    return list(set(file_time).difference(oldfiles)) 



def _autocleanByTrashCount(trash, file_time):
    nft = sorted(file_time,key=lambda (f, t): t, reverse=True) 
        
    while trash.cfg["trash"]["autoclean"]["count"] <= trash.elems:
        f, t = nft[-1]
        logging.debug("Removing {} to free bukkit({} files excess)".format(
            utils.addstamp(f, t), trash.elems - trash.cfg["trash"]["autoclean"]["count"] + 1))
        trash.rm(utils.addstamp(f, t))
        nft.pop(-1)
    return nft

def _autocleanByTrashSize(trash, file_time):
    nft = sorted(file_time,key=lambda (f, t): t, reverse=True) 
        
    while trash.cfg["trash"]["autoclean"]["size"] <= trash.size:
        f, t = nft[-1]
        logging.debug("Removing {} to free bukkit({} bytes excess)".format(
            utils.addstamp(f, t), trash.size - trash.cfg["trash"]["autoclean"]["size"]))
        trash.rm(utils.addstamp(f, t))
        nft.pop(-1)
    return nft

def _cleanBySameCount(trash, file_time):
    nf = file_time[:]
    
    d = utils.file_timeToFileDict(nf)
    
    for key, val in d.iteritems():
        if len(val) > trash.cfg["trash"]["autoclean"]["samename"]:
            for dt in val[trash.cfg["trash"]["autoclean"]["samename"]:]:
                logging.debug("Removing {} becouse  there are a lot of same file".format(utils.addstamp(key, dt)))
                trash.rm(utils.addstamp(key, dt))
                nf.remove((key, dt))
    return nf
                

def autoclean(trash):
    waslocked = trash.locked
    if not waslocked:
        trash.lock()
    
    files = []
    for dirpath, dirnames, filenames in os.walk(trash.dirpath):
        files.extend([os.path.join(dirpath, f) for f in filenames])
        
    files = filter(lambda fn: not os.path.samefile(fn, trash.fullLockfile()), files)
            
    file_time = [utils.splitstamp(f) for f in files]
    file_time = _autocleanByDate(trash, file_time)
    file_time = _autocleanByTrashCount(trash, file_time)
    file_time = _autocleanByTrashSize(trash, file_time)
    file_time = _cleanBySameCount(trash, file_time)

    if not waslocked:
        trash.unlock()
