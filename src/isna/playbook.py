import tempfile
import sys as _sys


from functools import partial as _partial
from collections import (
    UserDict as _UserDict,
    ChainMap as _ChainMap,
    Iterable as _Iterable,
    defaultdict as _defaultdict,
)
import jinja2
from jinja2 import meta as _meta
from isna import util as _util
from isna.config import cfg

def _ansible_filters():
    from ansible.plugins.filter.core import FilterModule
    return FilterModule().filters()

# DEFAULT_HOSTS = ('localhost',)

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
    loaders = []
    for td in templ_dirs:
        if isinstance(td, str):
            ldr = jinja2.FileSystemLoader(td, followlinks=True)
        elif isinstance(td, _Iterable): # MUST come after check for str since
            ldr = jinja2.PackageLoader(*td)
        else:
            raise TypeError('type {} is not supported'.format(type(td)))
        loaders.append(ldr)
    return jinja2.ChoiceLoader(loaders)

def get_env(*templ_dirs):
    """Get a jinja environment with loaders from templ_dirs

    Each templ_dir can either be a 
        directory path as a string
        or a list-like object of ['pymodule_name', 'template_folder']
    """
    return JinjaEnv(loader=get_loader(*templ_dirs))
        
def get_undefined(template):
    env = template.environment
    template_str = env.loader.get_source(env, template.name)[0]
    parsed_content = env.parse(template_str)
    return _meta.find_undeclared_variables(parsed_content)

class _UserDictRepr(_UserDict):
    def __repr__(self):
        reprdict = super().__repr__()
        cname = self.__class__.__name__
        main = '{cname}({temp}, {host}, **{reprdict})'
        main = main.format(
            cname=cname,
            temp=repr(self.templ_dirs),
            host=repr(self.host_list),
            reprdict=reprdict,
        )
        return main

class PBMaker(_UserDictRepr):
    def __init__(self, *templ_dirs, host_list=cfg['default_hosts'], **kwargs):
        super().__init__(kwargs)
        self.templ_dirs = templ_dirs
        self.host_list = list(host_list)
        self._templates = {}

    @property
    def environment(self):
        try:
            return self._environment
        except AttributeError:
            self._environment = get_env(*self.templ_dirs)
            # self._environment.filters.update(_ansi_filters)
            return self._environment

    def get_template(self, name):
        templ = self._templates.get(name, False)
        if templ:
            return templ
        try:
            templ = self.environment.get_template(name)
        except jinja2.exceptions.TemplateAssertionError: # Load ansible filters
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
        cm = {k:_util.maybe_bool(v) for k,v in cm.items()}
        templ = self.get_template(name)
        return templ.render(**cm)


def _tempfile(towrite, mode='w+t', suffix=None, prefix='isna'):
    tf = tempfile.NamedTemporaryFile(mode='w+t', prefix=prefix, suffix=suffix)
    tf.write(towrite)
    tf.seek(0)
    return tf


def ansible_playbook(playbook_str, host_list, **extra_vars):
    import json
    import subprocess as sp
    temp_pb = _tempfile(playbook_str, suffix='.yml')
    temp_extra_vars = _tempfile(json.dumps(extra_vars), suffix='.json')

    cmd = ['ansible-playbook', temp_pb.name,]
    inv = ['-i', ','.join(host_list) + ',',]
    extra = ['-e', '@' + temp_extra_vars.name,]
    cmd = cmd + inv + extra
    out = sp.run(cmd, stdout=sp.PIPE, stderr=sp.PIPE, stdin=sp.DEVNULL)
    # out = run(cmd)
    temp_pb.close()
    temp_extra_vars.close()
    return out

    
if __name__ == '__main__':
    def subproc_status(out):
        if out.stdout:
            print(20*'@', 'stdout', 20*'@')
            print(out.stdout.decode(), end='')
        if out.stderr:
            print(20*'@', 'stderr', 20*'@')
            print(out.stderr.decode(), end='')
        print(20*'@', 'end', 20*'@')
        return out

    pbm = PBMaker(('isna', 'playbook_templates'), '/home/ida/htmp/', host_list=['localhost'])
    pbm.update({
        'pingtask': 'ping task string',
        'alpha': 'PBM ALPHA VAL'
    })
    out = ansible_playbook(
        pbm.render('ping.yml'),
        ['localhost'],
        ansible_connection='local',
        ansible_become='yes',
        ansible_become_user='root',
    )
    subproc_status(out)
    # print(out)
    print(pbm.render('t1.txt', alpha=1, beta=2, gamma=3))
    
