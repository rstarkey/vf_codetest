import collections
from nose.tools import *
from vf_start import *
# -*- coding: utf-8 -*-
"""
Purpose: Code Test - Start the services of a Veriflow system specified in the config file
Author: Robert Starkey <rstarkey@gmail.com>
Date: 10/11/2017
License: Nada, all yours.
Requires: python 3.6+
"""


class TestVFConfig:

    cfg = object

    def setup(self):
        self.cfg = VFConfig()

    @raises(FileNotFoundError)
    def test_bad_filename(self):
        """
        Test bad config file name
        :return:
        """
        self.cfg.read(filename="tests/cfg/asasfsfdsdfbad_line.cfg")
        assert False

    @raises(ConfigError)
    def test_bad_line(self):
        """
        Test config parser with a bad config line
        :return:
        """
        self.cfg.read(filename="tests/cfg/bad_line.cfg")
        assert False

    @raises(ConfigError)
    def test_missing_name(self):
        """
        feed config parser a line missing a name (required)
        :return:
        """
        self.cfg.read(filename="tests/cfg/missing_name.cfg")
        assert False

    @raises(ConfigError)
    def test_missing_cmd(self):
        """
        feed config parser a line missing a name (required)
        :return:
        """
        self.cfg.read(filename="tests/cfg/missing_cmd.cfg")
        assert False

    def test_split_regex(self):
        """
        test_split_regex: Send it good data and see if we get back what we expect
        :return:
        """
        self.cfg.read(filename="tests/cfg/good.cfg")
        tdata = ['test_name', 1, 2, 'test_stdin', 'test_stdout', 'test_stderr', 'test_cmd']

        # does the parse data return the expect number of elements?
        for proc in self.cfg.procs:
            assert len(tdata) == len(proc.keys())
            # does the data returned match the values we're expecting
            for i, key in enumerate(proc.keys()):
                assert proc[key] == tdata[i]

    def test_quoted_cmd(self):
        """
        test_quoted_cmd: Feed it a quoted cmd with a delimiter in it.
        :return:
        """
        self.cfg.read(filename="tests/cfg/run_cmd.cfg")
        assert self.cfg.procs[0].get("cmd", "nope") == 'echo "test : worked"'

    def test_start_order(self):
        """
        test_start_order: test to make sure that the start order sorter works as expected
        :return:
        """
        self.cfg.procs = [{'name': 'three', 'count': 1, 'order': 3, 'stdin': '', 'stdout': '', 'stderr': '',
                           'cmd': 'echo'},
                          {'name': 'last', 'count': 1, 'order': 100, 'stdin': '', 'stdout': '', 'stderr': '',
                           'cmd': 'echo'},
                          {'name': 'two', 'count': 1, 'order': 2, 'stdin': '', 'stdout': '', 'stderr': '',
                           'cmd': 'echo'},
                          {'name': 'one', 'count': 1, 'order': 1, 'stdin': '', 'stdout': '', 'stderr': '',
                           'cmd': 'echo'}]

        self.cfg.start_order_sort()
        assert self.cfg.procs[0]['name'] == "one" and self.cfg.procs[3]['name'] == "last"


class TestVFPRocess:
    cfg = object
    procmgr = VFProcessMgr()

    def setup(self):
        self.cfg = VFConfig()
        self.procmgr.pidlist = collections.OrderedDict([("zzz", 1234), ("ggg", 3212), ("aaa", 54322)])

    def test_spawn(self):
        """
        test_spawn: Test to see if spawn works
        :return:
        """
        self.cfg.read(filename="tests/cfg/run_cmd.cfg")
        self.procmgr.startup(self.cfg.procs)
        assert self.procmgr.pidlist['run_cmd_name']

    def test_spawn_bad_cmd(self):
        """
        test_spawn_bad_cmd: spawning a bad cmd should result in a pid of None
        :return:
        """
        self.cfg.read(filename="tests/cfg/bad_cmd.cfg")
        self.procmgr.startup(self.cfg.procs)
        assert self.procmgr.pidlist['bad_cmd_name']

    def test_unsorted_output(self):
        """
        test_unsorted_output: The output order should be exactly what we sent it
        :return:
        """
        class FakeArgs:
            svc_sort_order = False

        args = FakeArgs()
        self.procmgr.sort_output(args)
        assert list(self.procmgr.pidlist)[0] == "zzz"

    def test_sorted_output(self):
        """
        test_sorted_output: The output order should be sorted by service name
        :return:
        """
        class FakeArgs:
            svc_sort_order = True

        args = FakeArgs()
        self.procmgr.sort_output(args)
        assert list(self.procmgr.pidlist)[0] == "aaa"
