import argparse
import os
import sys
from collections import namedtuple, OrderedDict

from isna.config import cfg
from isna.query import InputQuery

UserAction = namedtuple('UserAction', 'name action ask_pass')
USER_CMD_CHOICES = ('sudo', 'ssh', 'su')
USER_DEFAULT = UserAction('root', 'sudo', 'no')


class GetArgParser:
    ask_choices = cfg['true_strs'] + cfg['false_strs']
    ask_true = cfg['true_strs']
    ask_false = cfg['false_strs']

    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description='Ansible-playbook wrapper',
        )

    @staticmethod
    def _dirtype(parser, path):
        if not os.path.isdir(path):
            parser.error('{} is not a valid directory'.format(path))
        else:
            return os.path.abspath(path)

    @classmethod
    def _usertype(cls, parser, user, default=USER_DEFAULT,
                  choices=USER_CMD_CHOICES):
        # print('_usertype() got', user)
        args = [x.strip() for x in user.split(',')]
        args = [x for x in args if x]
        if len(args) > len(default):
            msg = 'Only a max of {} values can be given with -u: {}'
            parser.error(msg.format(len(default), args))
        vals = list(default)
        for i, arg in enumerate(args):
            vals[i] = arg
        if vals[1] not in choices:
            parser.error('2nd arg to user must be one of {}'.format(choices))
        vals[2] = vals[2].lower()
        if vals[2] not in cls.ask_choices:
            parser.error('3rd arg to user must be one of {}'.format(choices))
        if vals[2] in cls.ask_true:
            vals[2] = True
        else:
            vals[2] = False
        # print('_usertype() returning', vals)
        return UserAction(*vals)

    def add_list_args(self):
        listgrp = self.parser.add_mutually_exclusive_group(required=False)
        listgrp.add_argument(
            '-lh', '--list-hosts',
            action='store_true',
            help='List hosts on .local domain',
        )
        listgrp.add_argument(
            '-lt', '--list-templates',
            action='store_true',
            help='List available templates',
        )
        listgrp.add_argument(
            '-lv', '--list-vars',
            action='store_true',
            help='List vars in playbook template',
        )
        return listgrp

    def add_options(self):
        parser = self.parser
        dflt_host = 'localhost'
        parser.add_argument(
            '-hn', '--host',
            default=dflt_host,
            help='Run playbook on this host (default: {})'.format(dflt_host),
        )
        parser.add_argument(
            '-t', '--templates',
            help='Add a template directory',
            metavar='DIR',
            type=lambda x: self._dirtype(parser, x),
            action='append',
        )
        parser.add_argument(
            '-e', '--extra-vars',
            help='Supply variables for template.',
            metavar=('KEY', 'VALUE'),
            nargs=2,
            action='append',
            default=[],
        )

    def add_arguments(self):
        parser = self.parser
        parser.add_argument(
            'playbook_template',
            nargs='?',
            default='',
            type=str,
            help=("A playbook template's filename if it is in any of the templates directories. "
                  "Alternatively, it can be a relative or absolute path of a template.")
        )

    def add_user_option(self):
        parser = self.parser
        dflt_ucmd = ','.join(USER_DEFAULT)
        uvars = UserAction._fields
        umeta = '[,'.join(uvars) + ((len(uvars) - 1) * ']')
        umeta = umeta.upper()
        parser.add_argument(
            '-u', '--user',
            help=(
                'Do action as user.  '
                "If given with no args it defaults to '{}'.  "
                'Choices for actions are {}.  '
                'Choices for ask_pass are {}'
            ).format(dflt_ucmd, USER_CMD_CHOICES, self.ask_choices),
            type=lambda x: self._usertype(parser, x, default=USER_DEFAULT),
            const=dflt_ucmd,
            metavar=umeta,
            nargs='?',
            action='append',
        )


def parse_args(args=None):
    gap = GetArgParser()
    gap.add_list_args()
    gap.add_user_option()
    gap.add_options()
    gap.add_arguments()
    args = gap.parser.parse_args(args=args)
    return args, gap.parser.print_help


def get_templ_dirs(templ_dirs, default=cfg['templ_dirs']):
    total = []
    if templ_dirs is not None:
        total.extend(templ_dirs)
    total.extend(default)
    return total


