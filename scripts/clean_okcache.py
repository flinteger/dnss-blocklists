#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Validate source's 'additions' and 'exclusions' field are sorted.
#

import glob

import util


def main():
    blocked_domains = set()
    domain_files = glob.glob("blocklists/*.domains.txt")
    for file in domain_files:
        blocked_domains.update(util.load_domains(file))

    okdomains = util.load_domains("cache/okdomains")
    okdomains.intersection_update(blocked_domains)
    util.write_domains(okdomains, "cache/okdomains", False)


if __name__ == '__main__':
    main()
