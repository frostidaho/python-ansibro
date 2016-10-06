#!/usr/bin/env python
import sys as _sys
from functools import partial as _partial
from collections import namedtuple as _namedtuple


def _identity(x):
    return x


def _hidden_input(prompt):
    from getpass import getpass
    return getpass(prompt)

QueryRes = _namedtuple('QueryRes', 'var result raw_result')


class InputQuery:
    """InputQuery is a class which facilitates getting user-input or input from a pipe

    If stdin is a tty, it queries the user using input() and getpass().
    However, if stdin is piped then the data is assumed to be formatted
    as a json object (dict-like)
    """
    prompt_begin = 'Enter '
    prompt = '{}'
    prompt_end = 'ᐅ '
    prompt_default = ' (default: {})'
    prompt_choices = ' (choices: {})'
    input_file = _sys.stdin

    class InputError(Exception):
        pass

    def __init__(self, print_file=_sys.stderr):
        """Create InputQuery instance.

        print_file is a file-like object where user-input prompts
        are written.
        """
        self.print_file = print_file
        self.is_tty = self.input_file.isatty()
        if self.is_tty:
            self._query = self._user_query
        else:
            self._query = self._stdin_read

    def _build_prompt(self, var, default=None, prompt=None, choices=None, **kw):
        """_build_prompt creates a prompt-string for querying the user.

        If passed a prompt string, it will simply return it unaltered.
        Otherwise it will create it from the given values.
        For example:
        >>> iq = InputQuery()
        >>> iq._build_prompt('SomeVar', default='no', choices=['yes', 'no'])
        "Enter SomeVar (default: no) (choices: ['yes', 'no'])ᐅ "
        """
        if prompt is None:
            prompt = self.prompt_begin + self.prompt.format(var)
        else:
            return prompt

        if default is not None:
            prompt += self.prompt_default.format(default)
        if choices is not None:
            prompt += self.prompt_choices.format(choices)
        prompt += self.prompt_end
        return prompt

    @staticmethod
    def _get_value(query_fn, transform, choices):
        """Query value, transform it, and validate it.

        Returns a tuple of (is_valid, transformed_value)
        """
        def validate(value, choices):
            if choices is None:
                return True
            if value in choices:
                return True
            else:
                return False
        raw_res = query_fn()
        res = transform(raw_res)
        valid = validate(res, choices)
        return valid, res, raw_res

    def __call__(self, var, default=None, choices=None, prompt=None,
                 hide=False, repeat=False, transform=_identity, **kwargs):
        """Query stdin for var"""
        query = _partial(self._query, var, default=default, choices=choices,
                         prompt=prompt, hide=hide, repeat=repeat, **kwargs)
        valid, res, raw_res = self._get_value(query, transform, choices)
        if valid:
            return QueryRes(var, res, raw_res)
        if not self.is_tty:
            raise ValueError('{} is not in {}'.format(res, choices))
        else:
            while not valid:
                self.qprint('{} is not in {}'.format(res, choices))
                valid, res, raw_res = self._get_value(query, transform, choices)
        return QueryRes(var, res, raw_res)

    def qprint(self, *args, sep=' ', end='\n'):
        "qprint is a wrapper for print, which writes to self.print_file"
        print(*args, sep=sep, end=end, file=self.print_file, flush=True)

    def _input(self, prompt, hide=False, repeat=False, **kw):
        """Prompt the tty-user and return the given value

        If hide is true it will not display the typed characters.
        """
        def getinp(prompt=prompt):
            self.qprint(prompt, end='')
            return _hidden_input('') if hide else input('')

        res = getinp()
        if repeat:
            res2 = getinp('Repeat ' + prompt)
            if res != res2:
                raise ValueError('{!r} != {!r}'.format(res, res2), prompt)
        return res

    def _user_query(self, var, *, allow_empty=False, **kw):
        kw['prompt'] = self._build_prompt(var, **kw)
        try:
            val = self._input(**kw)
        except KeyboardInterrupt as e:
            raise self.InputError('Received Ctrl-c from user', var) from e
        if val or allow_empty:
            return val
        else:
            if kw['default'] is not None:
                return kw['default']
            return self._user_query(var, allow_empty=allow_empty, **kw)

    def _stdin_read(self, var, **kw):
        "Get var from a json object read from stdin"
        try:
            jdat = self._json_dat
        except AttributeError:
            import json
            try:
                jdat = json.load(self.input_file)
            except json.decoder.JSONDecodeError as e:
                raise self.InputError('Could not decode json from stdin', var) from e
            self._json_dat = jdat
        if kw['default'] is not None:
            val = jdat.get(var, kw['default'])
        else:
            try:
                val = jdat[var]
            except KeyError as e:
                msg = 'The key {} was not given to stdin'.format(var)
                raise self.InputError(msg, var) from e
        return val


if __name__ == '__main__':
    iq = InputQuery()
    x = iq('SomeVar', default='yes', choices=['yes', 'no'])
    print(x)
    x = iq('AnotherVar', default='YES', choices=['YES', 'NO'], transform=str.upper)
    print(x)
    x = iq('password', hide=True, repeat=True)
    print(x)
