#!/usr/bin/env python
# -*- coding:  utf-8 -*-
"""
stati.tests
~~~~~~~~~~~

Unittests for stati

:copyright: (c) 2014 by GottWall team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from mock import Mock, patch
import json
from datetime import datetime
from .base import BaseTestCase
from stati_net import UDPClient
import responses
from six import b

import socket


class UDPTestCase(BaseTestCase):

    project = "test_gottwall_project"
    private_key = "gottwall_pricatekey"
    public_key = "project_public_key"
    project = "test_gottwall_project"
    host = "127.0.0.1"
    port = 8888
    auth_delimiter = "--custom-stream-auth--"
    chunk_delimiter = "--custom-chunk--"

    test_data = {"name": "orders", "value": 2, "timestamp": datetime.utcnow(),
                 "filters": {"status": ["Completed", "Test"]},
                 "action": "incr"}

    def setUp(self):
        self.client = UDPClient(self.project, self.private_key, self.public_key,
                                host=self.host, port=self.port,
                                auth_delimiter=self.auth_delimiter,
                                chunk_delimiter=self.chunk_delimiter)

    def test_init(self):
        client = self.client

        data = self.test_data
        auth_header = client.auth_header
        serialized_data = client.serialize(auth_header, data["action"],
                                           data['name'], data['timestamp'], data['value'],
                                           data['filters'])
        decoded_data = json.loads(serialized_data)
        self.assertEqual(client.dt_to_ts(data.get('timestamp')),
                          decoded_data['ts'])
        self.assertEqual(data['name'], decoded_data['n'])
        self.assertEqual(data['value'], decoded_data['v'])
        self.assertEqual(data['filters'], decoded_data['f'])
        self.assertEqual(auth_header, decoded_data['auth'])
        self.assertEqual(data['action'], decoded_data['a'])

    def test_headers(self):
        client = self.client

        ts = client.dt_to_ts(datetime.utcnow())
        self.assertEqual(client.auth_header, "GottWallS2 {0} {1} {2} {3}".format(
            ts, client.make_sign(ts), client._solt_base, self.project))

    def test_make_chunk(self):
        client = self.client
        data = self.test_data
        auth = client.auth_header
        serialized_data = client.serialize(auth, data["action"],
                                           data['name'], data['timestamp'], data['value'],
                                           data['filters'])
        self.assertEqual(auth + client.auth_delimiter + serialized_data + client.chunk_delimiter,
                         client.make_chunk(auth, serialized_data))



    def test_send_bucket(self):
        client = self.client
        client.authenticated = True
        auth_header = client.auth_header

        client.sock = Mock()
        client.sock.sendto = Mock()

        client.send_bucket(auth_header, "test_data")
        call_args = client.sock.sendto.call_args_list[0][0]

        self.assertEquals(call_args[0], client.make_chunk(auth_header, "test_data"))
        self.assertEquals(call_args[1], (client.host, client.port))
