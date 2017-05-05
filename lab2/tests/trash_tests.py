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
            "directory" : os.path.join(self.folder, ".trash"),
            "lock_file" : "lock",

            "max_size" : 300,
            "max_count": 10
        }
        
        self.trash = Trash(**cfg)
        
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
        
    def test_ext_invalid(self):
        lock_file = self.trash.get_lock_file_path()
        self.trash.lock()
        with self.assertRaises(ValueError):
            self.trash.to_external("/a/b.txt")
            
    def test_lock(self):
        lock_file = self.trash.get_lock_file_path()
        self.assertFalse(os.path.exists(lock_file))
        self.trash.set_lock()
        self.assertTrue(os.path.exists(lock_file))
        self.trash.unset_lock()
        self.assertFalse(os.path.exists(lock_file))

    def test_double_lock(self):
        self.trash.set_lock()
        with self.assertRaises(IOError):
            self.trash.set_lock()

    def test_simple(self):
        directory = os.path.join(self.files_folder, "e")
        path = os.path.join(directory, "f.txt")
        
        with self.trash.lock():
            count, size  = self.trash.add(path)
            self.assertEquals(count, 1)
            self.assertEquals(size, 10)
            
            files = list(utils.search(directory, "*", "*"))
            files = [os.path.relpath(f, directory) for f in files]
            files.sort()
            self.assertEquals(files, ["g.txt", "h.png", "j", "k"])
            
            count, size  = self.trash.restore(path)
            self.assertEquals(count, 1)
            self.assertEquals(size, 10)
            
            files = list(utils.search(directory, "*", "*"))
            files = [os.path.relpath(f, directory) for f in files]
            files.sort()
            self.assertEquals(files, ["f.txt", "g.txt", "h.png", "j", "k"])

        
        
    def test_simple_count_limit(self):
        directory = os.path.join(self.files_folder)
        path = os.path.join(directory, "a.txt")
        
        self.trash.max_count = 5
        with self.trash.lock():
            for i in xrange(1,6):
                self.trash.add(path)
                open(path, "w").close
                
            with self.assertRaises(myrm.trash.LimitExcessException):
                self.trash.add(path)
        
 
    def test_simple_size_limit(self):
        directory = os.path.join(self.files_folder)
        path = os.path.join(directory, "a.txt")
        
        self.trash.max_size = 15
        
        with self.trash.lock(): 
            
            with open(path, "w") as f:
                f.write("1234567890")

            self.trash.add(path)
            
            with open(path, "w") as f:
                f.write("123456")
            
            with self.assertRaises(myrm.trash.LimitExcessException):
                self.trash.add(path)
        
    def test_simple_clear(self):
        directory = os.path.join(self.files_folder, "e")
        path = os.path.join(directory, "f.txt")
        
        with self.trash.lock():  
            count, size = self.trash.add(path)
            self.assertEquals(count, 1)
            self.assertEquals(size, 10)
            
            count, size = self.trash.remove(path)
            self.assertEquals(count, 1)
            self.assertEquals(size, 10)
            
            files = list(utils.search(directory, "*", "*"))
            files = [os.path.relpath(f, directory) for f in files]
            files.sort()
            self.assertEquals(files, ["g.txt", "h.png", "j", "k"])
            
            files = stamp.get_versions_list(self.trash.to_internal(path))
            self.assertTrue(len(files) == 0)
        
        
    def test_dir(self):
        directory = self.files_folder
        path = os.path.join(directory, "e")
        
        with self.trash.lock():
            count, size = self.trash.add(path)
            self.assertEquals(count, 5)
            self.assertEquals(size, 15)
            
            files = list(utils.search(directory, "*", "*"))
            files = [os.path.relpath(f, directory) for f in files]
            files.sort()
            self.assertEquals(files, ["a.txt","b.txt","c.png","d"])
            
            count, size = self.trash.restore(path)
            self.assertEquals(count, 5)
            self.assertEquals(size, 15)
            
            files = list(utils.search(directory, "", "*", recursive=True))
            files = [os.path.relpath(f, directory) for f in files]
            files.sort()
            self.assertEquals(files, ["a.txt","b.txt","c.png","d", 
                                      "e/f.txt", "e/g.txt", "e/h.png", "e/j",
                                      "e/k/l.txt"])
        
    def test_remove_dir(self):
        directory = self.files_folder
        path = os.path.join(directory, "e")
        
        with self.trash.lock():
            count, size = self.trash.add(path)
            self.assertEquals(count, 5)
            self.assertEquals(size, 15)
            
            count, size = self.trash.remove(path)
            self.assertEquals(count, 5)
            self.assertEquals(size, 15)
            
            files = list(utils.search(directory, "*", "*"))
            files = [os.path.relpath(f, directory) for f in files]
            files.sort()
            
            self.assertEquals(files, ["a.txt","b.txt","c.png","d"])
            self.assertFalse(os.path.exists(self.trash.to_internal(path)))        
        
    def test_multi(self):
        directory = self.files_folder
        path = os.path.join(directory, "a.txt")
        
        with self.trash.lock():
        
            self.trash.add(path)
            
            with open(path, "w") as f:
                f.write("1th\n")
            self.trash.add(path)
            
            with open(path, "w") as f:
                f.write("2th\n")
            self.trash.add(path)
            
            with open(path, "w") as f:
                f.write("3th\n")
            self.trash.add(path)
            
            with open(path, "w") as f:
                f.write("4th\n")
            self.trash.add(path)
            
            count, size = self.trash.restore(path, how_old=3)
            self.assertEquals(count, 1)
            self.assertEquals(size, 4)
            f = open(path, "r")
            line = f.read();
            self.assertEquals(line, "1th\n")        
            
            os.remove(path);
            
            count, size = self.trash.restore(path, how_old=0)
            self.assertEquals(count, 1)
            self.assertEquals(size, 4)
            f = open(path, "r")
            line = f.read();
            self.assertEquals(line, "4th\n")        


    def test_multi_remove(self):
        directory = self.files_folder
        path = os.path.join(directory, "a.txt")
        
        with self.trash.lock():
        
            self.trash.add(path)
            
            with open(path, "w") as f:
                f.write("1th\n")
            self.trash.add(path)
            
            with open(path, "w") as f:
                f.write("2th\n")
            self.trash.add(path)
            
            with open(path, "w") as f:
                f.write("3th\n")
            self.trash.add(path)
            
            count, size = self.trash.remove(path, how_old=1)
            self.assertEquals(count, 1)
            self.assertEquals(size, 4)
            
            self.trash.restore(path, how_old=1)
            f = open(path, "r")
            line = f.read();
            self.assertEquals(line, "1th\n")      
            
            count, size = self.trash.remove(path)
            self.assertEquals(count, 2)
            self.assertEquals(size, 14)
            
            path = self.trash.to_internal(path)
            self.assertTrue(len(stamp.get_versions_list(path)) == 0)

        
    def test_search1(self):
        directory = self.files_folder
        path = os.path.join(directory, "*")
        files = list(self.trash.search(path))
        self.assertEquals(files, [])
        
    def test_search2(self):
        directory = self.files_folder
        with self.trash.lock():
            self.trash.add(os.path.join(directory, "a.txt"))
            path = os.path.join(directory, "*")
            files = list(self.trash.search(path))
            files = [os.path.relpath(f, directory) for f in files]
            files.sort()
            self.assertEquals(files, ["a.txt"])    
        
    def test_search3(self):
        directory = self.files_folder
        with self.trash.lock():
            self.trash.add(os.path.join(directory, "a.txt"))
            self.trash.add(os.path.join(directory, "b.txt"))
            path = os.path.join(directory, "*")
            files = list(self.trash.search(path))
            files = [os.path.relpath(f, directory) for f in files]
            files.sort()
            self.assertEquals(files, ["a.txt", "b.txt"])    
        
    def test_search4(self):
        directory = self.files_folder
        with self.trash.lock():
            self.trash.add(os.path.join(directory, "a.txt"))
            self.trash.add(os.path.join(directory, "c.png"))
            path = os.path.join(directory, "*.txt")
            files = list(self.trash.search(path))
            files = [os.path.relpath(f, directory) for f in files]
            files.sort()
            self.assertEquals(files, ["a.txt"])    
        
    def test_search5(self):
        directory = self.files_folder
        with self.trash.lock():
            self.trash.add(os.path.join(directory, "a.txt"))
            self.trash.add(os.path.join(directory, "c.png"))
            self.trash.add(os.path.join(directory, "e/f.txt"))
            
            path = os.path.join(directory, "*.txt")
            files = list(self.trash.search(path, recursive=True))
            files = [os.path.relpath(f, directory) for f in files]
            files.sort()
            self.assertEquals(files, ["a.txt", "e/f.txt"])    
            
            path = os.path.join(directory, "*.png")
            files = list(self.trash.search(path, recursive=True))
            files = [os.path.relpath(f, directory) for f in files]
            files.sort()
            self.assertEquals(files, ["c.png"])
    
    def test_search6(self):
        directory = self.files_folder
        with self.trash.lock():
            self.trash.add(os.path.join(directory, "a.txt"))
            self.trash.add(os.path.join(directory, "b.txt"))
            self.trash.add(os.path.join(directory, "c.png"))
            self.trash.add(os.path.join(directory, "d"))
            
            path = os.path.join(directory, "[ac].*")
            files = list(self.trash.search(path, recursive=True))
            files = [os.path.relpath(f, directory) for f in files]
            files.sort()
            self.assertEquals(files, ["a.txt", "c.png"])
        
    def test_search7(self):
        directory = self.files_folder
        
        with self.trash.lock():
            self.trash.add(os.path.join(directory, "a.txt"))
            self.trash.add(os.path.join(directory, "c.png"))
            self.trash.add(os.path.join(directory, "e/f.txt"))
            
            path = os.path.join(directory, "*")
            files = list(self.trash.search(path, recursive=True, find_all=True))
            files = [os.path.relpath(f, directory) for f in files]
            files.sort()
            self.assertEquals(files, ["a.txt", "c.png", "e", "e/f.txt"])    
