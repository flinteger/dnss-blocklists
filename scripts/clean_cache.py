#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# clean cache if greater than 95MB
#

import glob
import os


def main():
    cache_files = glob.glob("cache/*domains")
    for file in cache_files:

        size = os.path.getsize(file)  # in bytes
        print(f"Check file {file}, size: {size} bytes")
        if size > 90 * 1024 * 1024:
            print(f"Truncate file {file} from {size/1024/1024}MB to 0")
            with open(file, "w") as f:
                # open with write only mode to truncate to empty file.
                f.close()

if __name__ == '__main__':
    main()
