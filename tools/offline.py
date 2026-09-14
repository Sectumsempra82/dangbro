"""Shared constants for the pinned offline bundle (Python standard library only)."""
from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / 'docs'
IPK = 'org.webosbrew.hbchannel_0.7.3_all.ipk'
SHA256 = 'd10bf3c753551d7c72fb7a92b20fcd2317e502a220ac668ba8e76f6ea78b363c'
ASSETS = ['index.html', 'dangbro.js', 'local-url.js', 'help.html', 'guided-terminal.css',
          'resources/dangbro/index.html', 'resources/root_persistence.sh', 'resources/ts.sh']
URL = 'https://github.com/webosbrew/webos-homebrew-channel/releases/download/v0.7.3/' + IPK


def verify_ipk(path):
    digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if digest != SHA256:
        raise ValueError('Homebrew package checksum mismatch: ' + digest)


def check_assets():
    for name in ASSETS + ['resources/' + IPK]:
        path = WEB / name
        if not path.is_file():
            raise ValueError('Missing offline asset: ' + name)
        if path.resolve() != path.absolute():
            raise ValueError('Offline assets must not use symlinks: ' + name)
    verify_ipk(WEB / 'resources' / IPK)
