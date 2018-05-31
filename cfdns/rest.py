import json

from functools import partial

import requests


TIMEOUT = 10


class Rest(object):

    def __init__(self, root, headers=None, timeout=TIMEOUT):
        self.root = root
        self.timeout = timeout
        self.headers = {} if headers is None else headers

    def _request(self, method, path, data=None, headers=None):

        def _headers(headers=None):
            hs = self.headers.copy()
            if headers is not None:
                hs.update(headers)
            hs['Content-Type'] = 'application/json'
            return hs

        resp = {
            'GET': partial(
                requests.get,
                self.root.format(path),
                headers=_headers(),
                params=data,
                timeout=self.timeout
            ),
            'POST': partial(
                requests.post,
                self.root.format(path),
                headers=_headers(),
                data=json.dumps(data),
                timeout=self.timeout
            ),
            'PUT': partial(
                requests.put,
                self.root.format(path),
                headers=_headers(),
                data=json.dumps(data),
                timeout=self.timeout
            ),
            'DELETE': partial(
                requests.delete,
                self.root.format(path),
                headers=_headers(),
                timeout=self.timeout
            ),
        }[method]()
        if resp.status_code == 200:
            resp = resp.json()
            return resp
        return resp.content

    def get(self, path, params=None, headers=None):
        return self._request('GET', path, params, headers)

    def post(self, path, data, headers=None):
        return self._request('POST', path, data, headers)

    def put(self, path, data, headers=None):
        return self._request('PUT', path, data, headers)

    def delete(self, path, headers=None):
        return self._request('DELETE', path, data=None, headers=None)
