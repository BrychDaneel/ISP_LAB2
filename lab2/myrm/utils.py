# -*- coding: utf-8 -*- 
import os
import re
import datetime


def ask(filename):
    u_ans = raw_input("Perfom operation to {} ? [Y/n]".format(filename)).lower()
    return  not u_ans or u_ans == 'y'

def acsess(targ, msg, cfg):
    if cfg.interactive and not ask(targ):
        return False
    if cfg.verbose:
        print(msg)
    if cfg.dryrun:
        return False
    return True

        

def search(path, dirmask, filemask, recursive=False):

        fm = re.compile(filemask)
        dm = re.compile(dirmask)
        print(path, dirmask, filemask, recursive)
        for f in os.listdir(path):
            full = os.path.join(path, f)
            isdir = os.path.isdir(full)
            if  not isdir:
                if  fm.match(f):
                    yield (isdir, full)
            else:
                if dm.match(f):
                    yield (isdir, full)
                elif recursive:
                    for match in search(full, dirmask, filemask, recursive):
                        yield match    
                
                    
                    
def timestamp():
    d = datetime.datetime.utcnow()
    return d.toordinal()*24*60*60 + d.hour*60*60 + d.minute * 60 + d.second, d.microsecond
    
