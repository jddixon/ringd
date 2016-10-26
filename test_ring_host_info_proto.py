#!/usr/bin/env python3

# testRingHostInfoProto.py

import binascii
import time
import unittest
from io import StringIO

from rnglib import SimpleRNG
from ringd import RING_HOST_INFO_PROTO
from ring_host_info_proto import RING_HOST_INFO_PROTO_SPEC

import fieldz.fieldTypes as F
import fieldz.msg_spec as M
import fieldz.typed as T
from xlattice.node import Node      # THIS WAS FROM pzog.xlattice...
from fieldz.chan import Channel
from fieldz.msgImpl import makeMsgClass, makeFieldClass

RNG = SimpleRNG(int(time.time()))
# XXX THIS WAS CAUSING A TEST FAILURE; FIXED By s/16/64/
BUFSIZE = 64 * 1024
HOST_BY_NAME = {}
HOST_BY_ADDR = {}
HOST_BY_NODE_ID = {}
HOST_BY_PUB_KEY = {}
HOST_BY_PRIVATE_KEY = {}


class HostInfo(object):
    __slots__ = ['_name', '_ip_addr', '_node_id', '_pub_key',
                 '_private_key', ]

    def __init__(self, name=None, ip_addr=None, node_id=None,
                 pub_key=None, priv_key=None):
        self._name = name
        self._ip_addr = ip_addr
        self._node_id = node_id
        self._pub_key = pub_key
        self._private_key = priv_key

    @classmethod
    def create_random_host(cls):
        name, dotted_q, node_id, pub_key, priv_key = host_info_values()
        return cls(name, dotted_q, node_id, pub_key, priv_key)


class RingHostInfo(object):
    __slots__ = ['_hosts', ]

    def __init__(self, hosts):
        # DEBUG
        # END
        self._hosts = []
        for host in hosts:
            self._hosts.append(host)

    @classmethod
    def create_random_ring(cls):
        ring = ring_data_values()
        return cls(ring)


def ring_data_values():
    count = 2 + RNG.next_int16(4)    # so 2 to 5 hosts
    ring = []
    for _ in range(count):
        host = HostInfo.create_random_host()
        ring.append(host)
    # DEBUG
    print("RING_HOST_INFO_VALUES returning a list of %u hosts" % len(ring))
    # END
    return ring


def host_info_values():
    max_count = 8
    nnn = 0
    while nnn < max_count:
        nnn = nnn + 1
        node = Node(True)    # uses SHA1; generates RSA keys by default
        priv_key = node.key.exportKey()
        pub_key = node.pub_key.exportKey()
        hex_node_id = binascii.b2a_hex(node.node_id)

#       # DEBUG
        print("nodeID is (%s) %s" % (type(node.node_id), node.node_id))
#       print "PRIVATE KEY: " + str(privateKey)
#       print "PUBLIC KEY:  " + repr(pubKey)
#       # END

        name = RNG.next_file_name(8)

        addr = RNG.next_int32()
        dotted_q = '%d.%d.%d.%d' % (
            (addr >> 24 & 0xff),
            (addr >> 16 & 0xff),
            (addr >> 8 & 0xff),
            (addr & 0xff))
        # DEBUG
        print("name is      '%s'" % name)
        print("addr is      '%s'" % addr)
        print("dottedQ is   '%s'" % dotted_q)
        print("hexNodeID is '%s'\n" % hex_node_id)
        # END
        if name in HOST_BY_NAME:
            continue
        if dotted_q in HOST_BY_ADDR:
            continue
        if hex_node_id in HOST_BY_NODE_ID:       # hex value
            continue
        # DEBUG
        # print "PUB_KEY: %s" % pubKey.n
        # END
        if pub_key in HOST_BY_PUB_KEY:
            print("pubKey is not unique")
            continue
        if priv_key in HOST_BY_PRIVATE_KEY:
            print("privateKey is not unique")
            continue

        # we require that all of these fields be unique in the sample set
        HOST_BY_NAME[name] = name      # dumb, but life is short
        HOST_BY_ADDR[dotted_q] = name
        HOST_BY_NODE_ID[hex_node_id] = name
        HOST_BY_PUB_KEY[pub_key] = name
        HOST_BY_PRIVATE_KEY[priv_key] = name

        # NOTE that nodeID is a binary value here
        return (name, dotted_q, node.node_id, pub_key, priv_key)  # GEEP


