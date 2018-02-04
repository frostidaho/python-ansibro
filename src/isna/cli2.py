"""Isna

Usage:
  isna ls temp [--dir=<dir>]...
  isna ls vars [--dir=<dir>]... TEMPLATE...
  isna ls hosts [--domain=<domain>]
  isna [--dir=<dir>]... [--vars=<xtra>] [--ssh=<user@host:port>] [--sudo=<user>] TEMPLATE...
  isna (-h | --help | --version)

Options:
  --dir=<dir>             Additional template directory.
  --ssh=<user@host:port>  Connect as user to host using ssh
  --sudo=<user>           Sudo to this user after connection
  --domain=<domain>       Avahi-domain [default: .local]
  --vars=<vars>           Extra variables for TEMPLATE and ansible
  -h --help               Show this screen.
  --version               Show version.
"""
import sys
from docopt import docopt


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
        if '--debug' in argv:
            del argv[argv.index('--debug')]
            debug = True
        else:
            debug = False

    args = docopt(__doc__, version='Isna v0.2.0', argv=argv)
    args.pop('--help', None), args.pop('--version', None)
    import isna.cli as cli
    return cli.main(debug=debug, **args)
