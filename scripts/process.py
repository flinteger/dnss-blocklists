#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import concurrent.futures
import json
import logging
import os
import random
import re
import shutil
import sys
import threading
import urllib.request
from typing import List
from urllib.parse import urlparse
from zipfile import ZIP_DEFLATED, ZipFile

import dns.message
import dns.query
import dns.rcode
import util

MAX_WORKERS = 100
DNS_TIMEOUT = 5  # in seconds
DNS_SERVERS = [   # Use multiple DNS servers to avoid rate limit
    # Cloudflare
    '1.1.1.1',
    '1.0.0.1',

    # Google
    '8.8.8.8',
    '8.8.4.4',

    # Quad9
    '9.9.9.9',
    '149.112.112.112',

    # OpenDNS
    # '208.67.222.222',
    # '208.67.220.220',

    # Control D
    # '76.76.2.0',
    # '76.76.10.0'
]


def usage():
    print(f"Usage: {sys.argv[0]} file ...")
    print(f"Example: {sys.argv[0]} sources/ad.json")


class SourceFile:

    OUTPUT_DIR = 'blocklists'

    def __init__(self, filename: str):
        super().__init__()
        self.cache_counter = 0
        self.filename = filename
        self.all_domains = set()
        self.hosts = set()
        self.nxdomains = util.load_domains('./cache/nxdomains')
        self.okdomains = util.load_domains('./cache/okdomains')
        self.tbddomains = util.load_domains('./cache/tbddomains')
        self.list_name = ""
        self.lock = threading.Lock()

    def process(self):
        logging.info(f"Processing file {self.filename}")
        sources = []
        exclusions = []
        additions = []
        with open(self.filename) as f:
            data = json.load(f)
            self.list_name = data["name"]
            sources = data['sources'] if 'sources' in data else []
            exclusions = data["exclusions"] if 'exclusions' in data else []
            additions = data['additions'] if 'additions' in data else []

        logging.info(f"{self.list_name} Begin to process")

        # Add additions first
        if additions:
            for host in additions:
                logging.debug(f"Add additions: {host}")
                self.hosts.add(host)

        for s in sources:
            url = s["url"]
            format = s["format"]
            filename = os.path.join("cache", url.replace("/", "_").replace(":", ""))

            try:
                self.download(url, filename)
            except Exception as e:
                logging.error(f"{self.list_name} Download {url} failed: {e}")
                continue

            if format == "hosts":
                self.process_hosts(filename, exclusions)
            elif format == "domains":
                self.process_domains(filename, exclusions)
            elif format == "abp":
                self.process_abp(filename, exclusions)
            elif format == "urls":
                self.process_urls(filename, exclusions)
            else:
                logging.error(f"{self.list_name} Unknown format: {format}: {url}")

        # self._cleanup_hosts()
        self._concurrent_cleanup_hosts()

        self.write_list()

        util.write_domains(self.nxdomains, './cache/nxdomains')
        util.write_domains(self.okdomains, './cache/okdomains')
        util.write_domains(self.tbddomains, './cache/tbddomains')
        util.write_domains(self.all_domains, './cache/alldomains')

    def write_list(self):
        # with open(f"{SourceFile.OUTPUT_DIR}/{self.list_name}.json", 'w') as f:
        #     hosts_list = list(self.hosts)
        #     hosts_list.sort()
        #     f.write(json.dumps(hosts_list, sort_keys=True, indent=2))

        domains_txt = f"{SourceFile.OUTPUT_DIR}/{self.list_name}.domains.txt"
        with open(domains_txt, 'w') as f:
            hosts_list = list(self.hosts)
            hosts_list.sort()
            f.write('\n'.join(hosts_list))

        # compress .domains.txt
        if os.path.exists(domains_txt):
            out_zip = f"{domains_txt}.zip"
            with ZipFile(out_zip, "w", ZIP_DEFLATED) as zip:
                zip.write(domains_txt, f"{self.list_name}.domains.txt")

        with open(f"{SourceFile.OUTPUT_DIR}/{self.list_name}.hosts", 'w') as f:
            hosts_list = list(self.hosts)
            hosts_list.sort()

            ipv4_list = map(lambda x: "0.0.0.0 " + x, hosts_list)
            f.write('\n'.join(ipv4_list))

            f.write('\n')

            ipv6_list = map(lambda x: ":: " + x, hosts_list)
            f.write('\n'.join(ipv6_list))

    def download(self, url: str, filename: str) -> None:
        logging.info(f"{self.list_name} Downloading {url} to {filename}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:80.0) Gecko/20100101 Firefox/80.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;*/*'
        }

        req = urllib.request.Request(url, None, headers)

        with urllib.request.urlopen(req) as input_stream, open(filename, "wb") as output_stream:
            shutil.copyfileobj(input_stream, output_stream)

    def process_hosts(self, filename: str, exclusions: List[str]):
        with open(filename) as f:
            count = 0
            for line in f.readlines():
                line = line.strip()
                if len(line) == 0 or line.isspace() or line.startswith("#"):
                    # skip empty or comment line
                    continue

                # logging.debug(f"{self.list_name} Processing line: {line}")

                try:
                    [_, host] = line.split(" ", 1)
                    host = host.strip()
                    if self.process_host(host, exclusions):
                        count += 1
                except ValueError:
                    logging.error(f"{self.list_name} Failed to parse line: {line}")
            logging.info(f"{self.list_name} Processed {filename}. hosts: {count}")

    def process_domains(self, filename: str, exclusions: List[str]):
        with open(filename) as f:
            count = 0
            for line in f.readlines():
                line = line.strip()
                if len(line) == 0 or line.isspace() or line.startswith("#"):
                    # skip empty or comment line
                    continue

                # logging.debug(f"{self.list_name} Processing line: {line}")

                if self.process_host(line, exclusions):
                    count += 1

            logging.info(f"{self.list_name} Processed {filename}. hosts: {count}")

    def process_urls(self, filename: str, exclusions: List[str]):
        with open(filename) as f:
            count = 0
            for line in f.readlines():
                line = line.strip()
                if len(line) == 0 or line.isspace() or line.startswith("#"):
                    # skip empty or comment line
                    continue

                # logging.debug(f"{self.list_name} Processing line: {line}")
                url = urlparse(line)
                netloc = url.netloc     # may include port, e.g. example.com:8080
                if not netloc:
                    continue

                host = netloc.split(':')[0]
                if self.process_host(host, exclusions):
                    count += 1

            logging.info(f"{self.list_name} Processed {filename}. hosts: {count}")

    def process_abp(self, filename: str, exclusions: List[str]):
        """
        Process ad block plus file format.

        Adblock Plus filters explained: https://adblockplus.org/filter-cheatsheet
        """
        with open(filename) as f:
            count = 0
            for line in f.readlines():
                line = line.strip(' \r\n\t^')
                if len(line) == 0 or line.isspace() or line.startswith("#") or line.startswith("!"):
                    # skip empty or comment line
                    continue
                # sample line:
                #   ||xkjxgt.com^
                #   @@||launches.appsflyer.com^|

                # logging.debug(f"{self.list_name} Processing line: {line}")

                if line.startswith('@@'):
                    # exception rule, ignore
                    continue

                domain = line.split('|')[-1]

                if self.process_host(domain, exclusions):
                    count += 1

            logging.info(f"{self.list_name} Processed {filename}. hosts: {count}")

    def process_host(self, host: str, exclusions: List[str]) -> bool:
        host = host.lower()
        if not HostUtil.is_valid_domain(host):
            logging.error(f"{self.list_name} Ignore invalid domain: {host}")
            return False

        self.all_domains.add(host)

        for exclusion in exclusions:
            # print(f"Checking {exclusion}")
            if exclusion.find('*.') == 0:
                # a wildcard host, e.g. *.example.com
                if host == exclusion[2:]:
                    # e.g. compare host == example.com
                    logging.info(f"{self.list_name} Host {host} is in wildcard exclusions {exclusion}, ignore")
                    return False

                # e.g. re.search("[.]example.com", host)
                if re.search('[.]' + exclusion[2:] + '$', host):
                    logging.info(f"{self.list_name} Host {host} is in wildcard exclusions {exclusion}, ignore")
                    return False
            else:
                if host == exclusion:
                    logging.info(f"{self.list_name} Host {host} is in exclusions, ignore")
                    return False

        self.hosts.add(host)
        return True

    def _cleanup_hosts(self):
        clean_hosts = set()
        total = len(self.hosts)
        i = 0
        alive = 0

        logging.debug(f"{self.list_name} cleanup hosts: len(hosts)={total}")

        for host in self.hosts:
            i += 1
            if i % 500 == 0:
                logging.info(f"{self.list_name} Cleaned {i}/{total} alive: {alive}")

            if self._is_alive_host(host):
                alive += 1
                logging.debug(f"{self.list_name} host is alive: {host}")
                clean_hosts.add(host)
        self.hosts = clean_hosts

    def _concurrent_cleanup_hosts(self):

        clean_hosts = set()
        clean_hosts_lock = threading.Lock()

        total = len(self.hosts)
        i = 0
        alive_counter = 0

        logging.debug(f"{self.list_name} begin cleanup hosts. hosts: {total}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            for host, alive in zip(self.hosts, executor.map(self._is_alive_host, self.hosts)):
                with clean_hosts_lock:
                    i += 1
                    if alive:
                        alive_counter += 1
                        clean_hosts.add(host)

                    if i % 500 == 0:
                        logging.info(f"{self.list_name} Cleaned {i}/{total} alive: {alive_counter}")

        logging.info(f"{self.list_name} finished cleanup hosts: {len(clean_hosts)}/{total}")

        self.hosts = clean_hosts

    def _is_alive_host(self, host) -> bool:
        if HostUtil.is_IPv4(host):
            logging.info(f"{self.list_name} Host {host} is IPv4 address, ignore")
            return False

        if host.startswith('*.'):
            logging.debug(f"{self.list_name} Host {host} is a wildcard, always alive")
            return True

        # check cached NXDOMAIN first to save DNS query time
        if host in self.nxdomains:
            logging.debug(f"{self.list_name} Host {host} in nxdomains, ignore")
            return False

        if host in self.okdomains:
            logging.debug(f"{self.list_name} Host {host} in okdomains, alive")
            return True

        # if host in self.tbddomains:
        #     logging.debug(f"{self.list_name} Host {host} in tbddomains, alive")
        #     return True

        not_sure = False
        exist = False
        try:
            q = dns.message.make_query(host, 'A')
            dns_server = random.choice(DNS_SERVERS)
            response = dns.query.udp(q, dns_server, timeout=DNS_TIMEOUT)   # timeout in seconds
            rcode = response.rcode()
            logging.debug(f"{self.list_name} DNS query response code: {rcode}. host={host} dns_server={dns_server}")
            if rcode == dns.rcode.NXDOMAIN:
                logging.info(f"{self.list_name} Host is not exist anymore, ignore. host={host} dns_server={dns_server}")
                with self.lock:
                    self.nxdomains.add(host)
                    self._increase_cache_counter()
                return False
            if rcode == dns.rcode.NOERROR:
                logging.debug(f"{self.list_name} Host have valid DNS A record. host={host} dns_server={dns_server}")
                exist = True
            else:
                logging.info(f"{self.list_name} DNS query return un-handled rcode: {rcode}. host={host} dns_server={dns_server}")
        except dns.exception.Timeout:
            # timeout probably due to DNS server is not set up correct for that domain.
            logging.error(f"{self.list_name} DNS query failed: timeout host={host} dns_server={dns_server}")
        except Exception as e:
            logging.error(f"{self.list_name} DNS query failed: {e} host={host} dns_server={dns_server}")
            not_sure = True    # set to true to avoid missing a host

        with self.lock:
            if exist:
                self.okdomains.add(host)
                self._increase_cache_counter()
            else:
                self.tbddomains.add(host)
                self._increase_cache_counter()

        return exist or not_sure


    def _increase_cache_counter(self):
        self.cache_counter += 1
        if self.cache_counter % 500 == 0:
            logging.info(f"{self.list_name} Writing to cache: cache_counter={self.cache_counter} nxdomains={len(self.nxdomains)} okdomains={len(self.okdomains)}")
            util.write_domains(self.nxdomains, './cache/nxdomains')
            util.write_domains(self.okdomains, './cache/okdomains')
            util.write_domains(self.tbddomains, './cache/tbddomains')


class HostUtil:
    # abc-.example.com is valid domain
    LABEL_RE = re.compile('^[a-z0-9_]([a-z0-9-_]{0,250})?$', re.IGNORECASE)

    @staticmethod
    def is_IPv4(host: str) -> bool:
        return re.search('^([0-9]{1,3}[.]){3}[0-9]{1,3}$', host) is not None

    @staticmethod
    def is_valid_domain(host: str) -> bool:
        if host.find(".") == -1:
            # no dot in domain name
            return False

        if len(host) > 255:
            return False

        return all(HostUtil.LABEL_RE.match(x) for x in host.split('.'))


def main():
    datefmt = "%Y-%m-%dT%H:%M:%S%Z"
    # format = "%(asctime)s pid=%(process)d tid=%(thread)d logger=%(name)s level=%(levelname)s %(message)s"
    format = "%(asctime)s %(thread)d %(levelname)s %(message)s"
    levelName = os.environ.get("LOG_LEVEL", "INFO")
    level = logging.getLevelName(levelName)
    logging.basicConfig(
        # filename='dns-filters.log',
        level=level,  # logging.DEBUG,
        datefmt=datefmt,
        format=format)

    if len(sys.argv) == 1:
        usage()
        sys.exit(1)

    for filename in sys.argv[1:]:
        SourceFile(filename).process()


if __name__ == '__main__':
    main()
