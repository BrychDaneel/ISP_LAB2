# -*- coding: utf-8 -*- 
import os
import re

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


def fileToReg(f):
    return f

def parceDirMsk(filename):
        isdir = os.path.isdir(filename) 
        if isdir:
            path = filename 
            filename = '.*'
        else:
            path = '.'
            dr, filename = os.path.split(filename)
            path = os.path.join(path, dr)
        
        filemask = fileToReg(filename)
        return (isdir, path, filemask)
        

def maskWalk(filename, recursive=False):
        
        isdir, path, filemask = parceDirMsk(filename)
        assert(not recursive or isdir)
        
        pat = re.compile(filemask)
        
        if recursive:
            for d, dirs, files in os.walk(path, topdown=False):
                for f in files:
                    f = os.path.join(d, f)
                    if pat.match(f):
                        yield (False, f)
                if filemask == '.*':
                    yield (True, d)
        else:
            for f in os.listdir(path):
                full = os.path.join(path, f)
                if not os.path.isdir(full) and pat.match(f):
                    yield (False, full)
