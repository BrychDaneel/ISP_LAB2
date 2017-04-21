# -*- coding: utf-8 -*-


import unittest
import os

import myrm.config as config


class ConfigTests(unittest.TestCase):
    
    def setUp(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.folder = os.path.join(script_dir, "test_folder", "config_test")
        
    def test_default(self):
        cfg = config.get_default_config()
        
        self.assertIn("force", cfg)
        self.assertIn("dryrun", cfg)
        self.assertIn("verbose", cfg)
        self.assertIn("interactive", cfg)
        
        self.assertIn("trash", cfg)
        self.assertIn("dir", cfg["trash"])
        self.assertIn("lockfile", cfg["trash"])
        self.assertIn("allowautoclean", cfg["trash"])

        self.assertIn("max", cfg["trash"])
        self.assertIn("size", cfg["trash"]["max"])
        self.assertIn("count", cfg["trash"]["max"])

        self.assertIn("autoclean", cfg["trash"])
        self.assertIn("size", cfg["trash"]["autoclean"])
        self.assertIn("count", cfg["trash"]["autoclean"])
        self.assertIn("days", cfg["trash"]["autoclean"])
        self.assertIn("samename", cfg["trash"]["autoclean"])
        
    def test_cfg(self):
        cfg = config.get_default_config()
        cfg["verbose"] = False
        cfg["trash"]["autoclean"]["count"] = 54321
        path = os.path.join(self.folder, "test1.cfg")
        config.save_to_cfg(cfg, path)
        new_cfg = config.load_from_cfg(path)
        self.assertEquals(new_cfg, cfg)
    
    def test_cfg_load(self):
        path = os.path.join(self.folder, "test.cfg")
        new_cfg = config.load_from_cfg(path)
        self.assertFalse(new_cfg["verbose"])
        self.assertEquals(new_cfg["trash"]["autoclean"]["count"], 54321)
        
    def test_cfg_error(self):
        path = os.path.join(self.folder, "bad.cfg")
        with self.assertRaises(ValueError):
            config.load_from_cfg(path) 
        
    def test_json(self):
        cfg = config.get_default_config()
        cfg["verbose"] = False
        cfg["trash"]["autoclean"]["count"] = 54321
        path = os.path.join(self.folder, "test1.json")
        config.save_to_json(cfg, path)
        new_cfg = config.load_from_json(path)
        self.assertEquals(new_cfg, cfg)
        
    def test_json_load(self):
        path = os.path.join(self.folder, "test.json")
        new_cfg = config.load_from_json(path)
        self.assertFalse(new_cfg["verbose"])
        self.assertEquals(new_cfg["trash"]["autoclean"]["count"], 54321)  
        
    def test_json_error(self):
        path = os.path.join(self.folder, "bad.json")
        with self.assertRaises(ValueError):
            config.load_from_json(path) 
        
