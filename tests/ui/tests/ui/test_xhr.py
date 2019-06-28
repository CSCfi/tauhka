#!/usr/bin/env python3
################################################################
# This file contains functional tests for the HelloWorld
#
# This file is part of Tauhka project.
#
# Author(s):
#     Juhapekka Piiroinen <juhapekka.piiroinen@csc.fi>
#
# Copyright 2019 CSC - IT Center for Science Ltd.
# All Rights Reserved.
################################################################

import os

from hellotestcase import HelloWorldTestCase, HelloWorldTestCaseReportAlways
from tauhka.testcase import TauhkaMemoryMonitor, TauhkaNetworkMonitor

from views.form import HelloForm


class HelloWorldXHRTest(HelloWorldTestCase):
    def start_test(self):
        self.start_memory_measure()
        self.open_url("http://127.0.0.1:8012")
        self.wait_until_window_title("Hello RPC")

    def end_test(self):
        if self.memory_usage_at_start:
            self.end_memory_measure_and_report()

    def test_1_send_xhr(self):
        self.start_test()

        form = HelloForm(testcase=self)

        # ensure that the field is empty
        assert form.afield.get_attribute("value") == ""

        # type in some text
        msg = "Hello World!"
        form.afield.send_keys(msg)

        # ensure that the value was changed
        assert form.afield.get_attribute("value") == msg

        expected_traffic = [
            {
                "request": ("POST", "http://127.0.0.1:8012/echo", "payload={msg}".format(msg=msg)),
                "response": ('200', msg)
            }
        ]
        with TauhkaNetworkMonitor(
                testcase=self,
                description="verify network traffic during form.submit",
                network_events=expected_traffic) as networkmonitor:
            with TauhkaMemoryMonitor(
                    testcase=self,
                    description="form.submit - memory usage max 200",
                    max_memory_diff=200) as monitor:
                form.submit()

        # check that the form data is now in pre
        self.wait_until_innerhtml("status_msg", msg)


class HelloWorldXHRTestReport(HelloWorldXHRTest, HelloWorldTestCaseReportAlways):
    pass
