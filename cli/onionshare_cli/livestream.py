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

import os
import tempfile
import subprocess
import time
import threading

import pylivestream.api as pls


class LivestreamErrorNginx(Exception):
    """
    Nginx server failed to start
    """


class Livestream:
    def __init__(self, common, onion, mode_settings, local_only=False):
        self.common = common
        self.common.log("Livestream", "__init__")

        self.onion = onion
        self.mode_settings = mode_settings
        self.local_only = local_only

        self.onion_host = None

        # Prepare the data
        (
            self.ffmpeg_path,
            self.ffprobe_path,
            self.nginx_path,
            self.nginx_rtmp_module_path,
        ) = self.common.get_livestream_paths()
        self.data_dir = tempfile.TemporaryDirectory(dir=self.common.build_tmp_dir())
        self.webroot_dir = os.path.join(self.data_dir.name, "webroot")
        os.makedirs(self.webroot_dir, exist_ok=True)
        self.rtmp_port = self.common.get_available_port(1000, 65535)
        self.http_port = self.common.get_available_port(1000, 65535)

        # Write nginx conf
        with open(self.common.get_resource_path("nginx.conf_template")) as f:
            nginx_conf_template = f.read()

        nginx_conf_template = (
            nginx_conf_template.replace("{{data_dir}}", self.data_dir.name)
            .replace("{{webroot_dir}}", self.webroot_dir)
            .replace("{{nginx_rtmp_module_path}}", self.nginx_rtmp_module_path)
            .replace("{{rtmp_port}}", str(self.rtmp_port))
            .replace("{{http_port}}", str(self.http_port))
        )

        self.nginx_conf_path = os.path.join(self.data_dir.name, "nginx.conf")
        with open(self.nginx_conf_path, "w") as f:
            f.write(nginx_conf_template)

        # Write pylivestream config
        with open(self.common.get_resource_path("pylivestream.ini_template")) as f:
            pylivestream_ini_template = f.read()

        pylivestream_ini_template = (
            pylivestream_ini_template.replace("{{ffmpeg_path}}", self.ffmpeg_path)
            .replace("{{ffprobe_path}}", self.ffprobe_path)
            .replace("{{rtmp_port}}", str(self.rtmp_port))
        )

        self.pylivestream_ini_path = os.path.join(
            self.data_dir.name, "pylivestream.init"
        )
        with open(self.pylivestream_ini_path, "w") as f:
            f.write(pylivestream_ini_template)

        # Start nginx service
        self.common.log(
            "Livestream",
            "__init__",
            f"starting nginx, config path={self.nginx_conf_path}",
        )
        subprocess.run(
            [
                self.nginx_path,
                "-c",
                self.nginx_conf_path,
                "-g",
                f"error_log {self.data_dir.name}/error.log;",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        time.sleep(0.2)

        self.nginx_pid_path = os.path.join(self.data_dir.name, "nginx.pid")
        if os.path.exists(self.nginx_pid_path):
            with open(self.nginx_pid_path) as f:
                self.nginx_pid = int(f.read())
            self.common.log("Livestream", "__init__", f"nginx pid: {self.nginx_pid}")
        else:
            self.common.log("Livestream", "__init__", f"nginx failed to run")
            raise LivestreamErrorNginx()

        # Start livestream

        self.t = threading.Thread(target=self.start)
        self.t.start()

    def cleanup(self):
        self.common.log("Livestream", "__init__", "cleanup")
        subprocess.run(
            [
                self.nginx_path,
                "-c",
                self.nginx_conf_path,
                "-s",
                "stop",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # TODO: cleanly kill the thread
        # https://www.geeksforgeeks.org/python-different-ways-to-kill-a-thread/

    def start(self):
        if self.local_only:
            self.common.log(
                "Livestream", "start", "--local-only, so skip starting onion service"
            )
            self.onion_host = f"127.0.0.1:{self.http_port}"
        else:
            self.common.log("Livestream", "start", "starting onion service")
            self.onion_host = self.onion.start_onion_service(
                "livestream", self.mode_settings, self.http_port, True
            )

        self.common.log("Livestream", "start", "running pylivestream")
        self.common.log("Livestream", "start")
        self.stream = pls.stream_microphone(
            self.pylivestream_ini_path,
            ["localhost"],
            still_image="/home/user/Pictures/wallpaper/wp3026212-stellaris-wallpapers.png",
            assume_yes=True,
        )
