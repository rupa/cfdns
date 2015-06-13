#!/usr/bin/env python
'''
Dynamic DNS with Cloudflare
'''

import json
import os
import sys

from datetime import datetime
from socket import gethostbyname, gethostname
from subprocess import check_output
from time import sleep

import requests

URL = 'https://www.cloudflare.com/api_json.html'

TIMEOUT = 10

PLIST = '''
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN"
          "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{0}.location_change</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>CLOUDFLARE_API</key>
        <string>{1}</string>
        <key>CLOUDFLARE_EMAIL</key>
        <string>{2}</string>
    </dict>
    <key>ProgramArguments</key>
    <array>
        <string>{3}</string>
        <string>{4}/cfdns</string>
        <string>--sleep</string>
        <string>10</string>{5}
        <string>--ddns</string>
        <string>{6}</string>
        <string>{7}</string>
    </array>
    <key>WatchPaths</key>
    <array>
        <string>/Library/Preferences/SystemConfiguration</string>
    </array>
    <key>StandardOutPath</key>
    <string>{4}/{0}.location_change.log</string>
    <key>StandardErrorPath</key>
    <string>{4}/{0}.location_change.log</string>
</dict>
</plist>
'''

NM_SCRIPT = '''
#!/usr/bin/env bash

export CLOUDFLARE_API={0}
export CLOUDFLARE_EMAIL={1}
[ "$2" = "up" -a "$1" != "lo" ] && nohup {2} {3}/cfdns {4}--ddns {5} {5} &
'''

IFUPD_SCRIPT = '''
#!/usr/bin/env bash

export CLOUDFLARE_API={0}
export CLOUDFLARE_EMAIL={1}
[ "$MODE" = "start" -a "$IFACE" != "lo" ] && {{
    nohup {2} {3}/cfdns {4}--ddns {5} {6} &
}}
'''

def ssid():
    if sys.platform == 'darwin':
        info = {}
        for x in check_output([
            '/System/Library/PrivateFrameworks/Apple80211.framework'
            '/Versions/Current/Resources/airport',
            '-I'
        ]).split('\n'):
            if x:
                k, v = x.split(':', 1)
                info[k.strip()] = v.strip()
        return info['SSID']

def lan_ip():
    return gethostbyname(gethostname())

def wan_ip():
    return check_output(
        ['dig', '+short', 'myip.opendns.com', '@resolver1.opendns.com']
    ).strip()

def get(params, headers=None):
    if headers is None:
        headers = {}
    params['tkn'] = os.environ.get('CLOUDFLARE_API')
    params['email'] = os.environ.get('CLOUDFLARE_EMAIL')
    resp = requests.get(URL, headers=headers, params=params, timeout=TIMEOUT)
    if resp.status_code == 200:
        resp = resp.json()
        if 'msg' in resp and resp['msg']:
            sys.stderr.write('ERROR: {0}\n'.format(resp.msg))
        return resp
    return resp.content

def post(data, headers=None):
    if headers is None:
        headers = {}
    data['tkn'] = os.environ.get('CLOUDFLARE_API')
    data['email'] = os.environ.get('CLOUDFLARE_EMAIL')
    resp = requests.post(URL, headers=headers, data=data, timeout=TIMEOUT)
    if resp.status_code == 200:
        resp = resp.json()
        if 'msg' in resp and resp['msg']:
            sys.stderr.write('ERROR: {0}\n'.format(resp.msg))
    return resp

def get_records(domain, typ=None, name=None):
    data = {'a': 'rec_load_all', 'z': domain}
    resp = get(data)
    try:
        records = resp['response']['recs']['objs']
    except Exception as ex:
        print ex
        yield resp
    else:
        for record in sorted(records, key=lambda x: x['content']):
            if typ and record['type'] != typ:
                continue
            if name and record['display_name'] != name:
                continue
            yield record

def create_record(domain, name, data):
    data['a'] = 'rec_new'
    data['z'] = domain
    data['name'] = name
    data['ttl'] = str(data['ttl']) if 'ttl' in data else '1'
    resp = get(data)
    try:
        record = resp['response']['rec']['obj']
        return '{0:20s} {1:>30s} {2:20s}'.format(
            record['rec_id'],
            record['name'],
            record['content']
        )
    except Exception as ex:
        print ex
        return resp

def update_record(domain, rec_id, data):
    data['a'] = 'rec_edit'
    data['z'] = domain
    data['id'] = str(rec_id)
    data['ttl'] = str(data['ttl']) if 'ttl' in data else '1'
    resp = get(data)
    try:
        record = resp['response']['rec']['obj']
        return '{0:20s} {1:>30s} {2:20s}'.format(
            record['rec_id'],
            record['name'],
            record['content']
        )
    except Exception as ex:
        print ex
        return resp

def delete_record(domain, rec_id):
    data = {'a': 'rec_delete', 'z': domain, 'id': str(rec_id)}
    resp = get(data)
    return json.dumps(resp, indent=4, sort_keys=True)

def print_records(domain, typ=None, name=None):
    for record in get_records(domain, typ, name):
        try:
            print '{0:15s} {1:>25s} {2:20s} {3:10s}'.format(
                record['rec_id'],
                record['name'],
                record['content'],
                record['ttl']
            )
        except Exception as ex:
            print ex
            print record

def ddns(domain, name, ip=None, logfile=None, ttl=300):
    def log():
        if logfile:
            with open(logfile, 'a') as fh:
                fh.write('{0} {1} {2} {3}\n'.format(
                    datetime.now(), ssid(), lan_ip(), ip
                ))
    recs = list(get_records(domain, 'A', name))
    if ip is None:
        ip = wan_ip()
    if recs:
        for rec in recs:
            if rec['content'] == ip:
                continue
            print update_record(domain, rec['rec_id'], {
                'type': 'A',
                'name': name,
                'content': ip,
                'ttl': ttl,
            })
            log()
    else:
        print create_record(domain, name, {'type': 'A', 'content': ip})
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

    no_args = True
    if args.delete:
        no_args = False
        print delete_record(args.delete[0], args.delete[1])
    if args.ddns:
        if args.sleep:
            # Apparently launchd considers a process that ends in under 10
            # seconds to have failed. And we want to stay on its good side.
            # Also, launchd plist seems to run just a smidge early and we tend
            # to crap out with a connection error if we just go ahead. So let's
            # just sleep a while here, before we do anything.
            sleep(args.sleep)
        no_args = False
        ddns(args.ddns[0], args.ddns[1], logfile=args.logfile)
    if args.list:
        no_args = False
        print_records(args.list, 'A')
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
