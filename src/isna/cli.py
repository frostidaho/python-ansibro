"""Isna

Usage:
  isna ls temp [--dir=<dir>]... [-v]
  isna ls vars [--dir=<dir>]... [-v] TEMPLATE...
  isna ls hosts [--domain=<domain>] [-v]
  isna [--dir=<dir>]... [-v] [--vars=<xtra>] [--ssh=<user@host:port>] [--sudo=<user>] TEMPLATE...
  isna (-h | --help | --version)

Options:
  --dir=<dir>             Additional template directory.
  --ssh=<user@host:port>  Connect as user to host using ssh
  --sudo=<user>           Sudo to this user after connection
  --domain=<domain>       Avahi-domain [default: .local]
  --vars=<vars>           Extra variables for TEMPLATE and ansible
  -h --help               Show this screen.
  --version               Show version.
  -v                      Verbose
"""
import os
import docopt
from schema import Schema, And, Or, Use, SchemaError, Regex
from collections import namedtuple, ChainMap
from isna.config import cfg
from isna import util
from isna.query import InputQuery
import isna.playbook as pb
import sys

class Druck:
    def __init__(self, verbose=False, outfile=sys.stderr, **kwargs):
        self.verbose = verbose
        self.outfile = outfile

        from pprint import pformat
        self._pformat = pformat

    def pretty(self, obj):
        if self.verbose:
            print(self._pformat(obj), file=self.outfile, flush=True)

    def __call__(self, *pargs, **kwargs):
        if self.verbose:
            print(*pargs, file=self.outfile, flush=True, **kwargs)

def uniq(iterable):
    "Yield uniqe elements"
    seen = set()
    for item in iterable:
        if item not in seen:
            seen.add(item)
            yield item

def get_templ_dirs(templ_dirs, default=cfg['templ_dirs']):
    total = []
    if templ_dirs is not None:
        total.extend(templ_dirs)
    total.extend(default)
    return list(uniq(total))

class Validate:
    err_msg = 'Validation failed for {key!r} with data {data!r}'
    def __init__(self, d_args):
        self.data = d_args
        for k,v in self.schema.items():
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
            self._schema = {k:Schema(v) for k,v in d.items()}
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
        return Or(None, And(Use(util.dict_from_str), dict))

    def _schema_template(self):
        td = get_templ_dirs(self.data['--dir'])
        env = pb.get_env(*td)
        def is_template(name):
            if name in env.list_templates(cfg['templ_ext']):
                return True
            return False
        return [Or(os.path.isfile, is_template)]


_tr_ssh = namedtuple('_tr_ssh', 'user host port')
_tr_templs = namedtuple('_tr_templs', 'name dir')
class Transform:
    names = {
        '--ssh': 'ssh',
        '--sudo': 'sudo',
        '--domain': 'domain',
        '--dir': 'templ_dirs',
        'TEMPLATE': 'templs',
        '-v': 'verbose',
        '--vars': 'exvars',
        'vars': 'ls_vars',
        'hosts': 'ls_hosts',
        'temp': 'ls_temp',
    }

    def __init__(self, d_args):
        d_args.pop('ls', None)
        dat = {}
        self.data = dat
        for k,v in d_args.items():
            if k in self.names:
                dat[self.names[k]] = v
            else:
                dat[k] = v
        self.raw_dat = self.data.copy()
        for k,v in dat.items():
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
        # FIXME add from template path if template is file
        dirs = [x.dir for x in self.templs if x.dir]
        dirs.extend(self.raw_dat['templ_dirs'])
        return self._tr_templ_dirs(dirs)

    @staticmethod
    def _tr_templ_dirs(templ_dirs, default=cfg['templ_dirs']):
        return get_templ_dirs(templ_dirs, default=default)


def main(argv=None):
    args = docopt.docopt(__doc__, version='Isna v0.1', argv=argv)
    # dk = Druck(verbose=args['-v'])
    # dk.pretty(args)
    args.pop('--help', None), args.pop('--version', None)
    val = Validate(args)
    tr = Transform(val.data)
    dat = tr.data
    # dk.pretty(dat)
    ls = [k for k,v in dat.items() if k.startswith('ls_') and v]
    for func in ls:
        print(*globals()[func](**dat), sep='\n', flush=True)
        return 0
    runner = Runner(**dat)
    return runner.run()


