#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Generate `README.md` from template.
#

import json
import datetime

from jinja2 import Template


def main():
    with open('README.md.jinja') as f:
        blocklists = get_blocklists()
        last_updated_at=datetime.datetime.now().isoformat("T", "seconds")
        template = Template(f.read())
        print(template.render(blocklists=blocklists,
                              last_updated_at=last_updated_at))


def get_blocklists():
    blocklists = [
        {
            "name": "malicious",
            "source_file": "sources/malicious.json"
        },
        {
            "name": "ad",
            "source_file": "sources/ad.json"
        },
        {
            "name": "gambling",
            "source_file": "sources/gambling.json"
        },
        {
            "name": "piracy",
            "source_file": "sources/piracy.json"
        },
        {
            "name": "dating",
            "source_file": "sources/dating.json"
        },
        {
            "name": "porn",
            "source_file": "sources/porn.json"
        },
        {
            "name": "social_networks",
            "source_file": "sources/social_networks.json"
        }
    ]

    return list(map(fill_filter_detail, blocklists))


def fill_filter_detail(filter):
    source_file = filter["source_file"]
    filter["formats"] = [{
        "name": "hosts",
        "ext": ".hosts"
    }, {
        "name": "domains",
        "ext": ".domains.txt"
    }]
    base_url = "https://raw.githubusercontent.com/flinteger/dnss-blocklists/release/blocklists/"
    with open(source_file) as f:
        data = json.loads(f.read())
        name = data["name"]
        filter["description"] = data["description"]
        domains = f"blocklists/{name}.domains.txt"
        with open(domains) as o:
            filter["count"] = len(o.readlines())
            filter["url"] = base_url + name

    return filter


if __name__ == '__main__':
    main()
