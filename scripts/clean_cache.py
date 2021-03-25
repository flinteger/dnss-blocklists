#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# clean cache if greater than 95MB
#

import util

#
# >>> s1 = set([1, 2, 3, 5])
# >>> s2 = set([2, 5, 8])
# >>> s1.intersection_update(s2)
# >>> s1
# {2, 5}
#
def main():
    cache_files = ["cache/nxdomains", "cache/okdomains", "cache/tbddomains"]
    all_domains = util.load_domains("cache/alldomains")
    print(f"Total domains: {len(all_domains)}")
    for file in cache_files:
        cache_domains = util.load_domains(file)
        old_count = len(cache_domains)
        cache_domains.intersection_update(all_domains)
        new_count = len(cache_domains)
        util.write_domains(cache_domains, file, False)
        print(f"Cleaned {file}: {old_count} -> {new_count}")

if __name__ == '__main__':
    main()
