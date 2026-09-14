#!/usr/bin/env python3
"""Prepare on a connected computer, or import an already downloaded package."""
import argparse
import os
from pathlib import Path
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from offline import ROOT, WEB, IPK, URL, ASSETS, verify_ipk, check_assets


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ipk', type=Path, help='Import this file without any network request')
    parser.add_argument('--bundle', action='store_true', help='Also build dist/dangbro-offline.zip')
    args = parser.parse_args()
    destination = WEB / 'resources' / IPK
    with tempfile.TemporaryDirectory() as directory:
        package = Path(directory) / IPK
        if args.ipk:
            shutil.copyfile(args.ipk, package)
        else:
            print('Downloading the pinned Homebrew release on this computer only...')
            with urllib.request.urlopen(URL, timeout=60) as response, package.open('wb') as output:
                shutil.copyfileobj(response, output)
        verify_ipk(package)
        temporary = destination.with_suffix('.tmp')
        shutil.copyfile(package, temporary)
        os.replace(temporary, destination)
    check_assets()
    print('Offline assets ready. The server never downloads missing files.')
    if args.bundle:
        output = ROOT / 'dist' / 'dangbro-offline.zip'
        output.parent.mkdir(exist_ok=True)
        # Explicit allowlist prevents accidental inclusion of keys, recordings, or backups.
        files = [ROOT / name for name in ['README.md', 'OFFLINE.md', 'serve.py']]
        files += [WEB / name for name in ASSETS] + [WEB / 'resources' / IPK]
        files += [ROOT / 'tools' / name for name in ['offline.py', 'prepare.py']]
        for path in files:
            if not path.is_file() or path.resolve() != path.absolute():
                raise ValueError('Missing or symlinked bundle file: ' + str(path))
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(files):
                archive.write(path, 'dangbro-offline/' + path.relative_to(ROOT).as_posix())
        print(output)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError) as error:
        sys.exit('Preparation failed: ' + str(error))