def main(args=None):
    "main() is the entry point for the isna script"
    args, print_help = parse_args(args)

    dargs = vars(args)
    templ_name = dargs['playbook_template']
    templ_dirs = dargs['templates']
    if templ_dirs is None:
        templ_dirs = []
    if os.path.isfile(templ_name):
        _templ_path = os.path.realpath(templ_name)
        templ_dirs.append(os.path.dirname(_templ_path))
        templ_name = os.path.basename(_templ_path)
    dargs['playbook_template'] = templ_name
    dargs['templates'] = get_templ_dirs(templ_dirs)

    if args.list_hosts:
        return list_hosts(**dargs)
    elif args.list_templates:
        return list_templates(**dargs)
    elif args.list_vars:
        return list_template_vars(**dargs)

    res = run(**dargs)
    if res != 0:
        print_help()
    return res

inpq = InputQuery()
def _query(var, password_types=cfg['pass_substrs']):
    # iq = InputQuery()
    if any((x for x in password_types if x in var)):
        qres = inpq(var, hide=True, repeat=True)
    else:
        qres = inpq(var)
    return qres.result

def query(*variables):
    od = OrderedDict()
    for var in variables:
        od[var] = _query(var)
    return od


def _user_to_ansible(usr):
    pw_msg = '{}_{}_pass'
    d = {}
    if usr.action in ('sudo', 'su'):
        d['ansible_become'] = True
        d['ansible_become_method'] = usr.action
        d['ansible_become_user'] = usr.name
        if usr.ask_pass:
            # TODO: Make query() here such that if 'user_action_pass' is not given
            # that instead of raising an exception it goes on to try ansible_become_pass
            # or ansible_ssh_pass depending
            d['ansible_become_pass'] = _query(pw_msg.format(usr.name, usr.action))
    elif usr.action == 'ssh':
        d['ansible_ssh_user'] = usr.name
        if usr.ask_pass:
            d['ansible_ssh_pass'] = _query(pw_msg.format(usr.name, usr.action))
    else:
        raise ValueError('User action "{}" is not supported.'.format(usr.action))
    return d


def user_to_ansible(user_args):
    if user_args is None:
        return {}
    udict = {}
    for uaction in user_args:
        udict.update(_user_to_ansible(uaction))
    return udict


def run(host, **kwargs):
    from isna.playbook import PBMaker, AnsiblePlaybook

    if not kwargs['playbook_template']:
        print('You need to enter a template to run.', file=sys.stderr)
        return 1

    def render():
        pbm = PBMaker(*kwargs['templates'], host_list=[host])
        templ_name = kwargs['playbook_template']
        pbm.update(extra_vars)
        undef = pbm.undef_vars(templ_name)
        queried_vars = query(*sorted(undef))
        return pbm.render(templ_name, **queried_vars)

    extra_vars = OrderedDict(kwargs['extra_vars'])
    pb_text = render()
    if host == 'localhost':
        extra_vars['ansible_connection'] = 'local'
    extra_vars.update(user_to_ansible(kwargs['user']))
    print(pb_text)

    with AnsiblePlaybook(pb_text, [host], **extra_vars) as pb:
        out = pb.run()
    if out.stdout:
        print(out.stdout.decode())
    if out.stderr:
        print(out.stderr.decode())
    return out.returncode


def list_hosts(**kwargs):
    from isna.util import get_hosts
    hosts = ['localhost']
    hosts.extend(get_hosts())
    print('\n'.join(x for x in hosts if x))
    return 0


def list_templates(**kwargs):
    from isna.playbook import PBMaker
    pbm = PBMaker(*kwargs['templates'])
    all_templates = pbm.list_templates(cfg['templ_ext'])
    print('\n'.join(all_templates))
    return 0


def list_template_vars(**kwargs):
    from isna.playbook import PBMaker
    pbm = PBMaker(*kwargs['templates'])
    tname = kwargs['playbook_template']
    if not tname:
        print('Must give a playbook template for --list-vars', file=sys.stderr)
        return 1
    all_vars = sorted(pbm.all_vars(tname))
    if all_vars:
        print('\n'.join(all_vars))
    else:
        print("Template '{}' has no variables".format(tname), file=sys.stderr)
    return 0

