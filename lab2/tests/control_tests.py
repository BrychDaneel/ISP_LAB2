# -*- coding: utf-8 -*-


import unittest
import sys
import os

import myrm.control as control

class AcsessManagerTests(unittest.TestCase):

    def setUp(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.folder = os.path.join(script_dir, 
                                   "test_folder", "acsess_manage_test")
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
        self.assertTrue(control.ask("",""))
        
    def test_ask2(self):
        path_in = os.path.join(self.folder, "n.txt")
        path_out = os.path.join(self.folder, "output.txt")
        sys.stdin = open(path_in, "r")
        sys.stdout = open(path_out, "w")
        self.assertFalse(control.ask("",""))
        
    def test_interactive(self):
        path_in = os.path.join(self.folder, "4n.txt")
        path_out = os.path.join(self.folder, "output.txt")
        sys.stdin = open(path_in, "r")
        sys.stdout = open(path_out, "w")
        
        allow = control.remove("test.tst", interactive=True)
        self.assertFalse(allow)
        allow = control.restore("test.tst", interactive=True)
        self.assertFalse(allow)
        allow = control.clean("test.tst", interactive=True)
        self.assertFalse(allow)
        allow = control.autoclean("test.tst", interactive=True)
        self.assertFalse(allow)
        
    def test_run(self):
        path_out = os.path.join(self.folder, "output.txt")
        sys.stdout = open(path_out, "w")
        
        allow = control.remove("test.tst", interactive=False)
        self.assertTrue(allow)
        allow = control.restore("test.tst", interactive=False)
        self.assertTrue(allow)
        allow = control.clean("test.tst", interactive=False)
        self.assertTrue(allow)
        allow = control.autoclean("test.tst", interactive=False)
        self.assertTrue(allow)
