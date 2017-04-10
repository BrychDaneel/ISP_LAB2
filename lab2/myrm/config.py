# -*- coding: utf-8 -*- 

class Config(object):
    
    def __init__(self):
        self.trash_dir = "./trash"
        self.trash_lockfile = "lock"
        self.trash_maxsize = 1024
        self.trash_maxelems = 5
        self.trash_days = 1
        self.trash_maxsame = 2
        
        self.force = False
        self.dryrun = True
        self.verbose = True
        self.interactive = False
        
