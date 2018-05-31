from constants import HEADERS
from constants import URL

from rest import Rest


api = Rest(URL, HEADERS)


def list_zones():
    resp = api.get('/zones')
    return {
        x['name']: {
            'status': x['status'],
            'id': x['id']
        }
        for x in resp['result']
    }

def list_records(zone_id, typ=None, name=None):
    params = {}
    if typ is not None:
        params['type'] = typ
    if name is not None:
        params['name'] = name
    resp = api.get(
        '/zones/{0}/dns_records'.format(zone_id),
        params if params else None,
    )
    return sorted([
        {
            'id': x['id'],
            'name': x['name'],
            'type': x['type'],
            'content': x['content'],
            'ttl': x['ttl']
        } for x in resp['result']
    ], key=lambda x: x['name'])

def create_record(zone_id, name, typ, content, ttl=1):
    resp = api.post('/zones/{0}/dns_records'.format(zone_id), {
        'name': name,
        'type': typ,
        'content': content,
        'ttl': ttl,
    })
    try:
        rec = resp['result']
        return '{0:32s} {1:>5s} {2:20s} {3:10d}'.format(
            rec['name'],
            rec['type'],
            rec['content'],
            rec['ttl'],
        )
    except Exception as ex:
        print ex
        return resp

def update_record(zone_id, rec_id, data):
    resp = api.put('/zones/{0}/dns_records/{1}'.format(zone_id, rec_id), data)
    try:
        rec = resp['result']
        return '{0:32s} {1:>5s} {2:20s} {3:10d}'.format(
            rec['name'],
            rec['type'],
            rec['content'],
            rec['ttl'],
        )
    except Exception as ex:
        print ex
        return resp

def delete_record(zone_id, rec_id):
    resp = api.delete('/zones/{0}/dns_records/{1}'.format(zone_id, rec_id))
    try:
        return resp['result']
    except Exception as ex:
        print ex
        return resp

def print_records(domain, typ=None, name=None):
    for record in list_records(domain, typ, name):
        try:
            print '{0:32s} {1:>5s} {2:20s} {3:10d}'.format(
                record['name'],
                record['type'],
                record['content'],
                record['ttl']
            )
        except Exception as ex:
            print ex
            print record
