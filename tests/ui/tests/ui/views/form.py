#!/usr/bin/env python3
################################################################
# This file contains the helper wrapper for HelloWorld
#
# This file is part of Tauhka project.
#
# Author(s):
#     Juhapekka Piiroinen <juhapekka.piiroinen@csc.fi>
#
# Copyright 2019 CSC - IT Center for Science Ltd.
# All Rights Reserved.
################################################################


class HelloForm(object):
    def __init__(self, testcase):
        self.testcase = testcase
        self.theform = self.testcase.find_element("theform")
        self.afield = self.testcase.find_element_by_css("input[name=afield]")

    def submit(self):
        btn = self.theform.find_element_by_css_selector("input[type=submit]")
        btn.click()
