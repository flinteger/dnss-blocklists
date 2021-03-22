#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Query a list of domains in blocklists
#
import sys

from typing import List

import util


def main(domains: List[str]):
    blocklists = [
        'blocklists/ad.domains.txt',
        'blocklists/malicious.domains.txt',
        'blocklists/piracy.domains.txt',
        'blocklists/social_networks.domains.txt',
        'blocklists/dating.domains.txt',
        'blocklists/gambling.domains.txt',
        'blocklists/porn.domains.txt'
    ]

    for blocklist in blocklists:
        blocklist_domains = util.load_domains(blocklist)
        for (rank, domain) in domains:
            if domain in blocklist_domains:
                print(f"{rank}: {domain} in {blocklist}")


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} domain-file")
        sys.exit(1)

    rank = 0
    domains = list()

    # load top-N rank domains, the file content is ordered by rank.
    with open(sys.argv[1]) as f:
        for line in f.readlines():
            domain = line.strip()
            if len(domain) == 0 or domain.isspace() or domain.startswith("#"):
                # skip empty or comment line
                continue
            rank += 1
            domains.append((rank, domain))

    main(domains)
