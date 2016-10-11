import unittest
from isna import playbook as pb
from isna.config import cfg

import os
import jinja2


class TestJinjaEnv(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        def datfile(name):
            return os.path.join(cls.data_dir, name)
        cls.datfile = staticmethod(datfile)

    def test_get_loader(self):
        loader = pb.get_loader(self.data_dir)
        self.assertIsInstance(loader, jinja2.BaseLoader)
        loader = pb.get_loader()
        self.assertIsInstance(loader, jinja2.BaseLoader)

    def test_get_env(self):
        loader = pb.get_env(self.data_dir)
        self.assertIsInstance(loader, jinja2.Environment)
        loader = pb.get_env()
        self.assertIsInstance(loader, jinja2.Environment)

    def test_get_undefined(self):
        env = pb.get_env(self.data_dir)
        templ = env.get_template('playbook1.yml')
        undef = pb.get_undefined(templ)
        self.assertCountEqual(undef, {'alpha', 'beta', 'gamma'})


class TestPBMaker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        def datfile(name):
            return os.path.join(cls.data_dir, name)
        cls.datfile = staticmethod(datfile)
        cls.ex_templ_name = 'playbook1.yml'
        cls.ex_all_vars = {'alpha', 'beta', 'gamma'}

    def test_init(self):
        host_list = ['aaa', 'bbb']
        pbm = pb.PBMaker(self.data_dir, host_list=host_list)
        self.assertIsInstance(pbm.environment, jinja2.Environment)

    def test_list_templates(self):
        pbm = pb.PBMaker(self.data_dir)
        extension = self.ex_templ_name.rsplit('.', maxsplit=1)[-1]
        templ_names = pbm.list_templates([extension])
        self.assertIn(self.ex_templ_name, templ_names)
        templ_names = pbm.list_templates([extension+'asdf'])
        self.assertNotIn(self.ex_templ_name, templ_names)

    def test_all_vars(self):
        pbm = pb.PBMaker(self.data_dir)
        all_vars = pbm.all_vars(self.ex_templ_name)
        self.assertCountEqual(all_vars, self.ex_all_vars)

    def test_undef_vars(self):
        pbm = pb.PBMaker(self.data_dir)
        undef = pbm.undef_vars(self.ex_templ_name)
        self.assertCountEqual(undef, self.ex_all_vars)

        new_d = {'alpha': 'first'}
        undef = pbm.undef_vars(self.ex_templ_name, **new_d)
        self.assertCountEqual(undef, self.ex_all_vars - set(new_d))

        undef = pbm.undef_vars(self.ex_templ_name)
        self.assertCountEqual(undef, self.ex_all_vars)

        pbm.update(new_d)
        undef = pbm.undef_vars(self.ex_templ_name)
        self.assertCountEqual(undef, self.ex_all_vars - set(new_d))

    def test_render(self):
        pbm = pb.PBMaker(self.data_dir)
        self.assertRaises(
            jinja2.exceptions.UndefinedError,
            pbm.render,
            self.ex_templ_name
        )
        exv = sorted(self.ex_all_vars)
        new_d = {k:str(i) for i,k in enumerate(exv)}
        res = '\n'.join([str(i) for i,x in enumerate(exv)])
        out = pbm.render(self.ex_templ_name, **new_d)
        self.assertEqual(res, out)

        
