cfg = dict(
    true_strs=['yes', 'y', 'true'],
    false_strs=['no', 'n', 'false'],
    pass_substrs=['password', 'pass'],
    default_hosts=['localhost'],
    templ_dirs=[('isna', 'playbook_templates'),],
    templ_ext=['yml', 'json'],
)

_common_ansi_vars = dict(
    ansible_python_interpreter = '/usr/bin/python2',
)

cfg['common_ansi_vars'] = _common_ansi_vars
