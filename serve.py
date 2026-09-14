#!/usr/bin/env python3
"""Serve the complete rooting assets on an explicitly selected LAN interface."""
import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
from pathlib import Path
import sys
from urllib.parse import unquote, urlsplit
from tools.offline import WEB, check_assets


def lan_address(value):
    address = ipaddress.IPv4Address(value)
    networks = ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16')
    if not any(address in ipaddress.IPv4Network(network) for network in networks):
        raise ValueError('Use this computer\'s private LAN IPv4 address, not localhost or 0.0.0.0.')
    return str(address)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB), **kwargs)

    def list_directory(self, path):
        self.send_error(403, 'Directory listing disabled')
        return None

    def send_head(self):
        if self.headers.get('Host') != self.server.expected_host:
            self.send_error(403, 'Open the printed LAN URL')
            return None
        parts = Path(unquote(urlsplit(self.path).path)).parts
        if any(part == '..' or part.startswith('.') for part in parts):
            self.send_error(403)
            return None
        candidate = WEB.joinpath(*parts[1:])
        if any(part.is_symlink() for part in [candidate, *candidate.parents] if part != WEB.parent):
            self.send_error(403)
            return None
        if not candidate.resolve().is_relative_to(WEB.resolve()):
            self.send_error(403)
            return None
        return super().send_head()

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        super().end_headers()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', required=True, help='This computer\'s LAN IPv4, e.g. 192.168.1.10')
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    try:
        host = lan_address(args.host)
        if not 1 <= args.port <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        check_assets()
        with ThreadingHTTPServer((host, args.port), Handler) as server:
            server.expected_host = host if args.port == 80 else f'{host}:{args.port}'
            print(f'Open http://{server.expected_host}/?offline on this computer.', flush=True)
            print('Keep the TV on the same LAN. Its Internet access can remain blocked. Ctrl+C stops the server.', flush=True)
            server.serve_forever()
    except KeyboardInterrupt:
        pass
    except (OSError, ValueError) as error:
        print(f'Cannot start: {error}\nPrepare first: python3 tools/prepare.py --ipk /path/to/package.ipk', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
