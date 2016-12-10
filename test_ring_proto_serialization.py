#!/usr/bin/env python3
# testRingProtoSerialization.py

""" Test the protocol used for communications around the ring. """

import time
import unittest
# from io import StringIO

from rnglib import SimpleRNG

# from fieldz.parser import StringProtoSpecParser
# import fieldz.fieldTypes as F
import fieldz.msg_spec as M
# import fieldz.typed as T
from fieldz.chan import Channel
from fieldz.msg_impl import make_msg_class, MsgImpl
from ringd import RINGD_PROTO

BUFSIZE = 16 * 1024
RNG = SimpleRNG(time.time())

# TESTS -------------------------------------------------------------


class TestRingProtoSerialization(unittest.TestCase):
    """ Test the protocol used for communications around the ring. """

    def setUp(self):
        self.s_obj_model = RINGD_PROTO

    def tearDown(self):
        pass

    # utility functions #############################################
    def le_msg_values(self):
        """ returns a list """
        timestamp = int(time.time())
        key = [0] * 20
        length = RNG.next_int32()
        node_id = [0] * 20
        src = 'who is responsible'
        path = '/home/jdd/tarballs/something.tar.gz'
        # let's have some random bytes
        RNG.next_bytes(node_id)
        RNG.next_bytes(key)

        # DEBUG
        print("GENERATED TIMESTAMP = %d" % timestamp)
        print("GENERATED KEY       = %s" % key)
        print("GENERATED LENGTH    = %s" % length)
        # END

        # NOTE that this is a list
        return [timestamp, key, length, node_id, src, path]

    def do_test_ack(self, text):
        # Create a channel ------------------------------------------
        # its buffer will be used for both serializing # the instance
        # data and, by deserializing it, for creating a second instance.
        chan = Channel(BUFSIZE)
        buf = chan.buffer
        self.assertEqual(BUFSIZE, len(buf))

        # create the ack_msg_cls class ------------------------------
        ack_spec = self.s_obj_model.msgs[0]
        msg_name = ack_spec.name
        self.assertEqual('ack', msg_name)

        ack_msg_cls = make_msg_class(self.s_obj_model, 'ack')

        # create a message instance ---------------------------------
        values = [text]
        ack = ack_msg_cls(values)
        (_) = tuple(values)             # WAS text1

        # pylint: disable=no-member
        self.assertEqual(ack_spec.name, ack.name)
        # we don't have any nested enums or messages
        # pylint: disable=no-member
        self.assertEqual(0, len(ack.enums))
        # pylint: disable=no-member
        self.assertEqual(0, len(ack.msgs))

        # pylint: disable=no-member
        self.assertEqual(1, len(ack.fieldClasses))
        self.assertEqual(1, len(ack))        # number of fields in instance
        for ndx, value in enumerate(ack):
            self.assertEqual(values[ndx], value)

        # verify fields are accessible in the object ----------------
        # pylint: disable=no-member
        self.assertEqual(text, ack.text)

        # serialize the object to the channel -----------------------
        buf = chan.buffer
        chan.clear()
        nnn = ack.write_stand_alone(chan)
        self.assertEqual(0, nnn)                         # returns msg index
        chan.flip()

        print("ACTUAL LENGTH OF SERIALIZED ACK OBJECT: %u" % chan.limit)

        # deserialize the channel, making a clone of the message ----
        (readback, _) = MsgImpl.read(chan, self.s_obj_model)
        self.assertIsNotNone(readback)
        self.assertTrue(ack.__eq__(readback))

        # produce another message from the same values --------------
        ack2 = ack_msg_cls(values)
        chan2 = Channel(BUFSIZE)
        nnn = ack2.write_stand_alone(chan2)
        chan2.flip()
        (copy2, nn3) = ack_msg_cls.read(chan2, self.s_obj_model)
        self.assertTrue(ack.__eq__(readback))
        self.assertTrue(ack2.__eq__(copy2))
        self.assertEqual(nnn, nn3)                # GEEP

    # actual unit tests #############################################

    def test_ack_with_and_without_text(self):
        self.assertIsNotNone(self.s_obj_model)
        self.assertTrue(isinstance(self.s_obj_model, M.ProtoSpec))
        self.assertEqual('org.xlattice.ringd', self.s_obj_model.name)

        self.assertEqual(0, len(self.s_obj_model.enums))
        self.assertEqual(11, len(self.s_obj_model.msgs))
        self.assertEqual(0, len(self.s_obj_model.seqs))

        text = 'nothing much'
        self.do_test_ack(text)                    # msg is 16 bytes long
        text = ''
        self.do_test_ack(text)                    # msg is 4 bytes

    def test_le_msg_serialization(self):

        # parse the protoSpec

        # XXX highly questionable:
        #   verify that this adds 1 (msg) + 5 (field count) to the number
        #   of entries in getters, putters, etc

        self.assertIsNotNone(self.s_obj_model)
        self.assertTrue(isinstance(self.s_obj_model, M.ProtoSpec))
        self.assertEqual('org.xlattice.ringd', self.s_obj_model.name)

        self.assertEqual(0, len(self.s_obj_model.enums))
        self.assertEqual(11, len(self.s_obj_model.msgs))
        self.assertEqual(0, len(self.s_obj_model.seqs))

        # XXX a foolish test, but we use the variable 'leMsgSpec' below
        le_msg_spec = self.s_obj_model.msgs[5]
        msg_name = le_msg_spec.name
        self.assertEqual('logEntry', msg_name)

        # Create a channel ------------------------------------------
        # its buffer will be used for both serializing # the instance
        # data and, by deserializing it, for creating a second instance.
        chan = Channel(BUFSIZE)
        buf = chan.buffer
        self.assertEqual(BUFSIZE, len(buf))

        # create the LogEntryMsg class ------------------------------
        log_entry_msg = make_msg_class(self.s_obj_model, 'logEntry')

        # create a message instance ---------------------------------
        values = self.le_msg_values()        # a list of quasi-random values
        le_msg = log_entry_msg(values)
        (timestamp, key, length, node_id, src, path) = tuple(values)

        # DEBUG
        print("TIMESTAMP = %d" % timestamp)
        print("KEY       = %s" % key)
        print("LENGTH    = %s" % length)
        # END

        # pylint: disable=no-member
        self.assertEqual(le_msg_spec.name, le_msg.name)
        # we don't have any nested enums or messages
        self.assertEqual(0, len(le_msg.enums))
        self.assertEqual(0, len(le_msg.msgs))

        # pylint: disable=no-member
        self.assertEqual(6, len(le_msg.fieldClasses))
        self.assertEqual(6, len(le_msg))        # number of fields in instance
        for ndx, value in enumerate(le_msg):
            self.assertEqual(value, values[ndx])

        # verify fields are accessible in the object ----------------
        #(timestamp, key, length, nodeID, src, path) = tuple(values)
        self.assertEqual(timestamp, le_msg.timestamp)
        # pylint: disable=no-member
        self.assertEqual(key, le_msg.key)
        # pylint: disable=no-member
        self.assertEqual(length, le_msg.length)
        # pylint: disable=no-member
        self.assertEqual(node_id, le_msg.node_id)
        # pylint: disable=no-member
        self.assertEqual(src, le_msg.src)
        # pylint: disable=no-member
        self.assertEqual(path, le_msg.path)

        # serialize the object to the channel -----------------------
        buf = chan.buffer
        chan.clear()
        nnn = le_msg.write_stand_alone(chan)
        self.assertEqual(5, nnn)                         # returns msg index
        old_position = chan.position                     # TESTING flip()
        chan.flip()
        self.assertEqual(old_position, chan.limit)      # TESTING flip()
        self.assertEqual(0, chan.position)   # TESTING flip()
        actual = chan.limit

        print("ACTUAL LENGTH OF SERIALIZED OBJECT: %u" % actual)

        # deserialize the channel, making a clone of the message ----
        (readback, _) = MsgImpl.read(chan, self.s_obj_model)
        self.assertIsNotNone(readback)
        self.assertTrue(le_msg.__eq__(readback))

        # produce another message from the same values --------------
        le_msg2 = log_entry_msg(values)
        chan2 = Channel(BUFSIZE)
        nnn = le_msg2.write_stand_alone(chan2)
        chan2.flip()
        (copy2, nn3) = log_entry_msg.read(chan2, self.s_obj_model)
        self.assertTrue(le_msg.__eq__(readback))
        self.assertTrue(le_msg2.__eq__(copy2))
        self.assertEqual(nnn, nn3)                # GEEP

if __name__ == '__main__':
    unittest.main()
