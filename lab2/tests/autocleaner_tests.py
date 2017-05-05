# -*- coding: utf-8 -*-


import unittest
import os
import datetime

import myrm
import myrm.stamp as stamp
import myrm.utils as utils
import myrm.config as config

from myrm.trash import Trash
from myrm.autocleaner import Autocleaner


class TrashTests(unittest.TestCase):
    
    def setUp(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.folder = os.path.join(script_dir,"test_folder","autoclean_test")
        self.files_folder = os.path.join(self.folder, "files")
        
        os.makedirs(self.files_folder)
        with open(os.path.join(self.files_folder, "a.txt"), "w") as f:
            f.write("1234567890")
        with open(os.path.join(self.files_folder, "b.txt"), "w") as f:
            f.write("12345")
        with open(os.path.join(self.files_folder, "c.png"), "w"):
            pass

        os.makedirs(os.path.join(self.files_folder, "e"))
        with open(os.path.join(self.files_folder, "e", "f.txt"), "w") as f:
            f.write("1234567890")
        with open(os.path.join(self.files_folder, "e", "g.txt"), "w") as f:
            f.write("12345")
        with open(os.path.join(self.files_folder, "e", "h.png"), "w"):
            pass

        os.makedirs(os.path.join(self.files_folder, "e","k"))
        with open(os.path.join(self.files_folder, "e", "k","l.txt"), "w"):
            pass

        trash_cfg = {
            "directory" : os.path.join(self.folder, ".trash"),
            "lock_file" : "lock",

            "max_size" : 1024,
            "max_count": 100
        }
        
        self.trash = Trash(**trash_cfg)

        with self.trash.lock():
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
    
        self.autocleaner = Autocleaner(self.trash)
        
    def tearDown(self):
        for dirpath, dirnames, filenames in os.walk(self.folder, topdown=False):
            for element in filenames:
                element_path = os.path.join(dirpath, element)
                os.remove(element_path)
            if not os.path.samefile(dirpath, self.folder):
                os.rmdir(dirpath)
                
    def test_size(self):
        directory = self.files_folder
        self.autocleaner.size = 6
        self.autocleaner.count = 20
        self.autocleaner.days = 1
        self.autocleaner.same_count = 10

        self.autocleaner.autoclean()
        
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
        self.autocleaner.size = 100
        self.autocleaner.count = 4
        self.autocleaner.days = 1
        self.autocleaner.same_count = 10

        self.autocleaner.autoclean()
        
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
        self.autocleaner.size = 100
        self.autocleaner.count = 100
        self.autocleaner.days = 1
        self.autocleaner.same_count = 3

        self.autocleaner.autoclean()
        
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
        self.autocleaner.size = 100
        self.autocleaner.count = 100
        self.autocleaner.days = 1
        self.autocleaner.same_count = 10
        
        path_int = os.path.join(self.files_folder, "b.txt")
        path_int = self.trash.to_internal(path_int)
        path_stamp = stamp.add_stamp(path_int, datetime.datetime(1990, 1, 1))
        open(path_stamp, "w").close()
        
        self.autocleaner.autoclean()
        
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
        self.autocleaner.size = 100
        self.autocleaner.count = 5
        self.autocleaner.days = 1
        self.autocleaner.same_count = 2
        
        self.autocleaner.autoclean()
        
        path = os.path.join(directory, "*.*")
        files_vers = self.trash.search(path, recursive=True)
        files = []
        for path in files_vers:
            for dtime in files_vers[path]:
                files.append(path)
        files.sort()
        files = [os.path.relpath(f, directory) for f in files]
        
        self.assertEquals(files, ['a.txt', 'e/g.txt', 'e/h.png', 'e/k/l.txt'])
