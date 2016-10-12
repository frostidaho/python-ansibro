import subprocess as sp
from functools import lru_cache as _lru_cache
from collections import namedtuple as _namedtuple

from isna.config import cfg


def maybe_bool(txt, true_strs=cfg['true_strs'],
               false_strs=cfg['false_strs']):
    """Convert txt string to bool if it matches any true/false strings

    If the lowercase version of txt is in true_strs  -> True
                                          false_strs -> False
                                          otherwise  -> txt
    """
    if not isinstance(txt, str):
        return txt
    _txt = txt.lower()
    if _txt in true_strs:
        return True
    elif _txt in false_strs:
        return False
    else:
        return txt


@_lru_cache()
def get_hosts(domain='.local'):
    "Return a list of hostnames on domain"
    hosts = set()
    p = sp.Popen(['avahi-browse', '-alrpt'], stdout=sp.PIPE)
    stdout, stderr = p.communicate()
    stdout = stdout.decode()
    for line in stdout.splitlines():
        elements = line.split(';')
        hosts = hosts | set([x for x in elements if x.endswith(domain)])
    return sorted(hosts)

need_pass = _namedtuple(
    'need_pass',
    ['host',
     'ssh_user', 'ssh_needs_pw', 'ssh_retcode', 'ssh_success',
     'sudo_user', 'sudo_needs_pw', 'sudo_retcode', 'sudo_success'],
)


class NeedsPass:

    @classmethod
    def ssh(cls, user='root', hostname='localhost', sudo='', port=22, strict=None):
        res = cls._ssh(user=user, hostname=hostname, sudo=sudo, port=port, strict=strict)
        code = res.returncode
        d = dict.fromkeys(need_pass._fields)
        d['host'] = hostname
        d['ssh_user'] = user
        d['ssh_retcode'] = code
        d['sudo_user'] = sudo if sudo else None
        if code == 0:
            d['ssh_needs_pw'] = False
            d['ssh_success'] = True
            if sudo:
                d['sudo_needs_pw'] = False
                d['sudo_retcode'] = code
                d['sudo_success'] = True
        elif code == 255:       # ssh always fails with 255
            cls._test_conn_err(res.stderr)
            d['ssh_needs_pw'] = True
            d['ssh_success'] = False

        else:
            d['ssh_needs_pw'] = False
            d['ssh_success'] = True
            d['ssh_retcode'] = 0
            if sudo:
                d['sudo_needs_pw'] = True
                d['sudo_retcode'] = code
                d['sudo_success'] = False
        return need_pass(**d)

    @staticmethod
    def _test_conn_err(stderr):
        """Test stderr from ssh for connection problems

        If connection problem is found raise ConnectionError()
        """
        errors = (
            'Connection refused',
            'Host key verification failed.',
            'Could not resolve hostname',
        )
        stderr = stderr.decode()
        if any(x for x in errors if x in stderr):
            raise ConnectionError(stderr)

    @staticmethod
    def _ssh(user='root', hostname='localhost', sudo='', port=22, strict=None):
        usrhost = '{}@{}'.format(user, hostname)
        cmd = [
            'ssh', '-T',
            '-oBatchMode=yes',
            '-oNoHostAuthenticationForLocalhost=yes',
            '-p', '{}'.format(port),
        ]
        if strict is not None:
            strict = 'yes' if strict else 'no'
            cmd.append('-oStrictHostKeyChecking={}'.format(strict))
        cmd.append(usrhost)

        if sudo:
            cmd.append('sudo -u {} -n whoami'.format(sudo))
        output = sp.run(
            cmd,
            stdin=sp.DEVNULL,
            stdout=sp.PIPE,
            stderr=sp.PIPE,
        )
        return output

    @classmethod
    @_lru_cache()
    def sudo(cls, user='root'):
        res = cls._sudo(user=user)
        code = res.returncode
        d = dict.fromkeys(need_pass._fields)
        d['host'] = 'localhost'
        d['sudo_user'] = user
        d['sudo_retcode'] = code
        d['sudo_needs_pw'] = False if code == 0 else True
        d['sudo_success'] = True if code == 0 else False
        return need_pass(**d)

    @staticmethod
    def _sudo(user='root'):
        cmd = 'sudo -u {} -n whoami'.format(user)
        output = sp.run(
            cmd,
            shell=True,
            stdout=sp.PIPE,
            stderr=sp.PIPE,
        )
        return output


def _json_parse_str(varstr):
    "Load obj from json; Return None on exception"
    import json
    try:
        return json.loads(varstr)
    except json.JSONDecodeError:
        return None


def _simple_parse_str(varstr, kv_sep='=', sep=';'):
    "Turn a string like 'a=1; b=2; c=three' into a dict"
    def parse():
        for kv in (x for x in varstr.split(sep) if x):
            k, v = kv.split(kv_sep)
            k, v = k.strip(), v.strip()
            yield k, v
    return dict(parse())


def dict_from_str(some_string, kv_sep='=', sep=';'):
    """Create a dictionary from a string

    some_string can be either
       a json object (dict-like), or
       a string of key,value pairs like 'a=1; b=2; c=three'
    """
    dvars = _json_parse_str(some_string)
    if dvars is None:
        dvars = _simple_parse_str(some_string, kv_sep=kv_sep, sep=sep)
    return dict(dvars)
