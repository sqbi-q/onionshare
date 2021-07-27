```
╭───────────────────────────────────────────╮
│    *            ▄▄█████▄▄            *    │
│               ▄████▀▀▀████▄     *         │
│              ▀▀█▀       ▀██▄              │
│      *      ▄█▄          ▀██▄             │
│           ▄█████▄         ███        -+-  │
│             ███         ▀█████▀           │
│             ▀██▄          ▀█▀             │
│         *    ▀██▄       ▄█▄▄     *        │
│ *             ▀████▄▄▄████▀               │
│                 ▀▀█████▀▀                 │
│             -+-                     *     │
│   ▄▀▄               ▄▀▀ █                 │
│   █ █     ▀         ▀▄  █                 │
│   █ █ █▀▄ █ ▄▀▄ █▀▄  ▀▄ █▀▄ ▄▀▄ █▄▀ ▄█▄   │
│   ▀▄▀ █ █ █ ▀▄▀ █ █ ▄▄▀ █ █ ▀▄█ █   ▀▄▄   │
│                                           │
│          https://onionshare.org/          │
╰───────────────────────────────────────────╯
```

## Installing OnionShare CLI

Install dependencies.

In Linux, install these from your package manager: `sudo apt install tor ffmpeg nginx libnginx-mod-rtmp`

In macOS, install it with [Homebrew](https://brew.sh): `brew install tor`

TODO: Figure out how to install the other macOS dependencies

Then install OnionShare CLI:

```sh
pip install onionshare-cli
```

Then run it with:

```sh
onionshare-cli --help
```

## Developing OnionShare CLI

You must have python3 and [poetry](https://python-poetry.org/) installed.

Install dependencies with poetry:

```sh
poetry install
```

To run from the source tree:

```sh
poetry run onionshare-cli
```

To run tests:

```sh
poetry run pytest -v ./tests
```

## Build a wheel package

```sh
poetry build
```

This will create `dist/onionshare_cli-$VERSION-py3-none-any.whl`.