class TestRingHostInfoProto(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    # utility functions #############################################

    def dump_bufer(self, buf):
        for i in range(16):
            print("0x%02x " % buf[i], end=' ')
        print()

    # actual unit tests #############################################
    def test_ring_host_info_proto(self):
        s_obj_model = RING_HOST_INFO_PROTO
        self.assertIsNotNone(s_obj_model)
        self.assertTrue(isinstance(s_obj_model, M.ProtoSpec))
        self.assertEqual('org.xlattice.pzog.ringHostInfo', s_obj_model.name)
        self.assertEqual(0, len(s_obj_model.enums))
        self.assertEqual(1, len(s_obj_model.msgs))
        self.assertEqual(0, len(s_obj_model.seqs))

        # OUTER MESSAGE SPEC ----------------------------------------
        msg_spec = s_obj_model.msgs[0]
        field = msg_spec[0]
        self.assertEqual(field.name, 'hosts')
        self.assertEqual(field.fTypeName, 'hostInfo')
        self.assertEqual(field.quantifier, M.Q_PLUS)

        # INNER MESSAGE SPEC ----------------------------------------
        msg_spec = s_obj_model.msgs[0].msgs[0]
        self.assertEqual(msg_spec.fName(0), 'hostName')
        self.assertEqual(msg_spec.fTypeName(0), 'lString')
        self.assertEqual(msg_spec.fName(1), 'ip_addr')
        self.assertEqual(msg_spec.fTypeName(1), 'lString')
        self.assertEqual(msg_spec.fName(2), 'node_id')
        self.assertEqual(msg_spec.fTypeName(2), 'fBytes20')
        self.assertEqual(msg_spec.fName(3), 'pub_key')
        self.assertEqual(msg_spec.fTypeName(3), 'lString')
        self.assertEqual(msg_spec.fName(4), 'priv_key')
        self.assertEqual(msg_spec.fTypeName(4), 'lString')
        try:
            msg_spec.fName(5)
            self.fail('did not catch reference to non-existent field')
        except IndexError:
            pass                                                    # GEEP

    # ---------------------------------------------------------------
    def test_caching(self):
        """ verify that classes with the same definition are cached """
        s_obj_model = RING_HOST_INFO_PROTO
        proto_name = s_obj_model.name
        self.assertTrue(isinstance(s_obj_model, M.ProtoSpec))

        outer_msg_spec = s_obj_model.msgs[0]
        inner_msg_spec = s_obj_model.msgs[0].msgs[0]
        OuterMsg = makeMsgClass(s_obj_model, outer_msg_spec.name)
        # NOTE change in parent
        InnerMsg = makeMsgClass(outer_msg_spec, inner_msg_spec.name)

        # TEST INNER MESSAGE ########################################
        Clz0 = makeMsgClass(outer_msg_spec, inner_msg_spec.name)
        Clz1 = makeMsgClass(outer_msg_spec, inner_msg_spec.name)
        # we cache classes, so the two should be the same
        self.assertEqual(id(Clz0), id(Clz1))

        # test that msg instances created from the same value lists differ
        values = host_info_values()
        inner_msg0 = Clz0(values)
        inner_msg1 = Clz0(values)
        # we don't cache instances, so these will differ
        self.assertNotEqual(id(inner_msg0), id(inner_msg1))

        # verify that field classes are cached
        field_spec = inner_msg_spec[0]
        dotted_name = '%s.%s' % (proto_name, inner_msg_spec.name)
        F0 = makeFieldClass(dotted_name, field_spec)
        F1 = makeFieldClass(dotted_name, field_spec)
        self.assertEqual(id(F0), id(F1))           # GEEP

        # TEST OUTER MESSAGE ########################################
        Clz2 = makeMsgClass(s_obj_model, outer_msg_spec.name)
        Clz3 = makeMsgClass(s_obj_model, outer_msg_spec.name)
        # we cache classe, so the two should be the same
        self.assertEqual(id(Clz2), id(Clz3))

        # test that msg instances created from the same value lists differ
        ring = ring_data_values()  # a list of random hosts

        # 'values_' is a list of field values.  In this case, the single
        # value is itself a list, a list of HostInfo value lists.
        values_ = [ring]            # a list whose only member is a list

        outer_msg0 = Clz2(values_)
        outer_msg1 = Clz2(values_)
        # we don't cache instances, so these will differ
        self.assertNotEqual(id(outer_msg0), id(outer_msg1))

        field_spec = outer_msg_spec[0]
        dotted_name = '%s.%s' % (proto_name, outer_msg_spec.name)
        F0 = makeFieldClass(dotted_name, field_spec)
        F1 = makeFieldClass(dotted_name, field_spec)
        self.assertEqual(id(F0), id(F1))           # GEEP

    # ---------------------------------------------------------------
    def testRingHostInfoProtoSerialization(self):
        s_obj_model = RING_HOST_INFO_PROTO
        proto_name = s_obj_model.name
        outer_msg_spec = s_obj_model.msgs[0]
        inner_msg_spec = s_obj_model.msgs[0].msgs[0]
        OuterMsg = makeMsgClass(s_obj_model, outer_msg_spec.name)
        # NOTE change in parent
        InnerMsg = makeMsgClass(outer_msg_spec, inner_msg_spec.name)

        # Create a channel ------------------------------------------
        # its buffer will be used for both serializing # the instance
        # data and, by deserializing it, for creating a second instance.
        chan = Channel(BUFSIZE)
        buf = chan.buffer
        self.assertEqual(BUFSIZE, len(buf))

        # create a message instance ---------------------------------

        # create some HostInfo instances
        count = 2 + RNG.next_int16(7)  # so 2 .. 8
        ring = []
        for nnn in range(count):
            # should avoid dupes
            values = host_info_values()
            ring.append(InnerMsg(values))

        outer_msg = OuterMsg([ring])     # a list whose member is a list

        # serialize the object to the channel -----------------------
        nnn = outer_msg.writeStandAlone(chan)
        old_position = chan.position
        chan.flip()

        self.assertEqual(old_position, chan.limit)
        self.assertEqual(0, chan.position)

        # deserialize the channel, making a clone of the message ----
        (readback, nn2) = OuterMsg.read(chan, s_obj_model)
        self.assertIsNotNone(readback)

        # verify that the messages are identical --------------------
        self.assertTrue(outer_msg.__eq__(readback))
        self.assertEqual(nnn, nn2)

        # produce another message from the same values --------------
        outerMsg2 = OuterMsg([ring])
        chan2 = Channel(BUFSIZE)
        nnn = outerMsg2.writeStandAlone(chan2)
        chan2.flip()
        (copy2, nn3) = OuterMsg.read(chan2, s_obj_model)
        self.assertTrue(outer_msg.__eq__(copy2))
        self.assertTrue(outerMsg2.__eq__(copy2))                   # GEEP

    # ---------------------------------------------------------------
    def round_trip_ring_host_info_instance_to_wire_format(
            self, spec, ring_host):

        # invoke WireMsgSpecWriter
        # XXX STUB

        # invoke WireMsgSpecParser
        # XXX STUB

        pass

    def test_round_trip_ring_host_info_instances_to_wire(self):
        ring_data_spec = RING_HOST_INFO_PROTO

        count = 3 + RNG.next_int16(6)   # so 3..8 inclusive

        # make that many semi-random nodes, taking care to avoid duplicates,
        # and round-trip each
        for _ in range(count):
            ring_host = HostInfo.create_random_host()
            self.round_trip_ring_host_info_instance_to_wire_format(
                ring_data_spec, ring_host)  # GEEP


if __name__ == '__main__':
    unittest.main()
