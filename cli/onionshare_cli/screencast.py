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
import time

from PIL import Image
import PIL


class ScreencastErrorNginx(Exception):
    """
    Nginx server failed to start
    """


class Screencast:
    def __init__(
        self,
        common,
        onion,
        mode_settings,
        local_only=False,
        background_image=None,
        disable_mic=False,
    ):
        self.common = common
        self.common.log("Screencast", "__init__")

        self.onion = onion
        self.mode_settings = mode_settings
        self.local_only = local_only
        self.background_image = background_image
        self.disable_mic = disable_mic

        self.onion_host = None

        # Prepare the data directory
        (
            self.ffmpeg_path,
            self.ffprobe_path,
            self.nginx_path,
            self.nginx_rtmp_module_path,
        ) = self.common.get_screencast_paths()
        self.data_dir = tempfile.TemporaryDirectory(dir=self.common.build_tmp_dir())
        self.webroot_dir = os.path.join(self.data_dir.name, "webroot")
        os.makedirs(self.webroot_dir, exist_ok=True)

        # Find ports for nginx services
        self.rtmp_port = self.common.get_available_port(1000, 65535)
        self.http_port = self.common.get_available_port(1000, 65535)

        # Prepare the background image
        if self.background_image:
            try:
                image = PIL.Image.open(self.background_image)
                w, h = image.size
                # Make the width and height divisible by 2
                even_w = w // 2 == w / 2
                even_h = h // 2 == h / 2
                if not even_w or not even_h:
                    self.common.log(
                        "Screencast", "__init__", "resizing background image"
                    )
                    if not even_w:
                        w += 1
                    if not even_h:
                        h += 1

                    image.resize(w, h)
                    self.background_image = os.path.join(
                        self.data_dir, "background.jpg"
                    )
                    with open(self.background_image, "w") as f:
                        image.save(f)

            except PIL.UnidentifiedImageError:
                pass

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

        # Start nginx service
        self.common.log(
            "Screencast",
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
            self.common.log("Screencast", "__init__", f"nginx pid: {self.nginx_pid}")
        else:
            self.common.log("Screencast", "__init__", f"nginx failed to run")
            raise ScreencastErrorNginx()

        # Start screencast
        self.ffmpeg_p = None
        self.stop_thread = False
        self.t = threading.Thread(target=self.start)
        self.t.start()

    def cleanup(self):
        self.common.log("Screencast", "__init__", "cleanup")
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

        self.stop_thread = True
        self.t.join()

    def start(self):
        if self.local_only:
            self.common.log(
                "Screencast", "start", "--local-only, so skip starting onion service"
            )
            self.onion_host = f"127.0.0.1:{self.http_port}"
        else:
            self.common.log("Screencast", "start", "starting onion service")
            self.onion_host = self.onion.start_onion_service(
                "screencast", self.mode_settings, self.http_port, True
            )

        # Build the ffmpeg command
        cmd = []
        if self.common.platform == "Linux":
            # Linux, microphone and background image
            # TODO: decide the command based on self.background_image and self.disable_mic
            cmd += [
                self.ffmpeg_path,
                "-loglevel",
                "error",
                "-y",
                "-loop",
                "1",
                "-f",
                "image2",
                "-i",
                self.background_image,
                "-f",
                "pulse",
                "-i",
                "default",
                "-codec:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-preset",
                "veryfast",
                "-b:v",
                "1200k",
                "-r",
                "30.0",
                "-g",
                "60.0",
                "-codec:a",
                "aac",
                "-b:a",
                "128k",
                "-ar",
                "44100",
                "-maxrate",
                "1200k",
                "-bufsize",
                "128k",
                "-shortest",
                "-strict",
                "experimental",
                "-f",
                "flv",
                f"rtmp://127.0.0.1:{self.rtmp_port}/live/stream",
            ]

        self.common.log("Screencast", "start", " ".join(cmd))
        self.ffmpeg_p = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        while True:
            time.sleep(0.1)
            if self.stop_thread:
                self.ffmpeg_p.kill()
                break
