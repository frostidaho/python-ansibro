import unittest
import os
from schema import SchemaError
import isna.cli as cli
from isna.config import cfg
from docopt import docopt


class TestValidate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        def getargs(argv):
            return docopt(cli.__doc__, argv=argv)
        cls.getargs = staticmethod(getargs)

        @classmethod
        def validate(cls, argv):
            args = cls.getargs(argv)
            v = cli.Validate(args)
            return v
        cls.validate = validate

    def test_template(self):
        self.validate(['user-create.yml'])
        with self.assertRaises(ValueError):
            self.validate(['nope-create-nothin.yml'])

    def test_ssh(self):
        val = self.validate
        val(argv=['--ssh=ida@localhost:22', 'user-create.yml'])
        val(argv=['--ssh=wow.local:9001', 'user-create.yml'])
        val(argv=['--ssh=nope@okay', 'user-create.yml'])
        with self.assertRaises(ValueError):
            val(['--ssh=wow.local:1234134149001', 'user-create.yml'])
        with self.assertRaises(ValueError):
            val(['--ssh=wow.local::22', 'user-create.yml'])

    def test_templ_dirs(self):
        val = self.validate
        val(['--dir=/tmp', 'user-create.yml'])
        with self.assertRaises(ValueError):
            val(['--dir=/tmpasdfjlasdf', 'user-create.yml'])



class TestTransformStatic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        def datfile(name):
            return os.path.join(cls.data_dir, name)
        cls.datfile = staticmethod(datfile)
        cls.tr = cli.Transform
        # cls.ssh = staticmethod(cls.tr._tr_ssh)

    def assertTrSSH(self, ssh, user, host, port):
        ssh = self.tr._tr_ssh(ssh)
        self.assertIsInstance(ssh, cli._tr_ssh)
        if user is None:
            self.assertIsNone(ssh.user)
        else:
            self.assertEqual(ssh.user, user)
        if host is None:
            self.assertIsNone(ssh.host)
        else:
            self.assertEqual(ssh.host, host)
        if port is None:
            self.assertIsNone(ssh.port)
        else:
            self.assertEqual(ssh.port, port)
        
    def test_ssh_none(self):
        self.assertTrSSH(None, None, None, None)

    def test_ssh_empty(self):
        self.assertTrSSH('', None, None, None)

    def test_ssh_0(self):
        self.assertTrSSH('meow@kater.local:22', 'meow', 'kater.local', 22)

    def test_ssh_1(self):
        self.assertTrSSH('google.local', None, 'google.local', None)

    def test_ssh_2(self):
        self.assertTrSSH('google.local:33', None, 'google.local', 33)

    def test_ssh_3(self):
        self.assertTrSSH('meow@google.local', 'meow', 'google.local', None)

    def assertInTemplDirs(self, tdirs, *args):
        for arg in args:
            self.assertIn(arg, tdirs)

    def test_templ_dirs_default(self):
        tdirs = self.tr._tr_templ_dirs
        x = tdirs([self.data_dir])
        self.assertInTemplDirs(x, self.data_dir, *cfg['templ_dirs'])

    def test_templ_dirs_no_deflt(self):
        tdirs = self.tr._tr_templ_dirs
        x = tdirs([self.data_dir], default=[])
        self.assertInTemplDirs(x, self.data_dir)
        for arg in cfg['templ_dirs']:
            self.assertNotIn(arg, x)

    def assertTempl(self, template, name, directory):
        self.assertIsInstance(template, cli._tr_templs)
        self.assertIsInstance(template.name, type(name))
        self.assertIsInstance(template.dir, type(directory))
        self.assertEqual(template.name, name)
        self.assertEqual(template.dir, directory)

    def test_templs_empty(self):
        templs = self.tr._tr_templs
        templates = templs([''])
        x = templates[0]
        self.assertTempl(x, '', None)

    def test_templs_file(self):
        templs = self.tr._tr_templs
        name = 'playbook1.yml'
        templates = templs([self.datfile(name)])
        x = templates[0]
        self.assertTempl(x, name, self.data_dir)
        
