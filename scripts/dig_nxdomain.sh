#!/bin/sh
#
# Examples:
#   $0 < domainfile > okdomains.txt 2>nxdomains.txt
#   $0 < domainfile > /dev/null   # only print NXDOMAIN
#   $0 < domainfile 2> /dev/null  # only print non-NXDOMAIN
#

DNS_SERVER=1.1.1.1

while IFS= read -r line ;
do
  echo $line | grep -qEo '^([0-9]{1,3}[.]){3}[0-9]{1,3}$'
  ret=$?
  if [ $ret -eq 0 ]; then
    # This is a IPv4 address, ignore.
    # echo $line
    continue
  fi

  dig @${DNS_SERVER} $line | grep -q "status: NXDOMAIN"
  ret=$?
  if [ $ret -eq 0 ]; then
    # match, domain not exist
    >&2 echo $line;
  else
    echo $line;
  fi
done
