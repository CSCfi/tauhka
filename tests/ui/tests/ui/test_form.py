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

from hellotestcase import HelloWorldTestCase
from tauhka.testcase import TauhkaMemoryMonitor

from views.form import HelloForm


class HelloWorldFormTest(HelloWorldTestCase):
    def start_test(self):
        self.start_memory_measure()
        self.open_url("file://{current_path}/../../src/index.html".format(current_path=os.getcwd()))
        self.wait_until_window_title("Hello World")

    def end_test(self):
        if self.memory_usage_at_start:
            self.end_memory_measure_and_report()

    def test_1_send_message(self):
        self.start_test()

        form = HelloForm(testcase=self)

        # ensure that the field is empty
        assert form.afield.get_attribute("value") == ""

        # type in some text
        msg = "Hello World!"
        form.afield.send_keys(msg)

        # ensure that the value was changed
        assert form.afield.get_attribute("value") == msg

        with TauhkaMemoryMonitor(
                testcase=self,
                description="form.submit - memory usage max 200",
                max_memory_diff=200) as monitor:
            form.submit()

        # check that the form data is now in pre
        assert self.find_element("formpost").get_attribute("innerHTML") == msg
