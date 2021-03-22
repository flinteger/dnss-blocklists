#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Validate source's 'additions' and 'exclusions' field are sorted.
#
import json
import sys


def usage():
    print(f"Usage: {sys.argv[0]} file...")


def main():
    if len(sys.argv) == 1:
        usage()
        sys.exit(1)

    ret = 0
    for file in sys.argv[1:]:
        if not validate(file):
            ret += 1

    sys.exit(ret)


def validate(file: str) -> bool:
    with open(file) as f:
        data = json.loads(f.read())
        for key in ['additions', 'exclusions']:
            if key in data:
                value = data[key]
                if sorted(value) != value:
                    print(f"Error: File {file} key:{key} is not sorted")
                    return False

        return True


if __name__ == '__main__':
    main()
