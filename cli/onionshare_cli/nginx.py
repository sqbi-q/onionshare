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
import subprocess
import os
from jinja2 import Template


class Nginx:
    def __init__(self, common):
        self.common = common

        self.pid_filename = os.path.join(common.build_data_dir(), "nginx.pid")
        self.error_log_filename = os.path.join(
            common.build_data_dir(), "nginx-error.log"
        )
        self.conf_filename = os.path.join(common.build_data_dir(), "nginx.conf")

        self.sites = []

        self.common.log("Nginx", "__init__", f"{self.conf_filename}")

        # Build the conf file
        with open(self.common.get_resource_path("nginx_conf_template"), "r") as f:
            self.template = Template(f.read())
        self.write_nginx_conf()

        # Start the server
        # TODO: make nginx_path work for all platforms
        self.nginx_path = "/usr/sbin/nginx"
        self.start()

    def add_site(self, name, nginx_port, flask_port):
        self.sites.append({name: name, nginx_port: nginx_port, flask_port: flask_port})
        self.write_nginx_conf()
        self.reload()

    def delete_site(self, name):
        new_sites = []
        for site in self.sites:
            if site["name"] != name:
                new_sites.append(site)

        self.sites = new_sites
        self.write_nginx_conf()
        self.reload()

    def write_nginx_conf(self):
        config = self.template.render(
            pid_filename=self.pid_filename,
            error_log_filename=self.error_log_filename,
            sites=self.sites,
        )
        with open(self.conf_filename, "w") as f:
            f.write(config)

    def start(self):
        self.common.log("Nginx", "start")
        self.p = subprocess.Popen(
            [
                self.nginx_path,
                "-c",
                self.conf_filename,
                "-g",
                f"error_log {self.error_log_filename};",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def stop(self):
        self.common.log("Nginx", "stop")
        self.p = subprocess.Popen(
            [self.nginx_path, "-c", self.conf_filename, "-s", "stop"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def reload(self):
        self.common.log("Nginx", "reload")
        self.p = subprocess.Popen(
            [self.nginx_path, "-c", self.conf_filename, "-s", "reload"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
