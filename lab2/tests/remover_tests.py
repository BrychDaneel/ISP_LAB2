# -*- coding: utf-8 -*-


import unittest
import os

import myrm
import myrm.stamp as stamp
import myrm.utils as utils
import myrm.config as config

from myrm.remover import Remover


class TrashTests(unittest.TestCase):
    
    def setUp(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.folder = os.path.join(script_dir,"test_folder","remover_test")
        self.files_folder = os.path.join(self.folder, "files")

        os.makedirs(self.files_folder)
        with open(os.path.join(self.files_folder, "a.txt"), "w") as f:
            f.write("1234567890")
        with open(os.path.join(self.files_folder, "b.txt"), "w") as f:
            f.write("12345")
        with open(os.path.join(self.files_folder, "c.png"), "w"):
            pass
        with open(os.path.join(self.files_folder, "d"), "w"):
            pass
        
        os.makedirs(os.path.join(self.files_folder, "e"))
        with open(os.path.join(self.files_folder, "e", "f.txt"), "w") as f:
            f.write("1234567890")
        with open(os.path.join(self.files_folder, "e", "g.txt"), "w") as f:
            f.write("12345")
        with open(os.path.join(self.files_folder, "e", "h.png"), "w"):
            pass
        with open(os.path.join(self.files_folder, "e", "j"), "w"):
            pass

        os.makedirs(os.path.join(self.files_folder, "e","k"))
        with open(os.path.join(self.files_folder, "e", "k","l.txt"), "w"):
            pass
        
        cfg = {
            "force" : False,
            "dryrun" : False,
            "interactive" : False,

            "auto_replace" : True,
            "allow_autoclean" : False,

            "trash" : {
                "directory" : os.path.join(self.folder, ".trash"),
                "lock_file" : "lock",

                "max_size" : 1024,
                "max_count": 10
            },

            "autoclean" : {
                "size" : 300,
                "count" : 10,
                "days" : 1,
                "same_count" : 2
            }
        }

        
        self.mrm = Remover(**cfg)
 
    def tearDown(self):
        for dirpath, dirnames, filenames in os.walk(self.folder, topdown=False):
            for element in filenames:
                element_path = os.path.join(dirpath, element)
                os.remove(element_path)
            if not os.path.samefile(dirpath, self.folder):
                os.rmdir(dirpath)
                
    def test_simple_remove(self):
        directory = self.files_folder
        path = os.path.join(directory, "a.txt")
        
        count, size, delta_files  = self.mrm.remove(path)
        self.assertEquals(count, 1)
        self.assertEquals(size, 10)
        
        files = list(utils.search(directory, "*", "*"))
        files = [os.path.relpath(f, directory) for f in files]
        files.sort()
        self.assertEquals(files, ["b.txt","c.png","d", "e"])

    def test_remove_mask1(self):
        directory = os.path.join(self.files_folder, "e")
        path = os.path.join(directory, "*")
        
        count, size, delta_files  = self.mrm.remove(path)
        self.assertEquals(count, 5)
        self.assertEquals(size, 15)
        
        files = list(utils.search(directory, "*", "*"))
        self.assertEquals(len(files), 0)
        
    def test_remove_mask2(self):
        directory = os.path.join(self.files_folder, "e")
        path = os.path.join(directory, "*.txt")
        
        count, size, delta_files  = self.mrm.remove(path)
        self.assertEquals(count, 2)
        self.assertEquals(size, 15)
        
        files = list(utils.search(directory, "*", "*"))
        files = [os.path.relpath(f, directory) for f in files]
        files.sort()
        self.assertEquals(files, ["h.png", "j", "k"])
        
    def test_remove_mask3(self):
        directory = os.path.join(self.files_folder)
        path = os.path.join(directory, "*.txt")
        
        count, size, delta_files  = self.mrm.remove(path, recursive=True)
        self.assertEquals(count, 5)
        self.assertEquals(size, 30)
        
        files = list(utils.search(directory, "*", "*", 
                                  recursive=True, find_all=True))
        files = [os.path.relpath(f, directory) for f in files]
        files.sort()
        self.assertEquals(files, ["c.png","d", "e",
                                  "e/h.png", "e/j", "e/k"])
        
    def test_remove_mask4(self):
        directory = os.path.join(self.files_folder)
        path = os.path.join(directory, "*.*")
        
        count, size, delta_files  = self.mrm.remove(path, recursive=True)
        self.assertEquals(count, 7)
        self.assertEquals(size, 30)
        
        files = list(utils.search(directory, "*", "*", 
                                  recursive=True, find_all=True))
        files = [os.path.relpath(f, directory) for f in files]
        files.sort()
        self.assertEquals(files, ["d", "e",
                                  "e/j", "e/k"])
        
    def test_remove_mask5(self):
        directory = os.path.join(self.files_folder)
        path = os.path.join(directory, "[ab].*")
        
        count, size, delta_files  = self.mrm.remove(path, recursive=True)
        self.assertEquals(count, 2)
        self.assertEquals(size, 15)
        
        files = list(utils.search(directory, "*", "*"))
        files = [os.path.relpath(f, directory) for f in files]
        files.sort()
        self.assertEquals(files, ["c.png","d", "e"])
    
    def test_remove_mask6(self):
        directory = os.path.join(self.files_folder)
        path = os.path.join(directory, "*")
        
        count, size, delta_files  = self.mrm.remove(path, recursive=True)
        self.assertEquals(count, 9)
        self.assertEquals(size, 30)
        
        files = list(utils.search(directory, "*", "*"))
        files = [os.path.relpath(f, directory) for f in files]
        files.sort()
        self.assertEquals(files, [])
        
    def test_restore1(self):
        directory = os.path.join(self.files_folder)
        path = os.path.join(directory, "a.txt")
        
        self.mrm.remove(path, recursive=True)
        count, size, delta_files  = self.mrm.restore(path, recursive=True)
        self.assertEquals(count, 1)
        self.assertEquals(size, 10)
        
        files = list(utils.search(directory, "*", "*"))
        files = [os.path.relpath(f, directory) for f in files]
        files.sort()
        self.assertEquals(files, ["a.txt", "b.txt","c.png","d", "e"])

    def test_restore2(self):
        directory = os.path.join(self.files_folder)
        path = os.path.join(directory, "*.txt")
        
        self.mrm.remove(path)
        count, size, delta_files  = self.mrm.restore(path)
        self.assertEquals(count, 2)
        self.assertEquals(size, 15)
        
        files = list(utils.search(directory, "*", "*"))
        files = [os.path.relpath(f, directory) for f in files]
        files.sort()
        self.assertEquals(files, ["a.txt", "b.txt","c.png","d", "e"])
    
    def test_restore3(self):
        directory = os.path.join(self.files_folder)
        path = os.path.join(directory, "[bc].*")
        
        self.mrm.remove(path)
        count, size, delta_files  = self.mrm.restore(path)
        self.assertEquals(count, 2)
        self.assertEquals(size, 5)
        
        files = list(utils.search(directory, "*", "*"))
        files = [os.path.relpath(f, directory) for f in files]
        files.sort()
        self.assertEquals(files, ["a.txt", "b.txt","c.png","d", "e"])
    
    def test_restore4(self):
        directory = os.path.join(self.files_folder)
        path = os.path.join(directory, "*")
        
        self.mrm.remove(path)
        count, size, delta_files  = self.mrm.restore(path)
        self.assertEquals(count, 9)
        self.assertEquals(size, 30)
        
        files = list(utils.search(directory, "", "*", recursive=True))
        files = [os.path.relpath(f, directory) for f in files]
        files.sort()
        self.assertEquals(files, ["a.txt", "b.txt","c.png","d", 
                                  "e/f.txt", "e/g.txt", "e/h.png", "e/j",
                                  "e/k/l.txt"])
    
    def test_restore5(self):
        directory = os.path.join(self.files_folder)
        path = os.path.join(directory, "*")
        
        self.mrm.remove(path)
        count, size, delta_files  = self.mrm.restore(path)
        self.assertEquals(count, 9)
        self.assertEquals(size, 30)
        
        files = list(utils.search(directory, "", "*", recursive=True))
        files = [os.path.relpath(f, directory) for f in files]
        files.sort()
        self.assertEquals(files, ["a.txt", "b.txt","c.png","d", 
                                  "e/f.txt", "e/g.txt", "e/h.png", "e/j",
                                  "e/k/l.txt"])
        
    def test_lst1(self):
        directory = os.path.join(self.files_folder)
        path = os.path.join(directory, "*")
        self.mrm.remove(path)
        
        files_vers = self.mrm.lst(path)
        files = [f[0] for f in files_vers]
        files = [os.path.relpath(f, directory) for f in files]

        self.assertEquals(files, ["a.txt", "b.txt","c.png","d", "e"])

    def test_lst2(self):
        directory = os.path.join(self.files_folder)
        path = os.path.join(directory, "*")
        self.mrm.remove(path)
        
        path = os.path.join(directory, "*.txt")
        files_vers = self.mrm.lst(path, recursive=True)
        files = [f[0] for f in files_vers]
        files = [os.path.relpath(f, directory) for f in files]

        self.assertEquals(files, ["a.txt", "b.txt", "e/f.txt", "e/g.txt", 
                                  "e/k/l.txt"])
        
    def test_lst3(self):
        directory = os.path.join(self.files_folder)
        path = os.path.join(directory, "*")
        self.mrm.remove(path)
        
        path = os.path.join(directory, "[bl]*")
        files_vers = self.mrm.lst(path, recursive=True)
        files = [f[0] for f in files_vers]
        files = [os.path.relpath(f, directory) for f in files]

        self.assertEquals(files, ["b.txt", "e/k/l.txt"])
        
    def test_lst4(self):
        directory = os.path.join(self.files_folder)
        path = os.path.join(directory, "[ab].txt")
        self.mrm.remove(path)
        
        path = os.path.join(directory, "[bl]*")
        files_vers = self.mrm.lst(path, recursive=True)
        files = [f[0] for f in files_vers]
        files = [os.path.relpath(f, directory) for f in files]

        self.assertEquals(files, ["b.txt"])

    def test_clean1(self):
        directory = os.path.join(self.files_folder)
        path = os.path.join(directory, "*")
        self.mrm.remove(path)
        
        self.mrm.clean(os.path.join(directory, "a.txt"))
        
        path = os.path.join(directory, "*")
        files_vers = self.mrm.lst(path)
        files = [f[0] for f in files_vers]
        files = [os.path.relpath(f, directory) for f in files]

        self.assertEquals(files, ["b.txt","c.png","d", "e"])
        
    def test_clean2(self):
        directory = os.path.join(self.files_folder)
        path = os.path.join(directory, "*")
        self.mrm.remove(path)
        
        self.mrm.clean(os.path.join(directory, "*.txt"))
        
        path = os.path.join(directory, "*")
        files_vers = self.mrm.lst(path)
        files = [f[0] for f in files_vers]
        files = [os.path.relpath(f, directory) for f in files]

        self.assertEquals(files, ["c.png","d", "e"])
        
    def test_clean3(self):
        directory = os.path.join(self.files_folder)
        path = os.path.join(directory, "*.txt")
        self.mrm.remove(path, recursive=True)
        
        self.mrm.clean(os.path.join(directory, "[af]*"), recursive=True)
        
        path = os.path.join(directory, "*.*")
        files_vers = self.mrm.lst(path, recursive=True)
        files = [f[0] for f in files_vers]
        files = [os.path.relpath(f, directory) for f in files]

        self.assertEquals(files, ["b.txt", "e/g.txt", "e/k/l.txt"])
