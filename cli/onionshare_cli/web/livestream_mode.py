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

from flask import request, render_template, make_response, jsonify, session


class LivestreamModeWeb:
    """
    All of the web logic for livestream mode
    """

    def __init__(self, common, web):
        self.common = common
        self.common.log("LivestreamModeWeb", "__init__")

        self.web = web

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
