#!/usr/bin/env python3
################################################################
# This contains the TauhkaTestCase.
#
# This file is part of Tauhka project.
#
# Author(s):
#     Juhapekka Piiroinen <juhapekka.piiroinen@csc.fi>
#
# Copyright (c) 2019 CSC - IT Center for Science Ltd.
# All Rights Reserved.
# ----
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
################################################################

import os
import sys
import logging
import unittest
import time
import json
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


class TauhkaTestCase(unittest.TestCase):
    def setUp(self):
        self.memory_usage_at_start = None
        self.test_events = []
        self.start_time = int(time.time())
        self.netlogfile = "{testcase}-{testmethod}-{timestamp}-networktraffic.json".format(
            timestamp=self.start_time,
            testcase=self.__class__.__name__,
            testmethod=self._testMethodName
        )
        self.netlogfiles.append(self.netlogfile)

        caps = DesiredCapabilities.CHROME.copy()
        caps['loggingPrefs'] = {
            'browser': 'ALL',
            'performance': 'ALL',
        }
        opts = webdriver.ChromeOptions()
        opts.add_argument("--no-sandbox")
        opts.add_argument("--js-flags=--expose-gc")
        if "TEST_DEBUG" not in os.environ.keys():
            opts.add_argument("--headless")
        opts.add_argument("--enable-precise-memory-info")
        opts.add_argument("--log-net-log={netlogfile}".format(netlogfile=self.netlogfile))
        opts.add_argument("--net-log-capture-mode=IncludeSocketBytes")
        self.test_start_time = time.time() + 1.25
        self.driver = webdriver.Chrome("./chromedriver", options=opts, desired_capabilities=caps)
        self.wait = WebDriverWait(self.driver, 10)

    def with_memory_usage(self, description, fn, *args, **kwargs):
        self.mark_memory_measure(description)
        fn(*args, **kwargs)
        self.diff_memory_measure_and_report(description)

    def start_memory_measure(self, description=None):
        if not description:
            description = "BEGIN"
        timestamp = time.time() - self.test_start_time
        self.memory_usage_at_start = int(self.memory_usage())
        self.test_events.append((timestamp, "{id} | {msg}".format(
            id=self.id(),
            msg=description
        )))

    def end_memory_measure_and_report(self, description=None):
        if not description:
            description = "END"
        timestamp = time.time() - self.test_start_time
        memory_diff, memory_end, memory_start = self.end_memory_measure()
        self.test_events.append((timestamp, "{id} | {msg} | JS Memory start: {start}Kb | end: {end}Kb | diff: {diff}Kb".format(
            id=self.id(),
            msg=description,
            start=int(memory_start/1024),
            end=int(memory_end/1024),
            diff=int(memory_diff/1024)
        )))

    def end_memory_measure(self):
        currentMemoryUsage = int(self.memory_usage())
        return currentMemoryUsage - self.memory_usage_at_start, currentMemoryUsage, self.memory_usage_at_start

    def mark_memory_measure(self, description):
        timestamp = time.time() - self.test_start_time
        self.memory_usage_at_mark = int(self.memory_usage())
        self.test_events.append((timestamp, "{id} | {msg}".format(
            id=self.id(),
            msg=description
        )))

    def diff_memory_measure(self):
        currentMemoryUsage = int(self.memory_usage())
        return currentMemoryUsage - self.memory_usage_at_mark, currentMemoryUsage, self.memory_usage_at_mark

    def diff_memory_measure_and_report(self, msg=None):
        timestamp = time.time() - self.test_start_time
        memory_diff, memory_end, memory_start = self.diff_memory_measure()
        self.test_events.append((timestamp, "{id} | {msg} | JS Memory start: {start}Kb | end: {end}Kb | diff: {diff}Kb".format(
            id=self.id(),
            msg=msg,
            start=int(memory_start/1024),
            end=int(memory_end/1024),
            diff=int(memory_diff/1024)
        )))

    def memory_usage(self):
        self.driver.execute_script("window.gc()")
        return self.driver.execute_script("return window.performance.memory.usedJSHeapSize")

    def close(self):
        self.driver.close()

    def print(self, message):
        self.logger.info(message)

    def run(self, result=None):
        self.netlogfiles = []
        self.logger = logging.getLogger()
        self.logger.level = logging.INFO
        self.stream_handler = logging.StreamHandler(sys.stdout)
        self.logger.addHandler(self.stream_handler)

        super().run(result)

        # analyze netlog
        for logfile in self.netlogfiles:
            print("")
            print("======================================================================")
            print("Test Report: " + self.id())
            print("----------------------------------------------------------------------")
            test_events_with_network = self.parse_netlog(logfile) + self.test_events
            test_events_with_network = sorted(test_events_with_network, key=lambda evt: evt[0])
            for event in test_events_with_network:
                print("{time:8.3f} | {data}".format(time=event[0], data=event[1]))
            print("\n")

        self.logger.removeHandler(self.stream_handler)

    def tearDown(self):
        if self.end_test:
            self.end_test()
        self.driver.quit()
        self.test_start_time = None

    def parse_netlog(self, netlog):
        retval = []
        data = ""
        with open(netlog, "r") as f:
            data += f.read()
        data = data.strip().rstrip(",")
        try:
            structure = json.loads(data + "]}")
        except json.decoder.JSONDecodeError:
            structure = json.loads(data)
        first_time = -1
        for event in structure['events']:
            if first_time == -1:
                first_time = int(event['time'])
            if event['source']['type'] == 1:
                if event['type'] == 166:
                    header = event['params']['headers']
                    headerdict = {}
                    for line in header:
                        if line.find(":") == 0:
                            line = line[1:]
                        (key, value) = line.split(":", 1)
                        headerdict[key] = value.strip()
                    actual_time = (int(event['time']) - first_time) / 1000
                    retval.append(
                        (
                            actual_time,
                            " => " + headerdict["method"] +
                            " " + headerdict['scheme'] +
                            " " + headerdict['authority'] +
                            " " + headerdict['path']
                        )
                    )
            if event['type'] == 101:
                location = event['params']['location']
                actual_time = (int(event['time']) - first_time) / 1000
                retval.append((actual_time, " URL CHANGED " + location))
            if event['type'] == 169:
                header = event['params']['headers']
                headerdict = {}
                for line in header:
                    try:
                        (key, value) = line.split(":", 1)
                        headerdict[key] = value
                    except ValueError:
                        pass
                if "location" in headerdict.keys():
                    actual_time = (int(event['time']) - first_time) / 1000
                    retval.append((actual_time, "REDIRECTED TO " + headerdict["location"]))
        return retval

    def elem_is_not_found(self, elemid):
        try:
            btn = self.driver.find_element_by_id(elemid)
            return False
        except NoSuchElementException:
            return True

    def elem_is_not_found_xpath(self, xpath):
        try:
            btn = self.driver.find_element_by_xpath(xpath)
            return False
        except NoSuchElementException:
            return True

    def scroll_to_element(self, elem):
        actions = ActionChains(self.driver)
        actions.move_to_element(elem)
        actions.perform()

    def scroll_to_up(self):
        self.driver.execute_script("window.scroll(0, 0);")

    def scroll_to_bottom(self):
        self.driver.find_element_by_tag_name('body').send_keys(Keys.END)

    def is_element_visible(self, elemId):
        return self.find_element(elemId).is_displayed()

    def click_elem(self, elemId):
        self.find_element(elemId).click()

    def select_option(self, elemId, option):
        self.select_option_by_text(elemId, option)

    def select_option_by_text(self, elemId, text):
        selectBox = Select(self.find_element(elemId))
        selectBox.select_by_visible_text(text)

    def select_option_by_value(self, elemId, value):
        selectBox = Select(self.find_element_by_id(elemId))
        selectBox.select_by_value(value)

    def is_option_selected(self, elemId, option):
        selectBox = Select(self.find_element(elemId))
        return option in selectBox.first_selected_option.text

    def enter_text(self, elemId, text):
        elem = self.find_element(elemId)
        elem.click()
        elem.send_keys(text)
        elem.send_keys(Keys.TAB)

    def wait_until_visible(self, elem):
        return self.wait.until(EC.visibility_of(elem))

    def wait_until_visible_by_id(self, elemId):
        return self.wait.until(EC.visibility_of(self.find_element(elemId)))

    def wait_until_window_title(self, title):
        return self.wait.until(EC.title_is(title))

    def wait_until_located_by_id(self, elemId):
        return self.wait.until(EC.presence_of_element_located((By.ID, elemId)))

    def wait_until_located_by_xpath(self, xpath):
        return self.wait.until(EC.presence_of_element_located((By.XPATH, xpath)))

    def wait_until_clickable_by_class(self, parent, class_name):
        return WebDriverWait(parent, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, class_name)))

    def clear_text(self, elemId):
        self.find_element(elemId).clear()

    def find_element(self, elemId):
        return self.wait.until(EC.presence_of_element_located((By.ID, elemId)))

    def find_element_by_id(self, elemId):
        return self.find_element(elemId)

    def find_element_by_name(self, elemName):
        return self.driver.find_element_by_name(elemName)

    def find_element_by_text(self, text):
        return self.driver.find_element_by_link_text(text)

    def find_element_by_xpath(self, xpath):
        return self.driver.find_element_by_xpath(xpath)

    def find_element_by_class_name(self, classname):
        return self.driver.find_element_by_class_name(classname)

    def open_url(self, url):
        self.driver.get(url)
