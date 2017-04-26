# -*- coding: utf-8 -*-


import unittest
import os

import myrm.trash
import myrm.stamp as stamp
import myrm.utils as utils
import myrm.config as config

from myrm.trash import Trash


class TrashTests(unittest.TestCase):
    
    def setUp(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.folder = os.path.join(script_dir,"test_folder","trash_test")
        self.files_folder = os.path.join(self.folder, "files")
        os.makedirs(self.files_folder)
        open(os.path.join(self.files_folder, "a.txt"), "w").close
        open(os.path.join(self.files_folder, "b.txt"), "w").close
        open(os.path.join(self.files_folder, "c.png"), "w").close
        open(os.path.join(self.files_folder, "d"), "w").close
        os.makedirs(os.path.join(self.files_folder, "e"))
        open(os.path.join(self.files_folder, "e", "f.txt"), "w").close
        open(os.path.join(self.files_folder, "e", "g.txt"), "w").close
        open(os.path.join(self.files_folder, "e", "h.png"), "w").close
        open(os.path.join(self.files_folder, "e", "j"), "w").close
        os.makedirs(os.path.join(self.files_folder, "e","k"))
        open(os.path.join(self.files_folder, "e", "k","l.txt"), "w").close
        
        cfg = config.get_default_config()
        cfg["force"] = False
        cfg["dryrun"] = False
        cfg["verbose"] = False
        cfg["interactive"] = False

        cfg["trash"]["dir"] = os.path.join(self.folder, ".trash")
        cfg["trash"]["lockfile"] = "lock"
        cfg["trash"]["allowautoclean"] = True

        cfg["trash"]["max"]["size"] = 1024
        cfg["trash"]["max"]["count"] = 5

        cfg["trash"]["autoclean"]["size"] = 300
        cfg["trash"]["autoclean"]["count"] = 10
        cfg["trash"]["autoclean"]["days"] = 1
        cfg["trash"]["autoclean"]["samename"] = 2
        
        self.trash = Trash(cfg)
        
    def tearDown(self):
        for dirpath, dirnames, filenames in os.walk(self.folder, topdown=False):
            for element in filenames:
                element_path = os.path.join(dirpath, element)
                os.remove(element_path)
            if not os.path.samefile(dirpath, self.folder):
                os.rmdir(dirpath)
            
    def test_int_ext(self):
        path = os.path.join(self.files_folder, "a.txt")
        path_int = self.trash.to_internal(path)
        path_ext = self.trash.to_external(path_int)
        path = os.path.abspath(path)
        self.assertNotEquals(path_int, path_ext)
        self.assertEquals(path_ext, path)
        
    def test_int_ext_dir(self):
        path = os.path.join(self.files_folder, "d")
        path_int = self.trash.to_internal(path)
        path_ext = self.trash.to_external(path_int)
        path = os.path.abspath(path)
        self.assertNotEquals(path_int, path_ext)
        self.assertEquals(path_ext, path)        
        
    def test_lock(self):
        lock_file = self.trash.lock_file_path()
        self.assertFalse(os.path.exists(lock_file))
        self.trash.lock()
        self.assertTrue(os.path.exists(lock_file))
        self.trash.unlock()
        self.assertFalse(os.path.exists(lock_file))

    def test_double_lock(self):
        lock_file = self.trash.lock_file_path()
        self.trash.lock()
        with self.assertRaises(AssertionError):
            self.trash.lock()

    def test_simple(self):
        directory = os.path.join(self.files_folder, "e")
        path = os.path.join(directory, "f.txt")
        self.trash.lock()
        
        self.trash.add(path)
        files = list(utils.search(directory, "*", "*"))
        files = [os.path.relpath(f, directory) for f in files]
        files.sort()
        self.assertEquals(files, ["g.txt", "h.png", "j", "k"])
        
        self.trash.restore(path)
        files = list(utils.search(directory, "*", "*"))
        files = [os.path.relpath(f, directory) for f in files]
        files.sort()
        self.assertEquals(files, ["f.txt", "g.txt", "h.png", "j", "k"])

        self.trash.unlock()
        
    def test_simple_clear(self):
        directory = os.path.join(self.files_folder, "e")
        path = os.path.join(directory, "f.txt")
        self.trash.lock()  
        
        self.trash.add(path)
        self.trash.remove(path)
        
        files = list(utils.search(directory, "*", "*"))
        files = [os.path.relpath(f, directory) for f in files]
        files.sort()
        self.assertEquals(files, ["g.txt", "h.png", "j", "k"])
        
        files = stamp.get_versions_list(self.trash.to_internal(path))
        self.assertTrue(len(files) == 0)
        
        self.trash.unlock()
        
        
    def test_dir(self):
        directory = self.files_folder
        path = os.path.join(directory, "e")
        self.trash.lock()
        
        self.trash.add(path)
        files = list(utils.search(directory, "*", "*"))
        files = [os.path.relpath(f, directory) for f in files]
        files.sort()
        self.assertEquals(files, ["a.txt","b.txt","c.png","d"])
        
        self.trash.restore(path)
        files = list(utils.search(directory, "", "*", recursive=True))
        files = [os.path.relpath(f, directory) for f in files]
        files.sort()
        self.assertEquals(files, ["a.txt","b.txt","c.png","d", 
                                  "e/f.txt", "e/g.txt", "e/h.png", "e/j",
                                  "e/k/l.txt"])

        self.trash.unlock()
        
    def test_remove_dir(self):
        directory = self.files_folder
        path = os.path.join(directory, "e")
        self.trash.lock()
        
        self.trash.add(path)
        self.trash.remove(path)
        files = list(utils.search(directory, "*", "*"))
        files = [os.path.relpath(f, directory) for f in files]
        files.sort()
        self.assertEquals(files, ["a.txt","b.txt","c.png","d"])

        self.assertFalse(os.path.exists(self.trash.to_internal(path)))

        self.trash.unlock()
        
        
    def test_multi(self):
        directory = self.files_folder
        path = os.path.join(directory, "a.txt")
        self.trash.lock()
        
        self.trash.add(path)
        
        f = open(path, "w")
        f.write("1th\n")
        f.close();
        self.trash.add(path)
        
        f = open(path, "w")
        f.write("2th\n")
        f.close();
        self.trash.add(path)
        
        f = open(path, "w")
        f.write("3th\n")
        f.close();
        self.trash.add(path)
        
        f = open(path, "w")
        f.write("4th\n")
        f.close();
        self.trash.add(path)
        
        self.trash.restore(path, how_old=3)
        f = open(path, "r")
        line = f.read();
        self.assertEquals(line, "1th\n")        
        
        os.remove(path);
        
        self.trash.restore(path, how_old=0)
        f = open(path, "r")
        line = f.read();
        self.assertEquals(line, "4th\n")        

        self.trash.unlock()

    def test_multi_remove(self):
        directory = self.files_folder
        path = os.path.join(directory, "a.txt")
        self.trash.lock()
        
        self.trash.add(path)
        
        f = open(path, "w")
        f.write("1th\n")
        f.close();
        self.trash.add(path)
        
        f = open(path, "w")
        f.write("2th\n")
        f.close();
        self.trash.add(path)
        
        f = open(path, "w")
        f.write("3th\n")
        f.close();
        self.trash.add(path)
        
        self.trash.remove(path, how_old=1)
        
        self.trash.restore(path, how_old=1)
        f = open(path, "r")
        line = f.read();
        self.assertEquals(line, "1th\n")      
        
        self.trash.remove(path, how_old=-1)
        
        path = self.trash.to_internal(path)
        self.assertTrue(len(stamp.get_versions_list(path)) == 0)

        self.trash.unlock()
        
