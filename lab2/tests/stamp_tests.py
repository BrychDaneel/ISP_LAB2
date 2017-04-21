# -*- coding: utf-8 -*-


import unittest
import os
import datetime
import myrm.utils as utils
import myrm.stamp as stamp


class StampTests(unittest.TestCase):
    
    def setUp(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.folder = os.path.join(script_dir, "test_folder", "stamp_test")
        
    def tearDown(self):
        for path in os.listdir(self.folder):
            os.unlink(os.path.join(self.folder, path))
            
    def test_trasnit1(self):
        path = "a/b.txt"
        dtime = datetime.datetime.now()
        new_path = stamp.add_stamp(path, dtime)
        res_path, res_dtime = stamp.split_stamp(new_path)
        self.assertEqual((path, dtime), (res_path, res_dtime))
    
    def test_none1(self):
        path = "/a/b.txt"
        res_path, res_dtime = stamp.split_stamp(path)
        self.assertEqual((path, None), (res_path, res_dtime))

    def test_none2(self):
        path = "/a/b"
        res_path, res_dtime = stamp.split_stamp(path)
        self.assertEqual((path, None), (res_path, res_dtime))
    
    def test_mask(self):
        path = os.path.join(self.folder, "a.txt")
        dtime = datetime.datetime.now()
        new_path = stamp.add_stamp(path, dtime)
        open(new_path, "w").close()
        mask = stamp.extend_mask_by_stamp(path)
        dircetory, file_mask = os.path.split(mask) 
        files = utils.search(dircetory, "", file_mask)
        files = [stamp.split_stamp(f)[0] for f in files]
        self.assertEqual(files, [path])
        
    def test_mask_time_big(self):
        path1 = os.path.join(self.folder, "a.txt")
        path2 = os.path.join(self.folder, "b.txt")
        path3 = os.path.join(self.folder, "c")
        
        dtime = datetime.datetime.now()
        
        new_path1 = stamp.add_stamp(path1, dtime)
        new_path2 = stamp.add_stamp(path2, dtime)
        new_path3 = stamp.add_stamp(path3, dtime)
        
        open(new_path1, "w").close()
        open(new_path2, "w").close()
        open(new_path3, "w").close()
        
        mask1 = stamp.extend_mask_by_stamp(path1)
        mask2 = stamp.extend_mask_by_stamp(path2)
        mask3 = stamp.extend_mask_by_stamp(path3)
        
        dircetory1, file_mask1 = os.path.split(mask1) 
        dircetory2, file_mask2 = os.path.split(mask2)
        dircetory3, file_mask3 = os.path.split(mask3)
        
        files1 = utils.search(dircetory1, "", file_mask1)
        files1 = [stamp.split_stamp(f)[0] for f in files1]
        files2 = utils.search(dircetory2, "", file_mask2)
        files2 = [stamp.split_stamp(f)[0] for f in files2]
        files3 = utils.search(dircetory3, "", file_mask3)
        files3 = [stamp.split_stamp(f)[0] for f in files3]
        
        self.assertEqual(files1, [path1])
        self.assertEqual(files2, [path2])
        self.assertEqual(files3, [path3])
        
    def test_dict(self):
        dtime1 = datetime.datetime.now()
        dtime2 = datetime.datetime.now()
        dtime3 = datetime.datetime.now()
        path1 = "a.txt"
        path2 = "b.txt"
        lst = [(path1, dtime1)]
        lst.append((path2, dtime2))
        lst.append((path2, dtime3))
        dct = stamp.get_file_list_dict(lst)
        self.assertEqual(dct[path1], [dtime1])
        self.assertEqual(dct[path2], [dtime3, dtime2])
        
        
class StampTimesTests(unittest.TestCase):
    
    def setUp(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.folder = os.path.join(script_dir, "test_folder", "stamp_test")
        self.path = os.path.join(self.folder, "a.txt")
        
        self.dtime1 = datetime.datetime.now()
        self.dtime2 = datetime.datetime.now()
        self.dtime3 = datetime.datetime.now()
        
        self.new_path1 = stamp.add_stamp(self.path, self.dtime1)
        self.new_path2 = stamp.add_stamp(self.path, self.dtime2)
        self.new_path3 = stamp.add_stamp(self.path, self.dtime3)
        
        open(self.new_path1, "w").close()
        open(self.new_path2, "w").close()
        open(self.new_path3, "w").close()
        
        
    def tearDown(self):
        for path in os.listdir(self.folder):
            os.unlink(os.path.join(self.folder, path))
            
            
    def test_time(self):    
        mask = stamp.extend_mask_by_stamp(self.path)
        dircetory, file_mask = os.path.split(mask) 
        files = utils.search(dircetory, "", file_mask)
        times = [stamp.split_stamp(f)[1] for f in files]
        times.sort()
        
        self.assertEqual(times, [self.dtime1, self.dtime2, self.dtime3])
        
    def test_versions_list(self):
        vers = stamp.get_versions_list(self.path)
        self.assertEqual(vers, [self.dtime3, self.dtime2, self.dtime1]) 
        
    def test_version1(self):
        vers = stamp.get_version(self.path, 1)
        self.assertEqual(vers, self.new_path2)
    
    def test_version2(self):
        vers = stamp.get_version(self.path, 3)
        self.assertEqual(vers, self.new_path1)
        
    def test_dict(self):
        mask = stamp.extend_mask_by_stamp(self.path)
        dircetory, file_mask = os.path.split(mask)
        files = utils.search(dircetory, "", file_mask)
        dct = stamp.files_to_file_dict(files) 
        self.assertEqual(dct[self.path], [self.dtime3, 
                                          self.dtime2, self.dtime1])
        
