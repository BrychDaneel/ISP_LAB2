# -*- coding: utf-8 -*-


import unittest
import os
import myrm.utils as utils


class SearchTests(unittest.TestCase):
    
    def setUp(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.folder = os.path.join(script_dir,"test_folder","utils_test")
    
    def test_1(self):
        files = utils.search(self.folder, "", "*", 
                             recursive=False, find_all=False)
        files = list(files)
        files = [os.path.relpath(f, self.folder) for f in files]
        files.sort();
        self.assertEqual(files, ["a.txt", "b.txt", "e.png"])
        
    def test_2(self):
        files = utils.search(self.folder, "*", "*", 
                             recursive=False, find_all=False)
        files = list(files)
        files = [os.path.relpath(f, self.folder) for f in files]
        files.sort();
        self.assertEqual(files, ["a.txt", "b.txt", "c", "e.png"])
        
    def test_recursive(self):
        files = utils.search(self.folder, "", "*", 
                             recursive=True, find_all=False)
        files = list(files)
        files = [os.path.relpath(f, self.folder) for f in files]
        files.sort();
        ans = ["a.txt", "b.txt", os.path.join("c","d.txt"), "e.png"]
        self.assertEqual(files, ans)
        
    def test_find_all(self):
        files = utils.search(self.folder, "*", "*", 
                             recursive=True, find_all=True)
        files = list(files)
        files = [os.path.relpath(f, self.folder) for f in files]
        files.sort()
        ans = ["a.txt", "b.txt", "c", os.path.join("c","d.txt"), "e.png"]
        self.assertEqual(files, ans)
        
    def test_mask1(self):
        files = utils.search(self.folder, "", "*.txt", 
                             recursive=True, find_all=False)
        files = list(files)
        files = [os.path.relpath(f, self.folder) for f in files]
        files.sort()
        ans = ["a.txt", "b.txt", os.path.join("c","d.txt")]
        self.assertEqual(files, ans)
        
    def test_mask2(self):
        files = utils.search(self.folder, "", "[ab].txt", 
                             recursive=True, find_all=False)
        files = list(files)
        files = [os.path.relpath(f, self.folder) for f in files]
        files.sort()
        ans = ["a.txt", "b.txt"]
        self.assertEqual(files, ans)
   
   
class SplitPathTests(unittest.TestCase):   
    
    def setUp(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.folder = os.path.join(script_dir,"test_folder","utils_test")
        
    def test_1(self):
        result = utils.split_path("a/b.txt")
        ans = ["", "a", "b.txt"]
        self.assertEqual(result, ans)

    def test_2(self):
        result = utils.split_path("/a/b.txt")
        ans = ["/", "a", "b.txt"]
        self.assertEqual(result, ans)
    
    def test_2(self):
        result = utils.split_path("./a/b.txt")
        ans = ["", ".", "a", "b.txt"]
        self.assertEqual(result, ans)
        
        
class FilesCountTests(unittest.TestCase):
    
    def setUp(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.folder = os.path.join(script_dir,"test_folder","utils_test")
        
    def test_1(self):
        ans = utils.files_count(os.path.join(self.folder, "c"))
        result = 1
        self.assertEqual(result, ans)
    
    def test_1(self):
        result = 4
        ans = utils.files_count(os.path.join(self.folder))
        self.assertEqual(result, ans)
        
        
class SizeTests(unittest.TestCase):
    
    def setUp(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.folder = os.path.join(script_dir,"test_folder","utils_test")
        
    def test_1(self):
        ans = 10
        result = utils.files_size(os.path.join(self.folder, "b.txt"))
        self.assertEqual(result, ans)
        
    def test_2(self):
        ans = 20
        result = utils.files_size(os.path.join(self.folder, "c", "d.txt"))
        self.assertEqual(result, ans)        
    
    def test_dir1(self):
        ans = 20
        result = utils.files_size(os.path.join(self.folder, "c"))
        self.assertEqual(result, ans)
    
    def test_dir2(self):
        ans = 34
        result = utils.files_size(os.path.join(self.folder))
        self.assertEqual(result, ans) 
