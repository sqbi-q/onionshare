# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014-2021 Micah Lee, et al. <micah@micahflee.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import http.client as httplib
import urllib.parse as urlparse

from flask import request, render_template, make_response, Response
from werkzeug.datastructures import Headers


class LivestreamModeWeb:
    """
    All of the web logic for livestream mode
    """

    def __init__(self, common, web):
        self.common = common
        self.common.log("LivestreamModeWeb", "__init__")

        self.web = web

        # Port of nginx's http service to proxy to
        self.http_port = None

        self.cur_history_id = 0
        self.supports_file_requests = False

        self.define_routes()

    def define_routes(self):
        """
        The web app routes for livestream
        """

        @self.web.app.route("/", methods=["GET"], provide_automatic_options=False)
        def index():
            self.web.add_request(self.web.REQUEST_LOAD, request.path)
            r = make_response(
                render_template(
                    "livestream.html",
                    static_url_path=self.web.static_url_path,
                    title=self.web.settings.get("general", "title"),
                )
            )
            return self.web.add_security_headers(r)

        @self.web.app.route(
            "/live/<filename>", methods=["GET"], provide_automatic_options=False
        )
        def stream(filename):
            # Proxy a GET request to nginx
            conn = httplib.HTTPConnection("127.0.0.1", self.http_port)
            conn.request("GET", f"/hls/{filename}")
            r = conn.getresponse()
            contents = r.read()

            response_headers = Headers()
            for key, value in r.getheaders():
                response_headers.add(key, value)

            flask_response = Response(
                response=contents, status=r.status, headers=response_headers
            )
            return flask_response
