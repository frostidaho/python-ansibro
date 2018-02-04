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
        cls.d0 = {'a': 0, 'b': 'one', 'c': True, 'd': [42, 'jein']}
        cls.json_s0 = '{"a":0, "b":"one", "c":true, "d": [42, "jein"]}'
        cls.simp_s0 = 'a=0; b=one; c=true; d=[42, "jein"]'

        cls.d1 = {'a': 0, 'b': 'one', 'c': True}
        cls.simp_s1 = "a=0; b=one; c=true"
        cls.json_s1 = '{"a":0, "b":"one", "c":true}'

        cls.d2 = {'a': {'a': 'good=bad'}, 'b': 'one'}
        cls.simp_s2 = 'a={"a": "good=bad"}; b=one'
        cls.json_s2 = '{"a": {"a": "good=bad"}, "b": "one"}'

        cls.d3 = {'a': 0, 'b': 'xyz'}
        cls.simp_s3 = 'a=0;\n b=xyz\n'
        cls.simp_s3_v2 = 'a=0;\n\n b =xyz\n'
        cls.simp_s3_v3 = '\na=0;\n\n b =   xyz\n'
        # cls.json_s3 = '{"a": 0, "b": 99}'

        cls.d4 = {'a': ['x', 'y', 'z']}
        cls.simp_s4 = 'a=["x","y","z"]'
        cls.simp_s4_v2 = 'a=["x",\n"y",\n"z"];'

        cls.d5 = {'name': 'aname'}
        cls.simp_s5 = 'name=aname\n'
        cls.simp_s5_v2 = 'name=aname \n'

    def assertAllEqual(self, first, *args):
        from itertools import chain
        for a, b in zip(chain((first,), args), args):
            self.assertEqual(a, b)

    def test_simple_parse_str0(self):
        x = util._simple_parse_str(self.simp_s0)
        self.assertEqual(self.d0, x)

    def test_simple_parse_str1(self):
        x = util._simple_parse_str(self.simp_s1)
        self.assertEqual(self.d1, x)

    def test_simple_parse_str2(self):
        x = util._simple_parse_str(self.simp_s2)
        self.assertEqual(self.d2, x)

    def test_simple_parse_str3(self):
        x = util._simple_parse_str(self.simp_s3)
        self.assertEqual(self.d3, x)
        x = util._simple_parse_str(self.simp_s3_v2)
        self.assertEqual(self.d3, x)
        x = util._simple_parse_str(self.simp_s3_v3)
        self.assertEqual(self.d3, x)

    def test_simple_parse_str4(self):
        x = util._simple_parse_str(self.simp_s4)
        self.assertEqual(self.d4, x)
        x = util._simple_parse_str(self.simp_s4_v2)
        self.assertEqual(self.d4, x)

    def test_simple_parse_str5(self):
        x = util._simple_parse_str(self.simp_s5)
        self.assertEqual(self.d5, x)
        x = util._simple_parse_str(self.simp_s5_v2)
        self.assertEqual(self.d5, x)


    def test_json_parse_str0(self):
        x = util._json_parse_str(self.json_s0)
        self.assertEqual(self.d0, x)

    def test_json_parse_simp_strs(self):
        x = util._json_parse_str(self.simp_s0)
        self.assertIsNone(x)
        x = util._json_parse_str(self.simp_s1)
        self.assertIsNone(x)
        x = util._json_parse_str(self.simp_s2)
        self.assertIsNone(x)

    def test_json_parse_str1(self):
        x = util._json_parse_str(self.json_s1)
        self.assertEqual(self.d1, x)

    def test_json_parse_str2(self):
        x = util._json_parse_str(self.json_s2)
        self.assertEqual(self.d2, x)

    def test_dict_from_str0(self):
        x = util.dict_from_str(self.json_s0)
        y = util.dict_from_str(self.simp_s0)
        self.assertAllEqual(self.d0, x, y)

    def test_dict_from_str1(self):
        x = util.dict_from_str(self.simp_s1)
        y = util.dict_from_str(self.json_s1)
        self.assertAllEqual(x, self.d1, y)

    def test_dict_from_str2(self):
        x = util.dict_from_str(self.simp_s2)
        y = util.dict_from_str(self.json_s2)
        self.assertAllEqual(x, self.d2, y)
