#!/bin/bash


if [ $# -eq 1 ]
then
    if test -f "$1"; then
        echo "$1 exists."
        cat <$1  > /dev/xdevcfg
    fi
else
    echo "No arguments supplied"
fi
