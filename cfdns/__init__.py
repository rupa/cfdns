#!/usr/bin/env python
'''
Dynamic DNS with Cloudflare
'''

import os
import sys

from datetime import datetime
from time import sleep

from cloudflare import list_zones
from cloudflare import list_records
from cloudflare import create_record
from cloudflare import update_record
from cloudflare import delete_record
from cloudflare import print_records
from constants import IFUPD_SCRIPT
from constants import NM_SCRIPT
from constants import PLIST
from network import lan_ip
from network import ssid
from network import wan_ip


def ddns(zone_id, domain, name, ip=None, logfile=None, ttl=300):

    def log():
        if logfile:
            with open(logfile, 'a') as fh:
                fh.write('{0} {1} {2} {3}\n'.format(
                    datetime.now(), ssid(), lan_ip(), ip
                ))
    full_name = '{0}.{1}'.format(name, domain)
    recs = list(list_records(zone_id, 'A', full_name))
    if ip is None:
        ip = wan_ip()
    if recs:
        for rec in recs:
            if rec['content'] == ip:
                continue
            print update_record(zone_id, rec['id'], {
                'type': 'A',
                'name': full_name,
                'content': ip,
                'ttl': ttl,
            })
            log()
    else:
        print create_record(zone_id, '{0}.{1}'.format(name, domain), 'A', ip)
        log()

def main():
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__,
    )
    parser.add_argument(
        '--ddns',
        nargs=2,
        metavar=('DOMAIN', 'NAME'),
        help='update A record for NAME.DOMAIN'
    )
    parser.add_argument(
        '--delete',
        nargs=2,
        metavar=('DOMAIN', 'ID'),
        help='delete ID from DOMAIN'
    )
    parser.add_argument(
        '--list',
        metavar='DOMAIN',
        help='list A records for DOMAIN'
    )
    parser.add_argument(
        '--logfile',
        help='log ddns updates from script in LOGFILE (absolute path)'
    )
    parser.add_argument(
        '--plist',
        nargs=2,
        metavar=('DOMAIN', 'NAME'),
        help='print launchd plist'
    )
    parser.add_argument(
        '--nm',
        nargs=2,
        metavar=('DOMAIN', 'NAME'),
        help='print /etc/NetworkManager/dispatcher.d/ script'
    )
    parser.add_argument(
        '--ifupd',
        nargs=2,
        metavar=('DOMAIN', 'NAME'),
        help='print /etc/network/if-up.d/ script'
    )
    parser.add_argument(
        '--sleep',
        type=int,
        metavar='SECONDS',
        help='sleep before running --ddns (chiefly for launchd)'
    )
    args = parser.parse_args()

    cwd = os.path.split(os.path.abspath(os.path.realpath(sys.argv[0])))[0]

    zone_lookup = list_zones()

    no_args = True
    if args.delete:
        no_args = False
        try:
            zone_id = zone_lookup[args.delete[0]]['id']
        except KeyError:
            print 'unknown zone'
            return
        full_name = '{0}.{1}'.format(args.delete[1], args.delete[0])
        for rec in list_records(zone_id, 'A', full_name):
            if rec['name'] == full_name:
                print delete_record(zone_id, rec['id'])
    if args.ddns:
        if args.sleep:
            # Apparently launchd considers a process that ends in under 10
            # seconds to have failed. And we want to stay on its good side.
            # Also, launchd plist seems to run just a smidge early and we tend
            # to crap out with a connection error if we just go ahead. So let's
            # just sleep a while here, before we do anything.
            sleep(args.sleep)
        no_args = False
        try:
            zone_id = zone_lookup[args.ddns[0]]['id']
        except KeyError:
            print 'unknown zone'
            return
        ddns(zone_id, args.ddns[0], args.ddns[1], logfile=args.logfile)
    if args.list:
        no_args = False
        print_records(zone_lookup[args.list]['id'], 'A')

    if args.plist:
        no_args = False
        print PLIST.format(
            '.'.join(reversed(args.plist[0].split('.'))),
            os.environ.get('CLOUDFLARE_API'),
            os.environ.get('CLOUDFLARE_EMAIL'),
            sys.executable,
            cwd,
            '''
        <string>--logfile</string>
        <string>{0}</string>
            '''.format(args.logfile).rstrip() if args.logfile else '',
            args.plist[0],
            args.plist[1],
        ).strip()
    if args.nm:
        no_args = False
        print NM_SCRIPT.format(
            os.environ.get('CLOUDFLARE_API'),
            os.environ.get('CLOUDFLARE_EMAIL'),
            sys.executable,
            cwd,
            '--logfile "{0}" '.format(args.logfile) if args.logfile else '',
            args.nm[0],
            args.nm[1],
        ).strip()
    if args.ifupd:
        no_args = False
        print IFUPD_SCRIPT.format(
            os.environ.get('CLOUDFLARE_API'),
            os.environ.get('CLOUDFLARE_EMAIL'),
            sys.executable,
            cwd,
            '--logfile "{0}" '.format(args.logfile) if args.logfile else '',
            args.ifupd[0],
            args.ifupd[1],
        ).strip()

    if no_args:
        parser.print_help()

if __name__ == '__main__':
    main()
