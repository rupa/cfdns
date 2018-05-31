import sys

from socket import gethostbyname, gethostname
from subprocess import check_output


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
