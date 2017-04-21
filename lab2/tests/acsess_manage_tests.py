# -*- coding: utf-8 -*-


import unittest
import sys
import os

import myrm.acsess_manage as acsess_manage 
import myrm.config as config

from myrm.acsess_manage import AcsessManager

class AcsessManagerTests(unittest.TestCase):

    def setUp(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.folder = os.path.join(script_dir, 
                                   "test_folder", "acsess_manage_test")
        self.acsess_manager = AcsessManager(config.get_default_config())
        self.stdin = sys.stdin
        self.stdout = sys.stdout
        
    def tearDown(self):
        sys.stdin = self.stdin
        sys.stdout = self.stdout
        
    def test_ask1(self):
        path_in = os.path.join(self.folder, "y.txt")
        path_out = os.path.join(self.folder, "output.txt")
        sys.stdin = open(path_in, "r")
        sys.stdout = open(path_out, "w")
        self.assertTrue(acsess_manage.ask("",""))
        
    def test_ask2(self):
        path_in = os.path.join(self.folder, "n.txt")
        path_out = os.path.join(self.folder, "output.txt")
        sys.stdin = open(path_in, "r")
        sys.stdout = open(path_out, "w")
        self.assertFalse(acsess_manage.ask("",""))
        
    def test_interactive(self):
        path_in = os.path.join(self.folder, "4n.txt")
        path_out = os.path.join(self.folder, "output.txt")
        sys.stdin = open(path_in, "r")
        sys.stdout = open(path_out, "w")
        
        self.acsess_manager.cfg["interactive"] = True
        self.assertFalse(self.acsess_manager.remove_acsess(""))
        self.assertFalse(self.acsess_manager.restore_acsess(""))
        self.assertFalse(self.acsess_manager.clean_acsess(""))
        self.assertFalse(self.acsess_manager.autoclean_acsess())
        
    
    def test_dryrun(self):
        path_out = os.path.join(self.folder, "output.txt")
        sys.stdout = open(path_out, "w")
        
        self.acsess_manager.cfg["interactive"] = False
        self.acsess_manager.cfg["dryrun"] = True
        self.assertFalse(self.acsess_manager.remove_acsess(""))
        self.assertFalse(self.acsess_manager.restore_acsess(""))
        self.assertFalse(self.acsess_manager.clean_acsess(""))
        self.assertFalse(self.acsess_manager.autoclean_acsess())
        
    def test_run(self):
        path_out = os.path.join(self.folder, "output.txt")
        sys.stdout = open(path_out, "w")
        
        self.acsess_manager.cfg["interactive"] = False
        self.acsess_manager.cfg["dryrun"] = False
        self.assertTrue(self.acsess_manager.remove_acsess(""))
        self.assertTrue(self.acsess_manager.restore_acsess(""))
        self.assertTrue(self.acsess_manager.clean_acsess(""))
        self.assertTrue(self.acsess_manager.autoclean_acsess()) 
