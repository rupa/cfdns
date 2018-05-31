import os


URL = 'https://api.cloudflare.com/client/v4{0}'

HEADERS = {
    'X-Auth-Key': os.environ.get('CLOUDFLARE_API'),
    'X-Auth-Email': os.environ.get('CLOUDFLARE_EMAIL')
}

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
