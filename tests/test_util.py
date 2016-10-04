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



