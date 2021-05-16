#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

from typing import Set


def load_domains(file: str) -> Set:
    domains = set()

    if not os.path.exists(file):
        return domains

    with open(file) as f:
        for line in f.readlines():
            line = line.strip()
            if len(line) == 0 or line.isspace() or line.startswith("#"):
                # skip empty or comment line
                continue
            domains.add(line)
    return domains


def write_domains(domains: Set, file: str, reload: bool = True):
    if reload and os.path.exists(file):
        # reload exist file to avoid any change outside current process.
        with open(file) as f:
            for line in f.readlines():
                line = line.strip()
                domains.add(line)

    with open(file, 'w') as f:
        domains_list = list(domains)
        domains_list.sort()
        f.write('\n'.join(domains_list))
        f.write('\n')
