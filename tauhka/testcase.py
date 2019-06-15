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
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


class TauhkaMemoryMonitor(object):
    def __init__(self, testcase, description, max_memory_diff):
        self.testcase = testcase
        self.memory_usage_at_start = None
        self.description = description
        self.max_memory_diff = max_memory_diff

    def __enter__(self):
        timestamp = time.time() - self.testcase.test_start_time
        self.memory_usage_at_start = int(self.testcase.memory_usage())
        self.testcase.test_events.append((
            timestamp,
            self.testcase.id(),
            str(int(self.memory_usage_at_start/1024)),
            "-",
            "-",
            self.description,
            "-",
            str(self.max_memory_diff)
        ))

    def __exit__(self, type, value, tb):
        result = "FAILURE"
        memory_result = "OK"
        if tb is None:
            result = "OK"
        current_memory_usage = int(self.testcase.memory_usage())
        memory_diff, memory_end, memory_start = current_memory_usage - self.memory_usage_at_start, current_memory_usage, self.memory_usage_at_start
        timestamp = time.time() - self.testcase.test_start_time

        if self.max_memory_diff < int(memory_diff/1024):
            memory_result = "MEMORY_ISSUE"

        self.testcase.test_events.append((
            timestamp,
            self.testcase.id(),
            str(int(memory_start/1024)),
            str(int(memory_end/1024)),
            str(int(memory_diff/1024)),
            self.description,
            result,
            memory_result
        ))


