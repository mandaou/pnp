import argparse
import sys


def parse_args(parser, commands):
    # Divide argv by commands
    split_argv = [[]]
    for c in sys.argv[1:]:
        if c in commands.choices:
            split_argv.append([c])
        else:
            split_argv[-1].append(c)
    # Initialize namespace
    args = argparse.Namespace()
    for c in commands.choices:
        setattr(args, c, None)
    # Parse each command
    parser.parse_args(split_argv[0], namespace=args)  # Without command
    for argv in split_argv[1:]:  # Commands
        n = argparse.Namespace()
        setattr(args, argv[0], n)
        parser.parse_args(argv, namespace=n)
    return args


def get_examples():
    example_string = """
Examples:
  Add:     pnps.py add     /google /AS1 /AS2 /AS3
  Remove:  pnps.py remove  /google /AS2
  Set:     pnps.py set     /google /AS4 /AS5
  Get:     pnps.py get     /google
  GetLpm:  pnps.py getlpm  /google2"""
    return example_string


def get_args():
    parent_parser = argparse.ArgumentParser(prog='pnpc.py', description='PNP Client for Publishers',
                                            epilog=get_examples(), formatter_class=argparse.RawTextHelpFormatter)

    parent_parser.add_argument('--config', nargs=1, metavar='ConfigFile', default='/etc/ndn/pnp/app.ini',
                        help='Configuration File. (Created by running: sudo ./runme.sh. Default: /etc/ndn/pnp/app.ini)')

    subparsers = parent_parser.add_subparsers(title='Available commands')

    parser_add = subparsers.add_parser('add', help='Use to add a new hosting AS for a given name')
    parser_add.add_argument('publisher_name', metavar='<Publisher Name>', nargs=1,
                            help='the name of publisher, i.e. /squ')
    parser_add.add_argument('as_list', metavar='<AS Numbers>', nargs='+',
                            help='a list of the hosting Autonomous System Numbers, i.e. /AS1 /AS2')

    parser_remove = subparsers.add_parser('remove', help='Use to remove an existing hosting AS for a given name')
    parser_remove.add_argument('publisher_name', metavar='<Publisher Name>', nargs=1,
                               help='the name of publisher, i.e. /squ')
    parser_remove.add_argument('as_list', metavar='<AS Numbers>', nargs='*',
                               help='a list of the hosting Autonomous System Numbers, i.e. /AS1 /AS2')

    parser_set = subparsers.add_parser('set', help='Wipe existing hosting ASes and set it to a new list')
    parser_set.add_argument('publisher_name', metavar='<Publisher Name>', nargs=1,
                            help='the name of publisher, i.e. /squ')
    parser_set.add_argument('as_list', metavar='<AS Numbers>', nargs='*',
                            help='a list of the hosting Autonomous System Numbers, i.e. /AS1 /AS2')

    parser_get = subparsers.add_parser('get', help='Get hosting ASes for a given publisher name')
    parser_get.add_argument('publisher_name', metavar='<Publisher Name>', nargs=1,
                            help='the name of publisher, i.e. /squ')

    parser_getlpm = subparsers.add_parser('getlpm', help='Get hosting ASes for a given publisher name or its LPM')
    parser_getlpm.add_argument('publisher_name', metavar='<Publisher Name>', nargs=1,
                               help='the name of publisher, i.e. /squ')

    args = parse_args(parent_parser, subparsers)
    return args
