#!/bin/bash

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 path/to/sancus.tar"
    exit
fi

echo ".. Unzipping $1"
unzip $1

NEMDEF_FILES=`ls *.nemdef`
NUM_NEMDEF_FILES=`wc -w <<< $NEMDEF_FILES`
echo ".. Found $NUM_NEMDEF_FILES .nemdef binaries"

for f in $NEMDEF_FILES ; do
    echo ".. Copying $f to testcase directory"
    mv $f testcase/
done
