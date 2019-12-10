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
import base64
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
        self.testcase.memory_logs.append((
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

        self.testcase.memory_logs.append((
            timestamp,
            self.testcase.id(),
            str(int(memory_start/1024)),
            str(int(memory_end/1024)),
            str(int(memory_diff/1024)),
            self.description,
            result,
            memory_result
        ))


class TauhkaNetworkMonitor(object):
    def __init__(self, testcase, description, network_events):
        self.testcase = testcase
        self.network_monitor_start = None
        self.description = description
        self.network_events = network_events

    def __enter__(self):
        self.network_monitor_start = time.time() - self.testcase.test_start_time
        # add current events to log, it will clear things for monitoring too
        self.testcase.network_logs += self.testcase.collect_network_requests()

    def __exit__(self, type, value, tb):
        result = "FAILURE"
        network_result = "OK"
        if tb is None:
            result = "OK"

        timestamp = time.time() - self.testcase.test_start_time
        max_tries = 10
        tries = 0
        network_requests = []
        while self.network_events:
            assert max_tries > tries, "Network traffic was incorrect."

            network_events_new = self.testcase.collect_network_requests(fetch_body_always=True)
            network_requests += network_events_new
            self.testcase.network_logs += network_events_new

            parsed_requests = {}

            for req in network_requests:
                request_timestamp = req[0]
                request_id = req[1]
                request_type = req[2]
                if request_id not in parsed_requests.keys():
                    parsed_requests[request_id] = {"request": None, "response": None}
                if request_type == "=>":
                    request_method = req[3]
                    request_url = req[4]
                    request_data = req[5]
                    parsed_requests[request_id]["request"] = (request_method, request_url, request_data)
                else:
                    response_status = req[3]
                    response_statusText = req[4]
                    response_text = req[5]
                    parsed_requests[request_id]["response"] = (req[3], req[5])

            for key in parsed_requests.keys():
                event = self.network_events[0]
                found_event = parsed_requests[key]
                is_ok = True
                for key in event.keys():
                    ev = event[key]
                    if ev:
                        ev_count = len(event[key])
                    else:
                        ev_count = 0
                    ev_found = found_event[key]
                    if ev_found:
                        ev_found_count = len(found_event[key])
                    else:
                        ev_found_count = 0
                    is_ok = ev_count == ev_found_count
                    if not is_ok:
                        break
                    for i in range(ev_count):
                        is_ok = ev[i] == ev_found[i]
                        if not is_ok:
                            break
                if is_ok:
                    self.network_events.pop(0)

            tries += 1
            if self.network_events:
                time.sleep(0.5)


class TauhkaTestCase(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        self.webdriver = os.environ.get("TAUHKA_WEBDRIVER", "./chromedriver")
        self.browser = os.environ.get("TAUHKA_BROWSER", "chrome")
        self.time_adjust = float(os.environ.get("TAUHKA_TIMEOFFSET", 1.25))
        self.default_wait = int(os.environ.get("TAUHKA_DEFAULT_WAIT", 10))
        self.maximum_wait = int(os.environ.get("TAUHKA_MAX_WAIT", 30))
        self.extra_logging = bool(os.environ.get("TAUHKA_EXTRA_LOGS", True))
        self.report_always = False

    def setUp(self):
        self.memory_usage_at_start = None
        self.memory_logs = []
        self.start_time = int(time.time())
        self.test_start_time = time.time() + self.time_adjust
        if "chrome" in self.browser:
            caps = DesiredCapabilities.CHROME.copy()
            if self.extra_logging:
                caps['goog:loggingPrefs'] = {
                    'browser': 'ALL',
                    'performance': 'ALL',
                }
                caps['loggingPrefs'] = caps['goog:loggingPrefs']
            opts = webdriver.ChromeOptions()
            if self.extra_logging:
                opts.add_experimental_option('perfLoggingPrefs', {
                    'enableNetwork': True,
                    'enablePage': True,
                    'traceCategories': "browser,devtools.timeline,devtools"
                })
                opts.add_argument("--js-flags=--expose-gc")
                opts.add_argument("--enable-precise-memory-info")
                opts.add_argument("--no-sandbox")
            if "TEST_DEBUG" not in os.environ.keys():
                opts.add_argument("--headless")
            self.driver = webdriver.Chrome(self.webdriver, options=opts, desired_capabilities=caps)
        else:
            self.driver = webdriver.Firefox(self.webdriver)
        self.driver.implicitly_wait(self.default_wait)
        self.wait = WebDriverWait(self.driver, self.maximum_wait)

    def with_memory_usage(self, description, fn, *args, **kwargs):
        self.mark_memory_measure(description)
        fn(*args, **kwargs)
        self.diff_memory_measure_and_report(description)

    def start_memory_measure(self, description=None):
        if not self.extra_logging:
            return
        if not description:
            description = "Test Started"
        timestamp = time.time() - self.test_start_time
        self.memory_usage_at_start = int(self.memory_usage())
        self.memory_logs.append((
            timestamp,
            self.id(),
            "-",
            "-",
            "-",
            description
        ))

    def end_memory_measure_and_report(self, description=None):
        if not self.extra_logging:
            return
        if not description:
            description = "Test Ended"
        timestamp = time.time() - self.test_start_time
        memory_diff, memory_end, memory_start = self.end_memory_measure()
        self.memory_logs.append((
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
        if not self.extra_logging:
            return
        timestamp = time.time() - self.test_start_time
        self.memory_usage_at_mark = int(self.memory_usage())
        self.memory_logs.append((
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
        if not self.extra_logging:
            return
        timestamp = time.time() - self.test_start_time
        memory_diff, memory_end, memory_start = self.diff_memory_measure()
        self.memory_logs.append((
            timestamp,
            self.id(),
            str(int(memory_start/1024)),
            str(int(memory_end/1024)),
            str(int(memory_diff/1024)),
            msg,
        ))

    def memory_usage(self):
        if not self.extra_logging:
            return 0
        self.driver.execute_script("window.gc()")
        return self.driver.execute_script("return window.performance.memory.usedJSHeapSize")

    def close(self):
        self.driver.close()

    def write_to_log(self, message):
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

        if self.extra_logging:
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
                if self.console_logs:
                    print("Console messages:")
                    for entry in self.console_logs:
                        print("{time:10.3f}".format(time=entry[0]), "\t".join(entry[1:]))
                    print("")
                if self.network_logs:
                    print("Network requests:")
                    for entry in self.network_logs:
                        print("{time:10.3f}".format(time=entry[0]), "\t".join(entry[1:]))
                    print("")
                if self.console_logs:
                    print("Tests and memory usage")
                    for entry in self.memory_logs:
                        print("{time:10.3f}".format(time=entry[0]), "\t".join(entry[1:]))

        self.logger.removeHandler(self.stream_handler)

    def collect_javascript_console(self):
        retval = []
        if "chrome" not in self.browser:
            return retval
        for row in self.driver.get_log('browser'):
            retval.append((row['timestamp'], row['level'], row['message']))
        return retval

    def collect_network_requests(self, fetch_body_always=False):
        retval = []
        if "chrome" not in self.browser or not self.extra_logging:
            return retval
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
                            if isinstance(requestPostData, dict):
                                if "postData" in requestPostData:
                                    requestPostData = requestPostData["postData"]

                        except WebDriverException:
                            pass
                        retval.append((
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
                        if fetch_body_always or (status > 299 and status != 304):
                            try:
                                body = self.driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': requestId})
                            except WebDriverException:
                                pass
                            if isinstance(body, dict):
                                if "base64Encoded" in body:
                                    if body["base64Encoded"]:
                                        body = base64.b64decode(body["body"])
                            if isinstance(body, dict):
                                if "body" in body:
                                    body = body["body"]
                        retval.append((
                            timestamp,
                            requestId,
                            "<=",
                            str(status),
                            statusText,
                            str(body)
                        ))
        return retval

    def tearDown(self):
        if self.extra_logging:
            self.console_logs += self.collect_javascript_console()
            self.network_logs += self.collect_network_requests()

        if self.end_test:
            self.end_test()

        self.driver.quit()
        self.test_start_time = None

    def end_test(self):
        pass

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

    def wait_until_window_title_contains(self, title):
        return self.wait.until(EC.title_contains(title))

    def wait_until_located_by_id(self, elemId):
        return self.wait.until(EC.presence_of_element_located((By.ID, elemId)))

    def wait_until_located_by_xpath(self, xpath):
        return self.wait.until(EC.presence_of_element_located((By.XPATH, xpath)))

    def wait_until_clickable_by_class(self, parent, class_name):
        return WebDriverWait(parent, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, class_name)))

    def wait_until_innerhtml(self, elemId, html):
        return WebDriverWait(self.driver, 4).until(element_has_innerhtml((By.ID, elemId), html))

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


class element_has_innerhtml(object):
    def __init__(self, locator, html):
        self.locator = locator
        self.html = html

    def __call__(self, driver):
        element = driver.find_element(*self.locator)
        if self.html in element.get_attribute("innerHTML"):
            return element
        else:
            return False
