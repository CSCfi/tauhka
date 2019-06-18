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

import falcon
import os
from wsgiref.simple_server import make_server


class EchoRoute:
    def on_post(self, req, resp):
        if (req.content_length in (None, 0)):
            resp.body = "{}"
            return
        resp.body = req.get_param("payload", required=True)


class IndexRoute:
    def on_get(self, req, resp):
        resp.content_type = "text/html"
        resp.body = open(os.path.dirname(os.path.realpath(__file__)) + "/index.html", "r").read()


api = falcon.API()
api.add_route('/', IndexRoute())
api.add_route('/echo', EchoRoute())
api.req_options.auto_parse_form_urlencoded = True


if __name__ == '__main__':
    with make_server('', 8000, api) as httpd:
        httpd.serve_forever()