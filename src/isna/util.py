import sys as _sys
from isna.config import cfg

def maybe_bool(txt, true_strs=cfg['true_strs'],
               false_strs=['false_strs']):
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

# # TODO: Replace _query fns with InpQuery()
# class InpQuery:
#     prompt = 'Enter value for {}: '
#     def __init__(self):
#         is_tty = _sys.stdin.isatty()
#         if is_tty:
#             self._query = self._user_query
#         else:
#             self._query = self._stdin_query

#     def __call__(self, var, prompt=None, *pargs, **kwargs):
#         if prompt is None:
#             prompt = self.prompt
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

