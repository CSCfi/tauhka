#!/usr/bin/env python3
################################################################
# This contains the base class HelloWorldTestCase with some helper
# functions for tests.
#
# This file is part of Tauhka project.
#
# Author(s):
#     Juhapekka Piiroinen <juhapekka.piiroinen@csc.fi>
#
# Copyright (c) 2019 CSC - IT Center for Science Ltd.
# All Rights Reserved.
################################################################

from tauhka.testcase import TauhkaTestCase
from selenium.common.exceptions import NoSuchElementException, TimeoutException


class HelloWorldTestCase(TauhkaTestCase):
    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        self.report_always = True
