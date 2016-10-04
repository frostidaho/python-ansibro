import argparse
import os
import sys
from collections import namedtuple, OrderedDict


UserAction = namedtuple('UserAction', 'name action ask_pass')
cfg = dict(
    user_cmd_choices = ('sudo', 'ssh', 'su'),
    user_default = UserAction('root', 'sudo', 'no'),
    templ_dirs = (('isna', 'playbook_templates'),),
    templ_ext = ('yml', 'txt'),
)


class GetArgParser:
    ask_choices = ('yes', 'y', 'no', 'n')
    ask_true = ('yes', 'y')
    ask_false = ('no', 'n')

    def __init__(self):

        self.parser = argparse.ArgumentParser(
            description='Ansible-playbook wrapper',
            # formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )

    @staticmethod
    def _dirtype(parser, path):
        if not os.path.isdir(path):
            parser.error('{} is not a valid directory'.format(path))
        else:
            return os.path.abspath(path)

    @classmethod
    def _usertype(cls, parser, user, default=cfg['user_default'], choices=cfg['user_cmd_choices']):
        # print('_usertype() got', user)
        args = [x.strip() for x in user.split(',')]
        args = [x for x in args if x]
        if len(args) > len(default):
            msg = 'Only a max of {} values can be given with -u: {}'
            parser.error(msg.format(len(default), args))
        vals = list(default)
        for i,arg in enumerate(args):
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
        )


    def add_user_option(self):
        parser = self.parser
        dflt_ucmd = ','.join(cfg['user_default'])
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
            ).format(dflt_ucmd, cfg['user_cmd_choices'], self.ask_choices),
            type=lambda x: self._usertype(parser, x, default=cfg['user_default']),
            const=dflt_ucmd,
            metavar=umeta,
            nargs='?',
            action='append',
        )
        

def main(args=None):
    gap = GetArgParser()
    gap.add_list_args()
    gap.add_user_option()
    gap.add_options()
    gap.add_arguments()

    args = gap.parser.parse_args(args=args)
    # print('main(): args=', args)
    dargs = vars(args)
    if args.list_hosts:
        return list_hosts(**dargs)
    elif args.list_templates:
        return list_templates(**dargs)
    res = run(**dargs)
    if res != 0:
        gap.parser.print_help()
    return res
    

def get_templ_dirs(templ_dirs, default=cfg['templ_dirs']):
    total = []
    if templ_dirs is not None:
        total.extend(templ_dirs)
    total.extend(default)
    return total

def _query(var, allow_empty=False, password_types=('password', 'pass')):
    from getpass import getpass
    if any((x for x in password_types if x in var)):
        val = getpass(prompt=var)
        # val = getpass(prompt='Enter secret value for {}: '.format(var))
    else:
        val = input(var)
        # val = input('Enter value for {}: '.format(var))
    if val or allow_empty:
        return val
    else:
        return _query(var)

def query(*variables):
    od = OrderedDict()
    for var in variables:
        od[var] = _query('Enter value for {}: '.format(var))
    return od

# def args_to_ansible(extra_args, user, ask_pass, become_user,
#                     ask_become_pass, **kwargs):
#     ansid = {}
#     for k, v in extra_args:
#         ansid[k] = v
#     if user:
#         ansid['ansible_ssh_user'] = user
#     if ask_pass:
#         val = click.prompt('Enter ssh connectoin password', hide_input=True)
#         ansid['ansible_ssh_pass'] = val
#     if become_user:
#         # http://docs.ansible.com/ansible/become.html
#         ansid['ansible_become_user'] = become_user
#         ansid['ansible_become'] = True
#         ansid['ansible_become_method'] = 'sudo'
#     if ask_become_pass:
#         val = click.prompt('Enter su/sudo password', hide_input=True)
#         ansid['ansible_become_pass'] = val
#     return ansid

def _user_to_ansible(usr):
    pw_msg = 'Enter password for {}-{}: '
    d = {}
    if usr.action in ('sudo', 'su'):
        d['ansible_become'] = True
        d['ansible_become_method'] = usr.action
        d['ansible_become_user'] = usr.name
        if usr.ask_pass:
            # msg = 'password for {}:{}'.format(usr.name, usr.action)
            d['ansible_become_pass'] = _query(pw_msg.format(usr.name, usr.action))
    elif usr.action == 'ssh':
        d['ansible_ssh_user'] = usr.name
        if usr.ask_pass:
            # msg = 'password for {}:{}'.format(usr.name, usr.action)
            d['ansible_ssh_pass'] = _query(pw_msg.format(usr.name, usr.action))
            pass
        pass
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
    from isna.playbook import PBMaker, ansible_playbook
    templ_name = kwargs['playbook_template']
    if not templ_name:
        print('You need to enter a template to run.', file=sys.stderr)
        return 1

    def render():
        templ_dirs = get_templ_dirs(kwargs['templates'])
        pbm = PBMaker(*templ_dirs, host_list=[host])
        templ_name = kwargs['playbook_template']

        # print('extra_vars =', extra_vars)
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

    out = ansible_playbook(
        pb_text,
        [host],
        **extra_vars,
    )
    print(out.stdout.decode())
    print(out.stderr.decode())

    # print(pbm.undef_vars(templ_name, alpha=32))
    return 0

def list_hosts(**kwargs):
    from isna.get_hosts import get_hosts
    hosts = ['localhost']
    hosts.extend(get_hosts())
    print('\n'.join(x for x in hosts if x))
    return 0

def list_templates(**kwargs):
    from isna.playbook import PBMaker
    templ_dirs = get_templ_dirs(kwargs['templates'])
    # print('list_templates', kwargs['templates'])
    # print(templ_dirs)
    pbm = PBMaker(*templ_dirs)
    all_templates = pbm.list_templates(cfg['templ_ext'])
    print('\n'.join(all_templates))
    return 0

# x = query('a', 'b', 'c_password')
# print(x)
