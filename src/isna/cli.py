"""isna.cli -- The main cli script for isna.

cli.main() is called by cli2.main()

cli2.py is just a small script which loads cli.py
cli2.py just parses the sys.argv using docopt and sends them to cli.main()

They are split like this so that printing out the program's
usage & help statements occur quickly.
"""
import os
from schema import Schema, And, Or, Use, SchemaError, Regex
from collections import namedtuple, ChainMap
from isna.config import cfg


DEBUG = False


def dprint(*pargs, **kwargs):
    "print function - if the global DEBUG variable is set"

    if DEBUG:
        from sys import stderr
        print('ISNA:\t', *(x.replace('\n', '\n\t') for x in map(str, pargs)),
              flush=True, file=stderr, **kwargs)


def dpprint(*pargs, **kwargs):
    "pretty print function - if the global DEBUG variable is set"
    if DEBUG:
        from sys import stderr
        from pprint import pformat
        allargs = '\n'.join(x for x in map(pformat, pargs))
        print('ISNA:\t', allargs.replace('\n', '\n\t'), flush=True,
              file=stderr, **kwargs)


def uniq(iterable):
    "Yield uniqe elements"
    seen = set()
    for item in iterable:
        if item not in seen:
            seen.add(item)
            yield item


def get_templ_dirs(templ_dirs, default=cfg['templ_dirs']):
    """Return template directories, including any default directories.

    Duplicates will be removed.
    Each directory is either a string path '/some/template/dir'
    or a tuple like ('python.module', 'templatefolder')
    """
    total = []
    if templ_dirs is not None:
        total.extend(templ_dirs)
    total.extend(default)
    return list(uniq(total))


class Validate:
    """Validate arguments/options given by docopt

    TODO: Replace Transform class by moving all of its transformations
    here.
    """
    err_msg = 'Validation failed for {key!r} with data {data!r}'

    def __init__(self, d_args):
        """Validate arguments/options given by docopt

        d_args is the dictionary of options & arguments made by docopt
        It also does some transformation of the data.
        """
        self.data = d_args
        for k, v in self.schema.items():
            try:
                self.data[k] = v.validate(self.data[k])
            except SchemaError as e:
                msg = self.err_msg.format(key=k, data=self.data[k])
                raise ValueError(msg) from e

    @property
    def schema(self):
        try:
            return self._schema
        except AttributeError:
            d = {
                '--ssh': self._schema_ssh(),
                '--dir': self._schema_dir(),
                'TEMPLATE': self._schema_template(),
                '--vars': self._schema_vars(),
            }
            self._schema = {k: Schema(v) for k, v in d.items()}
            return self._schema

    def _schema_ssh(self):
        cuser = r'[a-zA-Z_]'
        chost = r'[a-zA-Z0-9_\.]'
        cport = r'[0-9]{1,5}'
        re_pats = (
            r'^{user}+@{host}+$'.format(user=cuser, host=chost),
            r'^{user}+@{host}+:{port}$'.format(user=cuser, host=chost, port=cport),
            r'^{host}+$'.format(host=chost),
            r'^{host}+:{port}$'.format(host=chost, port=cport),
        )
        regexes = [Regex(v) for v in re_pats]
        return Or(type(None), *regexes)

    def _schema_dir(self):
        return [os.path.isdir]

    def _schema_vars(self):
        from isna.util import dict_from_str
        return Or(None, And(Use(dict_from_str), dict))

    def _schema_template(self):
        td = get_templ_dirs(self.data['--dir'])
        from isna.playbook import get_env
        env = get_env(*td)

        def is_template(name):
            if name in env.list_templates(cfg['templ_ext']):
                return True
            return False
        return [Or(os.path.isfile, is_template)]


_tr_ssh = namedtuple('_tr_ssh', 'user host port')
_tr_templs = namedtuple('_tr_templs', 'name dir')


class Transform:
    "Rename option & arg keys, and transform their values"
    names = {
        '--ssh': 'ssh',
        '--sudo': 'sudo',
        '--domain': 'domain',
        '--dir': 'templ_dirs',
        'TEMPLATE': 'templs',
        '--vars': 'exvars',
        'vars': 'ls_vars',
        'hosts': 'ls_hosts',
        'temp': 'ls_temp',
    }

    def __init__(self, d_args):
        d_args.pop('ls', None)
        dat = {}
        self.data = dat
        for k, v in d_args.items():
            if k in self.names:
                dat[self.names[k]] = v
            else:
                dat[k] = v
        self.raw_dat = self.data.copy()
        for k, v in dat.items():
            try:
                dat[k] = getattr(self, k)
            except AttributeError:
                pass

    @property
    def ssh(self):
        return self._tr_ssh(self.raw_dat['ssh'])

    @staticmethod
    def _tr_ssh(ssharg):
        if not ssharg:
            return _tr_ssh(None, None, None)
        import re
        pat_user = r'(?:^(?P<user>[a-zA-Z_]\w+)@)?'
        pat_host = r'(?P<host>[a-zA-Z0-9_\.]+)'
        pat_port = r'(?:\:(?P<port>[0-9]{1,5}$))?'
        pat = pat_user + pat_host + pat_port
        x = re.search(pat, ssharg).groupdict()
        port = x.get('port', None)
        if port is not None:
            x['port'] = int(port)
        return _tr_ssh(**x)

    @property
    def templs(self):
        return self._tr_templs(self.raw_dat['templs'])

    @staticmethod
    def _tr_templs(templs):
        total = []
        for template in templs:
            if os.path.isfile(template):
                tpath = os.path.realpath(template)
                total.append(_tr_templs(os.path.basename(tpath), os.path.dirname(tpath)))
            else:
                total.append(_tr_templs(template, None))
        return total

    @property
    def templ_dirs(self):
        dirs = [x.dir for x in self.templs if x.dir]
        dirs.extend(self.raw_dat['templ_dirs'])
        return self._tr_templ_dirs(dirs)

    @staticmethod
    def _tr_templ_dirs(templ_dirs, default=cfg['templ_dirs']):
        return get_templ_dirs(templ_dirs, default=default)


