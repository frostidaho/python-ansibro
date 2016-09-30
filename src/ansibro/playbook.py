from __future__ import print_function
# Blog post going over the Ansible2 python api
# https://serversforhackers.com/running-ansible-2-programmatically
# https://serversforhackers.com/running-ansible-programmatically
import os
from collections import namedtuple

from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.playbook import Playbook
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.template import Templar

from jinja2 import meta


Options = namedtuple(
    'Options',
    ['connection','module_path', 'forks', 'remote_user',
     'private_key_file', 'ssh_common_args', 'ssh_extra_args', 'sftp_extra_args',
     'scp_extra_args', 'become', 'become_method', 'become_user', 'verbosity', 'check']
)


class TQMArgs(object):
    def __init__(self, host_list=('localhost',)):
        self.host_list = host_list

    @property
    def host_list(self):
        return self._host_list

    @host_list.setter
    def host_list(self, val):
        self._host_list = list(val)

    @property
    def variable_manager(self):
        try:
            return self._variable_manager
        except AttributeError:
            variable_manager = VariableManager()
            ev = variable_manager.extra_vars
            ev.update({'ansible_python_interpreter': '/usr/bin/python2',})
            variable_manager.extra_vars = ev
            self._variable_manager = variable_manager
            return self._variable_manager

    def __getitem__(self, key):
        return self.variable_manager.extra_vars[key]

    def __setitem__(self, key, val):
        ev = self.variable_manager.extra_vars
        ev[key] = val
        self.variable_manager.extra_vars = ev

    @property
    def loader(self):
        try:
            return self._loader
        except AttributeError:
            self._loader = DataLoader()
            return self._loader

    @property
    def inventory(self):
        try:
            return self._inventory
        except AttributeError:
            self._inventory = Inventory(
                loader=self.loader,
                variable_manager=self.variable_manager,
                host_list=self.host_list,
            )
            self.variable_manager.set_inventory(self._inventory)
            self._set_localhost_opts(self._inventory)
            return self._inventory

    @staticmethod
    def _set_localhost_opts(inventory):
        localhost = inventory.get_host('localhost')
        localhost.set_variable('ansible_connection', 'local')

    @property
    def options(self):
        try:
            return self._options
        except AttributeError:
            self._options = Options(
                connection='smart', module_path=None, forks=5,
                remote_user=None, private_key_file=None, ssh_common_args=None,
                ssh_extra_args=None, sftp_extra_args=None, scp_extra_args=None,
                become=None, become_method=None, become_user=None,
                verbosity=0, check=False,
            )
            return self._options

    @property
    def passwords(self):
        return dict()

    def load_playbook(self, playbook_path):
        pb = Playbook.load(
            playbook_path,
            variable_manager=self.variable_manager,
            loader=self.loader,
        )
        return pb

    def new_task_queue_mgr(self, **kwargs):
        attribs = ['inventory', 'variable_manager', 'loader',
                   'options', 'passwords']
        tqm_kwargs = {}
        for name in attribs:
            try:
                tqm_kwargs[name] = kwargs[name]
            except KeyError:
                tqm_kwargs[name] = getattr(self, name)
        tqm = TaskQueueManager(**tqm_kwargs)
        return tqm


def missing_vars(playbook, play):
    pb_name = os.path.basename(playbook._file_name)

    all_vars = var_mgr.get_vars(loader=loader, play=play)
    templar = Templar(loader=loader, variables=all_vars)
    env = templar.environment
    env.loader.searchpath = [os.path.dirname(playbook._file_name),]
    ts = env.loader.get_source(env, pb_name)[0]
    parsed_content = env.parse(ts)
    
    jinja_undef_var = meta.find_undeclared_variables(parsed_content)
    undef_var = jinja_undef_var - set(var_mgr.get_vars(loader, play))
    return undef_var


# if __name__ == '__main__':
#     tqmargs = TQMArgs(['localhost'])
#     var_mgr = tqmargs.variable_manager
#     loader = tqmargs.loader
#     inv = tqmargs.inventory
#     opt = tqmargs.options

#     tqm = tqmargs.new_task_queue_mgr()
#     TESTPB = '/home/ida/Dropbox/htmp/ansible/test.yml'
#     pb = tqmargs.load_playbook(TESTPB)
#     tqmargs['password'] = 'some password'

#     for play in pb.get_plays():
#         mv = missing_vars(pb, play)
#         print(mv)

#         x = tqm.run(play)

