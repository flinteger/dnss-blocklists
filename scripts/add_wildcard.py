#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Add wildcard to additions hosts to match all the subdomains.
#
# Example: ./scripts/add_wildcard.py sources/service.*.json
#

import json
import logging
import sys


def usage():
    print(f"Usage: {sys.argv[0]} file ...")


class SourceFile:
    def __init__(self, filename: str):
        super().__init__()
        self.filename = filename

    def process(self):
        logging.info(f"Processing file {self.filename}")

        additions = []
        with open(self.filename) as f:
            data = json.load(f)
            self.list_name = data["name"]
            additions = data['additions'] if 'additions' in data else []

        # Add additions first
        if additions:
            new_additions = set()
            for host in additions:
                if not host.startswith('*.'):
                    logging.debug(f"Process host: {host}")
                    new_additions.add('*.' + host)
                else:
                    new_additions.add(host)
            new_additions = list(new_additions) # convert set to array
            new_additions.sort()
            data['additions'] = new_additions

            self.write_file(data)

    def write_file(self, data: object):
        # json.dump(data, )
        with open(self.filename, 'w') as f:
            json.dump(data, f, indent=2)

def main():
    datefmt = "%Y-%m-%dT%H:%M:%S%Z"
    format = "%(asctime)s %(thread)d %(levelname)s %(message)s"
    logging.basicConfig(
        # filename='dns-filters.log',
        level=logging.INFO,
        datefmt=datefmt,
        format=format)

    if len(sys.argv) == 1:
        usage()
        sys.exit(1)

    for filename in sys.argv[1:]:
        SourceFile(filename).process()


if __name__ == '__main__':
    main()
