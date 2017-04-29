# -*- coding: utf-8 -*-


import unittest
import os
import datetime

import myrm
import myrm.stamp as stamp
import myrm.utils as utils
import myrm.config as config
import myrm.autoclean as autoclean

from myrm.trash import Trash


class TrashTests(unittest.TestCase):
    
    def setUp(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.folder = os.path.join(script_dir,"test_folder","autoclean_test")
        self.files_folder = os.path.join(self.folder, "files")
        
        os.makedirs(self.files_folder)
        open(os.path.join(self.files_folder, "a.txt"), "w").close
        open(os.path.join(self.files_folder, "b.txt"), "w").close
        open(os.path.join(self.files_folder, "c.png"), "w").close
        os.makedirs(os.path.join(self.files_folder, "e"))
        open(os.path.join(self.files_folder, "e", "f.txt"), "w").close
        open(os.path.join(self.files_folder, "e", "g.txt"), "w").close
        open(os.path.join(self.files_folder, "e", "h.png"), "w").close
        os.makedirs(os.path.join(self.files_folder, "e","k"))
        open(os.path.join(self.files_folder, "e", "k","l.txt"), "w").close
        
        path = os.path.join(self.files_folder, "a.txt")
        f = open(path, "w")
        f.write("1234567890")
        f.close()
        
        path = os.path.join(self.files_folder, "b.txt")
        f = open(path, "w")
        f.write("12345")
        f.close()
        
        
        path = os.path.join(self.files_folder, "e", "f.txt")
        f = open(path, "w")
        f.write("1234567890")
        f.close()
        
        path = os.path.join(self.files_folder, "e", "g.txt")
        f = open(path, "w")
        f.write("12345")
        f.close()
        
        cfg = config.get_default_config()
        cfg["force"] = False
        cfg["dryrun"] = False
        cfg["verbose"] = False
        cfg["interactive"] = False

        cfg["trash"]["dir"] = os.path.join(self.folder, ".trash")
        cfg["trash"]["lockfile"] = "lock"
        cfg["trash"]["allowautoclean"] = True

        cfg["trash"]["max"]["size"] = 1024
        cfg["trash"]["max"]["count"] = 100
        
        self.trash = Trash(cfg)
        self.trash.lock()
        self.trash.add(os.path.join(self.files_folder, "a.txt"))
        self.trash.add(os.path.join(self.files_folder, "b.txt"))
        self.trash.add(os.path.join(self.files_folder, "c.png"))
        self.trash.add(os.path.join(self.files_folder, "e", "f.txt"))
        self.trash.add(os.path.join(self.files_folder, "e", "g.txt"))
        self.trash.add(os.path.join(self.files_folder, "e", "h.png"))
        self.trash.add(os.path.join(self.files_folder, "e", "k","l.txt"))
        
        path = os.path.join(self.files_folder, "a.txt")
        for i in xrange(1,5):
            open(path, "w").close
            self.trash.add(path)
            
        self.trash.unlock()
        
    def tearDown(self):
        for dirpath, dirnames, filenames in os.walk(self.folder, topdown=False):
            for element in filenames:
                element_path = os.path.join(dirpath, element)
                os.remove(element_path)
            if not os.path.samefile(dirpath, self.folder):
                os.rmdir(dirpath)
                
    def test_size(self):
        directory = self.files_folder
        self.trash.cfg["trash"]["autoclean"]["size"] = 6
        self.trash.cfg["trash"]["autoclean"]["count"] = 20
        self.trash.cfg["trash"]["autoclean"]["days"] = 1
        self.trash.cfg["trash"]["autoclean"]["samename"] = 10
        autoclean.autoclean(self.trash)
        
        path = os.path.join(directory, "*.*")
        
        files_vers = self.trash.search(path, recursive=True)
        files = []
        for path in files_vers:
            for dtime in files_vers[path]:
                files.append(path)
        files.sort()
        files = [os.path.relpath(f, directory) for f in files]
        
        self.assertEquals(files, ['a.txt', 'a.txt', 'a.txt', 'a.txt', 
                                  'e/g.txt', 'e/h.png', 'e/k/l.txt'])

    def test_count(self):
        directory = self.files_folder
        self.trash.cfg["trash"]["autoclean"]["size"] = 100
        self.trash.cfg["trash"]["autoclean"]["count"] = 4
        self.trash.cfg["trash"]["autoclean"]["days"] = 1
        self.trash.cfg["trash"]["autoclean"]["samename"] = 10
        autoclean.autoclean(self.trash)
        
        path = os.path.join(directory, "*.*")
        files_vers = self.trash.search(path, recursive=True)
        files = []
        for path in files_vers:
            for dtime in files_vers[path]:
                files.append(path)
        files.sort()
        files = [os.path.relpath(f, directory) for f in files]
        
        self.assertEquals(files, ['a.txt', 'a.txt', 'a.txt'])
    
    def test_same(self):
        directory = self.files_folder
        self.trash.cfg["trash"]["autoclean"]["size"] = 100
        self.trash.cfg["trash"]["autoclean"]["count"] = 100
        self.trash.cfg["trash"]["autoclean"]["days"] = 1
        self.trash.cfg["trash"]["autoclean"]["samename"] = 3
        autoclean.autoclean(self.trash)
        
        path = os.path.join(directory, "*.*")
        files_vers = self.trash.search(path, recursive=True)
        files = []
        for path in files_vers:
            for dtime in files_vers[path]:
                files.append(path)
        files.sort()
        files = [os.path.relpath(f, directory) for f in files]
        
        self.assertEquals(files, ['a.txt', 'a.txt', 'b.txt', 'c.png',
                                  'e/f.txt', 'e/g.txt', 'e/h.png', 
                                  'e/k/l.txt'])
        
        
    def test_old(self):
        directory = self.files_folder
        self.trash.cfg["trash"]["autoclean"]["size"] = 100
        self.trash.cfg["trash"]["autoclean"]["count"] = 100
        self.trash.cfg["trash"]["autoclean"]["days"] = 1
        self.trash.cfg["trash"]["autoclean"]["samename"] = 10
        
        path_int = os.path.join(self.files_folder, "b.txt")
        path_int = self.trash.to_internal(path_int)
        path_stamp = stamp.add_stamp(path_int, datetime.datetime(1990, 1, 1))
        open(path_stamp, "w").close()
        
        autoclean.autoclean(self.trash)
        
        path = os.path.join(directory, "*.*")
        files_vers = self.trash.search(path, recursive=True)
        files = []
        for path in files_vers:
            for dtime in files_vers[path]:
                files.append(path)
        files.sort()
        files = [os.path.relpath(f, directory) for f in files]
        
        self.assertEquals(files, ['a.txt', 'a.txt', 'a.txt', 'a.txt', 'a.txt',
                                  'b.txt', 'c.png',
                                  'e/f.txt', 'e/g.txt', 'e/h.png', 
                                  'e/k/l.txt'])
        
        path = stamp.get_version(path_int, 0)
        f = open(path, "r")
        line = f.read() 
        f.close()
        self.assertEquals(line, "12345")
        
        
    def test_count_same(self):
        directory = self.files_folder
        self.trash.cfg["trash"]["autoclean"]["size"] = 100
        self.trash.cfg["trash"]["autoclean"]["count"] = 5
        self.trash.cfg["trash"]["autoclean"]["days"] = 1
        self.trash.cfg["trash"]["autoclean"]["samename"] = 2
        
        autoclean.autoclean(self.trash)
        
        path = os.path.join(directory, "*.*")
        files_vers = self.trash.search(path, recursive=True)
        files = []
        for path in files_vers:
            for dtime in files_vers[path]:
                files.append(path)
        files.sort()
        files = [os.path.relpath(f, directory) for f in files]
        
        self.assertEquals(files, ['a.txt', 'e/g.txt', 'e/h.png', 'e/k/l.txt'])
