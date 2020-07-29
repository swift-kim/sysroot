#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status.
set -e

hash rpm2cpio 2> /dev/null || { echo "'rpm2cpio' is not installed. Aborting."; exit 1; }
hash cpio 2> /dev/null || { echo "'cpio' is not installed. Aborting."; exit 1; }

SOURCE_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

if [[ -z "$ROOTFS_DIR" ]]; then
    ROOTFS_DIR=$SOURCE_DIR/armel
    echo "ROOTFS_DIR set to $ROOTFS_DIR"
fi

if [[ -d "$ROOTFS_DIR" ]]; then
    rm -rf $ROOTFS_DIR
fi

TMP_DIR=$ROOTFS_DIR/.tmp
mkdir -p $TMP_DIR

echo ">>Start downloading files"
$SOURCE_DIR/tizen-fetch.sh $TMP_DIR
echo "<<Finished downloading files"

echo ">>Start constructing rootfs"
cd $ROOTFS_DIR
for f in $TMP_DIR/*.rpm; do
    rpm2cpio $f | cpio -idm --quiet
done
ln -s asm-arm usr/include/asm
ln -s libecore_input.so.1 usr/lib/libecore_input.so
echo "<<Finished constructing rootfs"

rm -rf $TMP_DIR