class TauhkaTestCase(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        self.webdriver = "./chromedriver"
        self.report_always = False

    def setUp(self):
        self.memory_usage_at_start = None
        self.test_events = []
        self.start_time = int(time.time())

        caps = DesiredCapabilities.CHROME.copy()
        caps['loggingPrefs'] = {
            'browser': 'ALL',
            'performance': 'ALL',
        }
        opts = webdriver.ChromeOptions()
        opts.add_experimental_option('perfLoggingPrefs', {
            'enableNetwork': True,
            'enablePage': True,
            'traceCategories': "browser,devtools.timeline,devtools"
        })
        opts.add_argument("--no-sandbox")
        opts.add_argument("--js-flags=--expose-gc")
        if "TEST_DEBUG" not in os.environ.keys():
            opts.add_argument("--headless")
        opts.add_argument("--enable-precise-memory-info")
        self.test_start_time = time.time() + 1.25
        self.driver = webdriver.Chrome(self.webdriver, options=opts, desired_capabilities=caps)
        self.wait = WebDriverWait(self.driver, 10)

    def with_memory_usage(self, description, fn, *args, **kwargs):
        self.mark_memory_measure(description)
        fn(*args, **kwargs)
        self.diff_memory_measure_and_report(description)

    def start_memory_measure(self, description=None):
        if not description:
            description = "Test Started"
        timestamp = time.time() - self.test_start_time
        self.memory_usage_at_start = int(self.memory_usage())
        self.test_events.append((
            timestamp,
            self.id(),
            "-",
            "-",
            "-",
            description
        ))

    def end_memory_measure_and_report(self, description=None):
        if not description:
            description = "Test Ended"
        timestamp = time.time() - self.test_start_time
        memory_diff, memory_end, memory_start = self.end_memory_measure()
        self.test_events.append((
            timestamp,
            self.id(),
            str(int(memory_start/1024)),
            str(int(memory_end/1024)),
            str(int(memory_diff/1024)),
            description,
        ))

    def end_memory_measure(self):
        currentMemoryUsage = int(self.memory_usage())
        return currentMemoryUsage - self.memory_usage_at_start, currentMemoryUsage, self.memory_usage_at_start

    def mark_memory_measure(self, description):
        timestamp = time.time() - self.test_start_time
        self.memory_usage_at_mark = int(self.memory_usage())
        self.test_events.append((
            timestamp,
            self.id(),
            "-",
            "-",
            "-",
            description
        ))

    def diff_memory_measure(self):
        currentMemoryUsage = int(self.memory_usage())
        return currentMemoryUsage - self.memory_usage_at_mark, currentMemoryUsage, self.memory_usage_at_mark

    def diff_memory_measure_and_report(self, msg=None):
        timestamp = time.time() - self.test_start_time
        memory_diff, memory_end, memory_start = self.diff_memory_measure()
        self.test_events.append((
            timestamp,
            self.id(),
            str(int(memory_start/1024)),
            str(int(memory_end/1024)),
            str(int(memory_diff/1024)),
            msg,
        ))

    def memory_usage(self):
        self.driver.execute_script("window.gc()")
        return self.driver.execute_script("return window.performance.memory.usedJSHeapSize")

    def close(self):
        self.driver.close()

    def print(self, message):
        self.logger.info(message)

    def run(self, result=None):
        self.logger = logging.getLogger()
        self.logger.level = logging.INFO
        self.stream_handler = logging.StreamHandler(sys.stdout)
        self.logger.addHandler(self.stream_handler)
        self.network_logs = []
        self.console_logs = []

        errors_before = len(result.errors)
        failures_before = len(result.failures)

        super().run(result)

        was_failure = (errors_before != len(result.errors) or failures_before != len(result.failures))
        if self.report_always or was_failure:
            print("\n")
            print("======================================================================")
            status = "OK"
            if was_failure:
                if errors_before != len(result.errors):
                    status = "ERROR"
                status = "FAILURE"
            print("Test status ({testname}): {status}. ".format(testname=self.id(), status=status))
            print("----------------------------------------------------------------------")
            print("Console messages:")
            for entry in self.console_logs:
                print("{time:10.3f}".format(time=entry[0]), "\t".join(entry[1:]))
            print("----------------------------------------------------------------------")
            print("Network requests:")
            for entry in self.network_logs:
                print("{time:10.3f}".format(time=entry[0]), "\t".join(entry[1:]))
            print("----------------------------------------------------------------------")
            print("Tests and memory usage")
            for entry in self.test_events:
                print("{time:10.3f}".format(time=entry[0]), "\t".join(entry[1:]))
            print("----------------------------------------------------------------------")

        self.logger.removeHandler(self.stream_handler)

    def tearDown(self):
        # collect console logs
        for row in self.driver.get_log('browser'):
            self.console_logs.append((row['timestamp'], row['level'], row['message']))

        # collect network logs
        perfs = self.driver.get_log('performance')
        for row in perfs:
            if "message" in row.keys():
                msg = json.loads(row['message'])['message']
                if 'method' in msg.keys():
                    if "Network.requestWillBeSent" == msg['method']:
                        params = msg['params']
                        timestamp = params['timestamp']
                        requestId = str(params['requestId'])
                        request = params['request']
                        requestPostData = ""
                        try:
                            requestPostData = self.driver.execute_cdp_cmd('Network.getRequestPostData', {'requestId': requestId})
                        except WebDriverException:
                            pass
                        self.network_logs.append((
                            timestamp,
                            requestId,
                            "=>",
                            request['method'],
                            request['url'],
                            str(requestPostData)
                        ))
                    if "Network.responseReceived" == msg['method']:
                        params = msg['params']
                        timestamp = params['timestamp']
                        requestId = str(params['requestId'])
                        response = params['response']
                        status = response['status']
                        statusText = response['statusText']
                        body = ""
                        if status > 299 and status != 304:
                            try:
                                body = self.driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': requestId})
                            except WebDriverException:
                                pass
                        self.network_logs.append((
                            timestamp,
                            requestId,
                            "<=",
                            str(status),
                            statusText,
                            str(body)
                        ))

        if self.end_test:
            self.end_test()

        self.driver.quit()
        self.test_start_time = None

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

    def wait_until_hidden_by_id(self, elemId):
        return self.wait.until(EC.invisibility_of_element_located((By.ID, elemId)))

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

    def find_element_by_css(self, css_selector):
        return self.driver.find_element_by_css_selector(css_selector)

    def find_element_by_class_name(self, classname):
        return self.driver.find_element_by_class_name(classname)

    def open_url(self, url):
        self.driver.get(url)
