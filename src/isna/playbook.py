from functools import partial as _partial
from collections import (
    ChainMap as _ChainMap,
    Iterable as _Iterable,
    defaultdict as _defaultdict,
    UserDict as _UserDict,
)
import jinja2
from jinja2 import meta as _meta
from isna import util as _util
from isna.config import cfg


def _ansible_filters():
    """Load and return some jinja2 filters that are shipped with ansible.

    This is only called when one of these filters appears in a playbook template.
    This is the only place ansible code is imported.
    """
    from ansible.plugins.filter.core import FilterModule
    return FilterModule().filters()


JinjaEnv = _partial(
    jinja2.Environment,
    block_start_string='<@@',
    block_end_string='@@>',
    variable_start_string='<@',
    variable_end_string='@>',
    comment_start_string='<#',
    comment_end_string='#>',
    undefined=jinja2.StrictUndefined,
)


def get_loader(*templ_dirs):
    """Get a jinja loader which searches in templ_dirs

    Each templ_dir can either be a
        directory path as a string (e.g., '/path/to/templates')
        or a list-like object of   (e.g, ['pymodule_name', 'template_folder'])
    """
    loaders = []
    for td in templ_dirs:
        if isinstance(td, str):
            ldr = jinja2.FileSystemLoader(td, followlinks=True)
        elif isinstance(td, _Iterable):  # MUST come after check for str since
            ldr = jinja2.PackageLoader(*td)
        else:
            raise TypeError('type {} is not supported'.format(type(td)))
        loaders.append(ldr)
    return jinja2.ChoiceLoader(loaders)


def get_env(*templ_dirs):
    """Get a jinja environment with loaders from templ_dirs

    Each templ_dir can either be a
        directory path as a string     (e.g., '/path/to/templates')
        or a list-like object of len 2 (e.g, ['pymodule_name', 'template_folder'])
    """
    return JinjaEnv(loader=get_loader(*templ_dirs))


def get_undefined(template):
    "Given a jinja2 template object return the template's variables"
    env = template.environment
    template_str = env.loader.get_source(env, template.name)[0]
    parsed_content = env.parse(template_str)
    return _meta.find_undeclared_variables(parsed_content)


class AnsibleArgs(_UserDict):

    @classmethod
    def from_ssh(cls, user=None, host=None, port=None):
        d = {}
        if host is None:
            d['ansible_connection'] = 'local'
            return cls(d)

        if user is None:
            import getpass
            user = getpass.getuser()
        if port is None:
            port = cfg['default_ssh_port']
        d['ansible_user'] = user
        d['ansible_port'] = port
        return cls(d)

    @classmethod
    def from_sudo(cls, user=None):
        if user is None:
            return cls()
        d = {
            'ansible_become': True,
            'ansible_become_method': 'sudo',
            'ansible_become_user': user,
        }
        return cls(d)


class PBMaker(_UserDict):

    def __init__(self, *templ_dirs, **kwargs):
        super().__init__(kwargs)
        self.templ_dirs = templ_dirs
        self._templates = {}

    @property
    def environment(self):
        try:
            return self._environment
        except AttributeError:
            self._environment = get_env(*self.templ_dirs)
            return self._environment

    def get_template(self, name):
        templ = self._templates.get(name, False)
        if templ:
            return templ
        try:
            templ = self.environment.get_template(name)
        except jinja2.exceptions.TemplateAssertionError:  # Load ansible filters
            self.environment.filters.update(_ansible_filters())
            templ = self.environment.get_template(name)
        self._templates[name] = templ
        return templ

    def list_templates(self, extensions=None, filter_func=None):
        return self.environment.list_templates(
            extensions=extensions,
            filter_func=filter_func,
        )

    def all_vars(self, templ_name):
        return get_undefined(self.get_template(templ_name))

    def undef_vars(self, templ_name, **kwargs):
        all_vars = self.all_vars(templ_name)
        cm = _ChainMap(kwargs, self.data)
        defined_vars = set(cm.keys())
        return all_vars - defined_vars

    def render(self, name, **kwargs):
        """Render the template with additional kwargs. Return as str.

        Any given kwargs will override the variables defined in self.data,
        but their value won't be stored.
        """
        cm = _ChainMap(kwargs, self.data)
        newd = {k: v for k, v in cm.items()}
        templ = self.get_template(name)
        return templ.render(**newd)

    def __repr__(self):
        reprdict = super().__repr__()
        cname = self.__class__.__name__
        main = '{cname}({temp}, **{reprdict})'
        main = main.format(
            cname=cname,
            temp=repr(self.templ_dirs),
            reprdict=reprdict,
        )
        return main


class AnsiblePlaybook:
    """AnsiblePlaybook is context manager for running playbooks

    For example:
        with AnsiblePlaybook(...) as pb:
            output = pb.run()
    """

    def __init__(self, playbook_str, host_list, **extra_vars):
        import tempfile
        import json
        import subprocess

        self._tempfile = tempfile
        self._json = json
        self._subprocess = subprocess

        self.playbook_str = playbook_str
        self.host_list = host_list
        self.extra_vars = {}
        self.extra_vars.update(cfg['common_ansi_vars'])
        self.extra_vars.update(extra_vars)

    def get_tempfile(self, towrite, mode='w+t', suffix=None, prefix='isna'):
        """Create a named temporary file from the string towrite


        It returns a handle to the file object.

        The file is named prefix**suffix, and should have no rwx permissions for group
        or others.
        [On my system tempfile.NamedTemporaryFile implicitly sets the permissions
        for group and others to zero. If this isn't always true we'll
        have to come up with another solution]
        """
        ntf = self._tempfile.NamedTemporaryFile
        tf = ntf(mode='w+t', prefix=prefix, suffix=suffix)
        tf.write(towrite)
        tf.seek(0)
        return tf

    def __enter__(self):
        self.temp_playbook = self.get_tempfile(self.playbook_str, suffix='.yml')
        self.temp_extra_vars = self.get_tempfile(
            self._json.dumps(self.extra_vars),
            suffix='.json',
        )
        return self

    def __exit__(self, *args):
        self.temp_playbook.close()
        self.temp_extra_vars.close()

    def run(self):
        sp = self._subprocess
        cmd = ['ansible-playbook', self.temp_playbook.name]
        inv = ['-i', ','.join(self.host_list) + ',']
        extra = ['-e', '@' + self.temp_extra_vars.name]
        cmd = cmd + inv + extra
        # return sp.run(cmd, stdout=sp.PIPE, stderr=sp.PIPE, stdin=sp.DEVNULL)
        return sp.run(cmd, stdin=sp.DEVNULL)