def main(debug=False, **kwargs):
    if debug:
        global DEBUG
        DEBUG = True
    dprint('docopt produced the args:\n', kwargs)
    val = Validate(kwargs)
    tr = Transform(val.data)
    dat = tr.data
    dpprint('validated & transformed args are:', dat)
    ls = [k for k, v in dat.items() if k.startswith('ls_') and v]
    for func in ls:
        print(*globals()[func](**dat), sep='\n', flush=True)
        return 0
    runner = Runner(**dat)
    return runner.run()


class Runner:

    def __init__(self, **kwargs):
        from isna.query import InputQuery
        self.kwargs = kwargs
        self.dirs = kwargs['templ_dirs']
        exvars = kwargs['exvars']
        exvars = exvars if exvars else {}
        self.exvars = exvars
        self.inpq = InputQuery()

    @property
    def templates(self):
        return [x.name for x in self.kwargs['templs']]

    def run(self):
        tdirs = [x for x in self.kwargs['templ_dirs']]
        from isna.playbook import PBMaker, AnsiblePlaybook
        pbm = PBMaker(*tdirs)
        pbm.update(self.template_vars)
        avars = self.get_ansible_vars()
        for name in self.templates:
            dprint('Running playbook', name)
            txt = pbm.render(name)
            dprint(txt)
            with AnsiblePlaybook(txt, self.host_list, **avars) as apb:
                out = apb.run()
                return out.returncode

    def get_ansible_vars(self):
        sudo = self.kwargs['sudo']
        ssh = self.kwargs['ssh']

        ansivars = ChainMap(self.inpq.data, self.exvars)
        ansivars = {k: v for k, v in ansivars.items() if k not in self.template_vars}
        from isna.playbook import AnsibleArgs
        ansivars.update(AnsibleArgs.from_ssh(**ssh._asdict()))
        ansivars.update(AnsibleArgs.from_sudo(sudo))
        from isna.util import NeedsPass
        if ssh.host is not None:
            dprint('Testing ssh connection without password')
            res = NeedsPass.ssh(
                user=ansivars['ansible_user'],
                hostname=ssh.host,
                port=ansivars['ansible_port'],
                sudo=sudo,
            )
            dprint('SSH test results:\n', res)
            if res.ssh_needs_pw and ('ansible_ssh_pass' not in ansivars):
                passtupl = self.inpq('ansible_ssh_pass', hide=True)
                ansivars[passtupl.var] = passtupl.result
            if res.sudo_needs_pw and ('ansible_become_pass' not in ansivars):
                passtupl = self.inpq('ansible_become_pass', hide=True)
                ansivars[passtupl.var] = passtupl.result
        elif sudo and ('ansible_become_pass' not in ansivars):
            dprint('Testing sudo without password')
            res = NeedsPass.sudo(user=sudo)
            dprint('Sudo test results:\n', res)
            if res.sudo_needs_pw:
                passtupl = self.inpq('ansible_become_pass', hide=True)
                ansivars[passtupl.var] = passtupl.result
        dprint('Ansible --extra-vars:\n{!r}'.format(ansivars))
        return ansivars

    @property
    def template_vars(self):
        try:
            return self._template_vars
        except AttributeError:
            remaining = set(self.all_templ_vars) - set(self.exvars)
            remaining = remaining - set(self.inpq.data)
            for var in remaining:
                if any(x in var for x in cfg['pass_substrs']):
                    self.inpq(var, hide=True, repeat=True)
                else:
                    self.inpq(var)
            tvs = ChainMap(self.inpq.data, self.exvars)
            from isna.util import maybe_bool
            tvs = {k: maybe_bool(tvs[k]) for k in self.all_templ_vars}
            self._template_vars = tvs
            dprint('Undefined template vars:\n', self._template_vars)
            return self._template_vars

    @property
    def host_list(self):
        ssh = self.kwargs['ssh']
        return [ssh.host] if ssh.host else [cfg['default_host']]

    @property
    def all_templ_vars(self):
        try:
            return self._all_templ_vars
        except AttributeError:
            self._all_templ_vars = ls_vars(**self.kwargs)
            dprint('All template vars:\n', self._all_templ_vars)
            return self._all_templ_vars


def ls_hosts(**kwargs):
    hosts = ['localhost']
    msg = 'Searching on the avahi domain {!r} for other hosts'
    dprint(msg.format(kwargs['domain']))
    from isna.util import get_hosts
    hosts.extend(get_hosts(domain=kwargs['domain']))
    return [x for x in hosts if x]


def ls_temp(**kwargs):
    templ_ext = cfg['templ_ext']
    templ_dirs = kwargs['templ_dirs']
    msg = 'Listing playbook templates ending w/ {!r} in {!r}'
    dprint(msg.format(templ_ext, templ_dirs))
    from isna.playbook import PBMaker
    pbm = PBMaker(*templ_dirs)
    return pbm.list_templates(templ_ext)


def ls_vars(**kwargs):
    from isna.playbook import PBMaker
    pbm = PBMaker(*kwargs['templ_dirs'])
    tnames = kwargs['templs']
    all_vars = []
    for x in tnames:
        all_vars.extend(pbm.all_vars(x.name))
    return sorted(uniq(all_vars))
