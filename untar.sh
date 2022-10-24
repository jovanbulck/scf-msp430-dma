#! /bin/bash

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 path/to/sancus.tar"
    exit
fi

echo ".. Untarring $1"
tar -zxf $1

NEMDEF_FILES=`find sancus -name \*.nemdef | grep -v Makefile | grep -v ".ifc"`
NUM_NEMDEF_FILES=`wc -w <<< $NEMDEF_FILES`
echo ".. Found $NUM_NEMDEF_FILES .nemdef binaries"

for f in $NEMDEF_FILES ; do
    echo ".. Copying $f to testcase directory"
    cp $f testcase/
done
