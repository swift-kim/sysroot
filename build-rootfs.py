#!/usr/bin/env python3
import argparse
import os
import re
import shutil
import subprocess
import urllib.request

basePackages = [
    'gcc',
    'glibc',
    'glibc-devel',
    'libgcc',
    'libstdc++',
    'libstdc++-devel',
    'linux-glibc-devel',
    'zlib-devel',
]
unifiedPackages = [
    'capi-base-common-devel',
    'capi-base-utils',
    'capi-base-utils-devel',
    'coregl',
    'coregl-devel',
    'ecore-core',
    'ecore-core-devel',
    'ecore-imf',
    'ecore-imf-devel',
    'ecore-imf-evas-devel',
    'ecore-input',
    'ecore-wl2',
    'ecore-wl2-devel',
    'efl-devel',
    'eina-devel',
    'emile-devel',
    'eo-devel',
    'evas',
    'evas-devel',
    'freetype2-devel',
    'jsoncpp',
    'jsoncpp-devel',
    'libdlog',
    'libdlog-devel',
    'libpng-devel',
    'libtbm-devel',
    'libtdm-client',
    'libtdm-client-devel',
    'libtdm-devel',
    'libwayland-client',
    'libxkbcommon-devel',
    'wayland-devel',
]

# Execute only if run as a script.
if __name__ != "__main__":
    exit(1)

if not shutil.which('rpm2cpio'):
    print('rpm2cpio is not installed. To install:\n'
          '  sudo apt install rpm2cpio')
    exit(1)
if not shutil.which('cpio'):
    print('cpio is not installed. To install:\n'
          '  sudo apt install cpio')
    exit(1)

# Parse arguments.
parser = argparse.ArgumentParser(
    description='Tizen rootfs generator (for Flutter)')
parser.add_argument(
    '-a', '--arch', type=str, choices=['arm', 'arm64', 'x86'],
    help='target architecture (defaults to "arm")',
    default='arm')
parser.add_argument(
    '-o', '--output', metavar='PATH', type=str,
    help='path to the output directory (defaults to arch)')
parser.add_argument(
    '-c', '--clean', action='store_true',
    help='clean the output directory and exit')
parser.add_argument(
    '-b', '--base-repo', metavar='URL', type=str,
    help='url to the base packages repository',
    default='http://download.tizen.org/snapshots/tizen/5.5-base/latest/repos/standard/packages')
parser.add_argument(
    '-u', '--unified-repo', metavar='URL', type=str,
    help='url to the unified packages repository',
    default='http://download.tizen.org/snapshots/tizen/5.5-unified/latest/repos/standard/packages')
args = parser.parse_args()

if not args.output:
    args.output = args.arch

if args.clean:
    shutil.rmtree(args.output)
    exit(0)

downloadPath = os.path.join(args.output, '.rpms')
os.makedirs(downloadPath, exist_ok=True)
existingRpms = [f for f in os.listdir(downloadPath) if f.endswith('.rpm')]

if args.arch == 'arm':
    archName = 'armv7l'
elif args.arch == 'arm64':
    archName = 'aarch64'
elif args.arch == 'x86':
    archName = 'i686'
else:
    print(f'Undefined arch: {args.arch}')
    exit(1)

# Retrieve html documents.
documents = {}
for url in [f'{args.base_repo}/{archName}',
            f'{args.base_repo}/noarch',
            f'{args.unified_repo}/{archName}',
            f'{args.unified_repo}/noarch']:
    request = urllib.request.Request(url)
    with urllib.request.urlopen(request) as response:
        documents[url] = response.read().decode('utf-8')

# Download packages.
for package in basePackages + unifiedPackages:
    pattern = f'{re.escape(package)}-\\d+\\.[\\d_\\.]+-[\\d\\.]+\\..+\\.rpm'

    if any([re.match(pattern, f) for f in existingRpms]):
        print(f'Already downloaded {package}')
        continue

    for parent, doc in documents.items():
        match = re.findall(f'<a href=".+">({pattern})</a>', doc)
        if len(match) > 0:
            url = f'{parent}/{match[0]}'
            break

    if len(match) == 0:
        print(f'Could not find a package {package}')
    else:
        print(f'Downloading {url}...')
        urllib.request.urlretrieve(url, f'{downloadPath}/{match[0]}')

# Extract files.
for rpm in [f for f in os.listdir(downloadPath) if f.endswith('.rpm')]:
    abspath = f'{os.path.abspath(downloadPath)}/{rpm}'
    command = f'cd {args.output} && rpm2cpio {abspath} | cpio -idum --quiet'
    subprocess.run(command, shell=True, check=True)

# Create symbolic links. Any errors are ignored.
subprocess.run(f'ln -s asm-arm {args.output}/usr/include/asm', shell=True)
subprocess.run(f'ln -s libecore_input.so.1 {args.output}/usr/lib/libecore_input.so',
               shell=True)

print('Complete')