class Runner:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.dirs = kwargs['templ_dirs']
        exvars = kwargs['exvars']
        exvars = exvars if exvars else {}
        self.exvars = exvars

        self.inpq = InputQuery()
        dk = self.dk
        dk('Running playbooks', *self.templates)
        dk('Variables found in templates:\n\t', end='')
        dk.pretty(self.all_templ_vars)
        tvs = self.template_vars
        # dk.pretty(tvs)
        dk('Ansible --extra-vars')
        avs = self.get_ansible_vars()
        dk.pretty(avs)

    @property
    def dk(self):
        try:
            return self._dk
        except AttributeError:
            self._dk = Druck(verbose=self.kwargs['verbose'])
            return self._dk

    @property
    def templates(self):
        return [x.name for x in self.kwargs['templs']]

    def run(self):
        tdirs = [x for x in self.kwargs['templ_dirs']]
        pbm = pb.PBMaker(*tdirs)
        pbm.update(self.template_vars)
        avars = self.get_ansible_vars()
        for name in self.templates:
            self.dk('Running playbook', name)
            txt = pbm.render(name)
            with pb.AnsiblePlaybook(txt, self.host_list, **avars) as apb:
                out = apb.run()
            if out.returncode != 0:
                return out.returncode
        return out.returncode


    def get_ansible_vars(self):
        sudo = self.kwargs['sudo']
        ssh = self.kwargs['ssh']

        ansivars = ChainMap(self.inpq.data, self.exvars)
        ansivars = {k:v for k,v in ansivars.items() if k not in self.template_vars}
        ansivars.update(pb.AnsibleArgs.from_ssh(**ssh._asdict()))
        ansivars.update(pb.AnsibleArgs.from_sudo(sudo))
        
        if ssh.host is not None:
            res = util.NeedsPass.ssh(
                user=ansivars['ansible_user'],
                hostname=ssh.host,
                port=ansivars['ansible_port'],
                sudo=sudo,
            )
            if res.ssh_needs_pw and ('ansible_ssh_pass' not in ansivars):
                passtupl = self.inpq('ansible_ssh_pass', hide=True)
                ansivars[passtupl.var] = passtupl.result
            if res.sudo_needs_pw and ('ansible_become_pass' not in ansivars):
                passtupl = self.inpq('ansible_become_pass', hide=True)
                ansivars[passtupl.var] = passtupl.result
        elif sudo and ('ansible_become_pass' not in ansivars):
            res = util.NeedsPass.sudo(user=sudo)
            if res.sudo_needs_pw:
                passtupl = self.inpq('ansible_become_pass', hide=True)
                ansivars[passtupl.var] = passtupl.result
        return ansivars


    @property
    def template_vars(self):
        try:
            return self._template_vars
        except AttributeError:
            remaining = set(self.all_templ_vars) - set(self.exvars)
            remaining = remaining - set(self.inpq.data)
            for var in remaining:
                self.inpq(var)
            tvs = ChainMap(self.inpq.data, self.exvars)
            tvs = {k:util.maybe_bool(tvs[k]) for k in self.all_templ_vars}
            self._template_vars = tvs
            return self._template_vars

    @property
    def host_list(self):
        ssh = self.kwargs['ssh']
        return [ssh.host] if ssh.host else cfg['default_hosts']

    @property
    def all_templ_vars(self):
        try:
            return self._all_templ_vars
        except AttributeError:
            self._all_templ_vars = ls_vars(**self.kwargs)
            return self._all_templ_vars
        
def ls_hosts(**kwargs):
    hosts = ['localhost']
    hosts.extend(util.get_hosts(domain=kwargs['domain']))
    return [x for x in hosts if x]

def ls_temp(**kwargs):
    pbm = pb.PBMaker(*kwargs['templ_dirs'])
    return pbm.list_templates(cfg['templ_ext'])

def ls_vars(**kwargs):
    pbm = pb.PBMaker(*kwargs['templ_dirs'])
    tnames = kwargs['templs']
    all_vars = []
    for x in tnames:
        all_vars.extend(pbm.all_vars(x.name))
    return sorted(uniq(all_vars))

