import subprocess as sp
from isna.config import cfg


def maybe_bool(txt, true_strs=cfg['true_strs'],
               false_strs=cfg['false_strs']):
    """Convert txt string to bool if it matches any true/false strings

    If the lowercase version of txt is in true_strs  -> True
                                          false_strs -> False
                                          otherwise  -> txt
    """
    _txt = txt.lower()
    if _txt in true_strs:
        return True
    elif _txt in false_strs:
        return False
    else:
        return txt


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


# # TODO: Replace _query fns with InpQuery()
# import sys as _sys
# from functools import partial as _partial
# class InpQuery:
#     def __init__(self, print_file=_sys.stdout):
#         is_tty = _sys.stdin.isatty()
#         if is_tty:
#             self._query = self._user_query
#         else:
#             self._query = self._stdin_query
#         self.qprint = _partial(print, file=print_file)

#     # def __call__(self, key, default=None, prompt='Enter value for {}', prompt_suffix=': ', hide_input=False, confirm=False, err=False):
#     #     pass

#     def __call__(self, var, default=None, prompt=None, *pargs, **kwargs):
#         if prompt is None:
#             prompt = self.prompt.format(var)
#         return self._query(var, prompt, *pargs, **kwargs)

#     @staticmethod
#     def _user_query(var, prompt, allow_empty=False, *pargs, **kwargs):
#         from getpass import getpass
#         if any((x for x in cfg['password_types'] if x in var)):
#             val = getpass(prompt=var)
#         else:
#             val = input(var)
#         if val or allow_empty:
#             return val
#         else:
#             return InpQuery._user_query(var, prompt, allow_empty)

#     def _stdin_query(self, var, *pargs, **kwargs):
#         try:
#             jdat = self._json_dat
#         except AttributeError:
#             import json
#             jdat = json.load(_sys.stdin)
#             self._json_dat = jdat
#         return jdat[var]
