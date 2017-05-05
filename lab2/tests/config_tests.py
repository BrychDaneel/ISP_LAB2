# -*- coding: utf-8 -*-


import unittest
import os

import myrm.config as config


class ConfigTests(unittest.TestCase):
    
    def setUp(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.folder = os.path.join(script_dir, "test_folder", "config_test")
        self.cfg = {
            "force" : False,
            "dryrun" : False,
            "verbose" : True,
            "interactive" : False,
            "replace" : False,
            "allowautoclean" : True,

            "trash" : {
                "dir" : "~/.trash",
                "lockfile" : "lock",

                "max_size" : 1024*1024*1024,
                "max_count": 10*1000*1000,
            },

            "autoclean" : {
                "size" : 512*1024*1024,
                "count" : 1000*1000,
                "days" : 90,
                "samename" : 10,
            }
        }
        self.maxDiff = 10000

        
    def test_cfg(self):
        self.cfg["verbose"] = False
        self.cfg["autoclean"]["count"] = 54321
        path = os.path.join(self.folder, "test1.cfg")
        config.save_to_cfg(self.cfg, path)
        new_cfg = config.load_from_cfg(path)
        self.assertEquals(new_cfg, self.cfg)
    
    def test_cfg_load(self):
        path = os.path.join(self.folder, "test.cfg")
        new_cfg = config.load_from_cfg(path)
        self.assertFalse(new_cfg["verbose"])
        self.assertEquals(new_cfg["autoclean"]["count"], 54321)
        
    def test_cfg_error(self):
        path = os.path.join(self.folder, "bad.cfg")
        with self.assertRaises(ValueError):
            config.load_from_cfg(path) 
        
    def test_json(self):
        self.cfg["verbose"] = False
        self.cfg["autoclean"]["count"] = 54321
        path = os.path.join(self.folder, "test1.json")
        config.save_to_json(self.cfg, path)
        new_cfg = config.load_from_json(path)
        self.assertEquals(new_cfg, self.cfg)
        
    def test_json_load(self):
        path = os.path.join(self.folder, "test.json")
        new_cfg = config.load_from_json(path)
        self.assertFalse(new_cfg["verbose"])
        self.assertEquals(new_cfg["autoclean"]["count"], 54321)  
        
    def test_json_error(self):
        path = os.path.join(self.folder, "bad.json")
        with self.assertRaises(ValueError):
            config.load_from_json(path) 
        
