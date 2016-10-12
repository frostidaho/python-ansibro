import unittest
from isna import util
from isna.config import cfg
from functools import partial
from itertools import chain

class TestMaybeBool(unittest.TestCase):
    "Test utils.maybe_bool"
    def test_true_exact(self):
        f = partial(util.maybe_bool, true_strs=cfg['true_strs'])
        for txt in cfg['true_strs']:
            self.assertIs(f(txt), True)

    def test_false_exact(self):
        f = partial(util.maybe_bool, false_strs=cfg['false_strs'])
        for txt in cfg['false_strs']:
            self.assertIs(f(txt), False)

    def test_true_upper(self):
        f = partial(util.maybe_bool, true_strs=cfg['true_strs'])
        for txt in cfg['true_strs']:
            self.assertIs(f(txt.upper()), True)

    def test_false_upper(self):
        f = partial(util.maybe_bool, false_strs=cfg['false_strs'])
        for txt in cfg['false_strs']:
            self.assertIs(f(txt.upper()), False)

    def test_identity(self):
        f = partial(util.maybe_bool, false_strs=(), true_strs=())
        for txt in chain(cfg['false_strs'], cfg['true_strs']):
            self.assertEqual(f(txt), txt)
            self.assertEqual(f(txt.upper()), txt.upper())

    def test_none(self):
        x = util.maybe_bool(None)
        self.assertIsNone(x)

class TestDictFromStr(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d0 = {'a':0, 'b':'one', 'c':True}
        cls.d1 = {'a':'0', 'b':'one', 'c':'True'}
        cls.s0 = '{"a":0, "b":"one", "c":true}'
        cls.s1 = "a=0; b=one; c=True"
        
    def test_simple_parse_str1(self):
        x = util._simple_parse_str(self.s1)
        self.assertEqual(self.d1, x)

    def test_json_parse_str0(self):
        x = util._json_parse_str(self.s0)
        self.assertEqual(self.d0, x)

    def test_json_parse_str1(self):
        x = util._json_parse_str(self.s1)
        self.assertEqual(None, x)

    def test_dict_from_str0(self):
        x = util.dict_from_str(self.s0)
        self.assertEqual(x, self.d0)

    def test_dict_from_str1(self):
        x = util.dict_from_str(self.s1)
        self.assertEqual(x, self.d1)

