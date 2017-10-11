#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
"""
Purpose: Code Test - Start the services of a Veriflow system specified in the config file
Author: Robert Starkey <rstarkey@gmail.com>
Date: 10/11/2017
License: Nada, all yours.
Requires: python 3.6+
"""

import argparse
import logging
import subprocess
from collections import OrderedDict
import sys
import os
import re
import shlex
from operator import itemgetter
# from pprint import pprint

# TODO Unit test to check for good config
# TODO Unit test to check spawning works
# TODO Unit test to check if start order is correct
# TODO unit test to check if output sort order is correct
# TODO unit test to check if config regex is working
# TODO unit test for required config fields

# Global to define config file fields, this way you don't have to run through my ugly code to add new fields
CONFIG_FIELDS = OrderedDict({'name': True, 'count': '1', 'order': '0', 'stdin': '/dev/null', 'stdout': '/dev/null',
                            'stderr': '/dev/null', 'cmd': True})


class ConfigError(Exception):
    """
    Raise for config errors
    """
    pass


class VFConfig:
    """
    class for config data and supporting methods
    """
    filename = None
    procs = []

    def __init__(self, filename):
        self.filename = filename
        self.read(filename)
        if self.procs:
            self.start_order_sort()

    def read(self, filename):
        """
        parse and validate config
        :param filename: file system path of the config file to be opened and parsed
        """
        # This regex sucks but it'll do for now
        # For every delimiter found, look forward to see if there is an even number of quotes, if so, delimiter!
        # this allows for fun stuff like blah:/bin/bash -c "echo `date` : $$ (nice one, BTW)
        _line_re = re.compile(r""":(?=(?:[^'"]|'[^']*'|"[^"]*")*?$)""")
        _is_num_re = re.compile(r"""^\d+$""")
        try:
            with open(filename, "r") as fObj:
                try:
                    for _line_num, _line in enumerate(fObj):
                        _line = _line.strip()
                        # strip comments
                        if not _line or _line.startswith('#'):
                            continue

                        logging.debug(f"Line: ({_line})")
                        _match = _line_re.split(_line)

                        # does the matched split match the number of expected fields? if not, warn
                        if _match and (len(_match) == len(CONFIG_FIELDS)):
                            logging.debug(f"good config line: {_match}")
                            _fields = {}
                            for i, _field in enumerate(CONFIG_FIELDS.keys()):
                                _match[i] = _match[i].strip()
                                if not _match[i]:
                                    # put in the default values if the field is empty
                                    _match[i] = CONFIG_FIELDS.get(_field, _match[i])
                                    # if the field is empty but the default is 'True', it's a required field
                                    if _match[i] is True:
                                        raise ConfigError(f"Missing required field ({_field}) at {filename}:"
                                                          f"{_line_num}: \"{_line}\"")

                                is_num = _is_num_re.match(_match[i])
                                # does it look like a number?  If so, cast it, makes sorting work as expected
                                if is_num:
                                    _match[i] = int(_match[i])
                                _fields.update({_field: _match[i]})

                            self.procs.append(_fields)
                        else:
                            raise ConfigError(f"Invalid config line format at {filename}:{_line_num}: \"{_line}\"")
                except ConfigError as err:
                    # Stop if there is a config error and display which line we don't like
                    logging.exception(err, exc_info=False)
                    sys.exit(1)

        except OSError:
            raise

    def start_order_sort(self):
        """
        sort the process list into start order based on 'order' config
        """
        self.procs = sorted(self.procs, key=lambda x: itemgetter("order")(x))


class VFProcessMgr:
    """
    Class to manage processes
    """
    # orderdict is used to preserve execution order, sorting happens later
    pidlist = OrderedDict()

    def __init__(self):
        pass

    @staticmethod
    def spawn(proccfg):
        """
        spwan the process
        :param proccfg: VFConfig object
        :return: pid of the process or None if there was an error spawning
        """
        logging.debug(f"spawning {proccfg}")

        _proc = None
        # not in the spec but having a visual that one of your commands failing to spawn is most helpful
        _pid = None

        try:
            _stdin = open(proccfg['stdin'])
            _stdout = open(proccfg['stdout'], "a+")
            _stderr = open(proccfg['stderr'], "a+")

        except OSError as err:
            logging.error(f"OS Error: {err}")
            # not exactly in the spec but halting exec at this point seems like a good idea.
            raise

        # as a general rule, I don't like having shell=True but since we trust people writing the config
        # (Hold my beer, watch this) when we add commands, passing the command to the shell will allow tricks like $$
        # and back ticks.  Lastly, close_fds because zombies are no fun!
        _cmd = shlex.split(proccfg['cmd'])
        logging.debug(f"running {_cmd}")
        try:
            _proc = subprocess.Popen(_cmd, shell=False, stdin=_stdin, stdout=_stdout, stderr=_stderr,
                                     close_fds=True)
        except FileNotFoundError as err:
            logging.warning(f"{err}")
            pass

        _stdin.close()
        _stdout.close()
        _stderr.close()

        if _proc:
            _pid = _proc.pid

        logging.debug(f"PID: {_pid}")
        return _pid

    def startup(self, procs):
        """
        run through the config and spawn the processes, keeping track of the name and pid
        """
        for cfg in procs:
            _spawncount = 0
            _pidlist = []
            while _spawncount < int(cfg['count']):
                # TODO checking for more than pid would be a great idea but not in the spec
                _pid = self.spawn(cfg)
                _spawncount += 1
                _pidlist.append(_pid)

            self.pidlist.update({cfg['name']: _pidlist})


def sortoutput(args, alist):
    """
    sort output based on args passed on command line (-s)
    :param args: argparse object
    :param alist: a list of tups to sort
    """
    if args.svc_sort_order:
        logging.debug(f"sorting output because -s")
        # sort the tuple by the first element
        alist = OrderedDict(sorted(alist.items(), key=lambda x: x[0]))

    return alist


def main(args, loglevel):
    """
    Main
    :param args: argparse object
    :param loglevel: logging level
    :return:
    """
    logging.basicConfig(format="%(levelname)s: %(message)s", level=loglevel)
    logging.debug("Your Argument: %s" % args)

    # as a general rule, scripts like this shouldn't run as root because they can do a lot of damage
    if os.getuid() == 0:
        logging.error("Cannot run as root.")
        sys.exit(1)

    # get config
    cfg = VFConfig(args.cfg_file)

    procmgr = VFProcessMgr()
    procmgr.startup(cfg.procs)

    for _name, _pids in sortoutput(args, procmgr.pidlist).items():
            print(f"{_name}:", ','.join(str(x) for x in _pids))


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Start the services of a Veriflow system")
    # surpress -d debug from showing up in the help output because it's not part of the spec
    parser.add_argument("-d", dest="debug", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("-s", dest="svc_sort_order", help="sort the output by service name", action="store_true")
    parser.add_argument("-c", dest="cfg_file", help="specifies the config file", required=True)
    _args = parser.parse_args()

    if _args.debug:
        _loglevel = logging.DEBUG
    else:
        _loglevel = logging.INFO

    main(_args, _loglevel)
