# -*- coding: utf-8 -*- 

class Config(object):
    
    def __init__(self):
        self.trash_dir = "./trash"
        self.trash_lockfile = "lock"
        
        self.force = False
        self.dryrun = True
        self.verbose = True
        self.interactive = False
        
