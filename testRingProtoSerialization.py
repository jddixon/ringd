#!/usr/bin/env python3

# testRingProtoSerialization.py
import time
import unittest
from io import StringIO

from rnglib import SimpleRNG

from fieldz.parser import StringProtoSpecParser
import fieldz.fieldTypes as F
import fieldz.msgSpec as M
import fieldz.typed as T
from fieldz.chan import Channel
from fieldz.msgImpl import makeMsgClass, makeFieldClass, MsgImpl
from ringd import *

BUFSIZE = 16 * 1024
rng = SimpleRNG(time.time())

# TESTS -------------------------------------------------------------


class TestRingProtoSerialization (unittest.TestCase):

    def setUp(self):
        self.sOM = RINGD_PROTO

    def tearDown(self):
        pass

    # utility functions #############################################
    def leMsgValues(self):
        """ returns a list """
        timestamp = int(time.time())
        key = [0] * 20
        length = rng.nextInt32()
        nodeID = [0] * 20
        src = 'who is responsible'
        path = '/home/jdd/tarballs/something.tar.gz'
        # let's have some random bytes
        rng.nextBytes(nodeID)
        rng.nextBytes(key)

        # DEBUG
        print("GENERATED TIMESTAMP = %d" % timestamp)
        print("GENERATED KEY       = %s" % key)
        print("GENERATED LENGTH    = %s" % length)
        # END

        # NOTE that this is a list
        return [timestamp, key, length, nodeID, src, path]

    def doTestAck(self, text):
        # Create a channel ------------------------------------------
        # its buffer will be used for both serializing # the instance
        # data and, by deserializing it, for creating a second instance.
        chan = Channel(BUFSIZE)
        buf = chan.buffer
        self.assertEquals(BUFSIZE, len(buf))

        # create the AckMsg class ------------------------------
        ackSpec = self.sOM.msgs[0]
        msgName = ackSpec.name
        self.assertEquals('ack', msgName)

        AckMsg = makeMsgClass(self.sOM, 'ack')

        # create a message instance ---------------------------------
        values = [text]
        ack = AckMsg(values)
        (text1) = tuple(values)

        self.assertEquals(ackSpec.name, ack.name)
        # we don't have any nested enums or messages
        self.assertEquals(0, len(ack.enums))
        self.assertEquals(0, len(ack.msgs))

        self.assertEquals(1, len(ack.fieldClasses))
        self.assertEquals(1, len(ack))        # number of fields in instance
        for i in range(len(ack)):
            self.assertEquals(values[i], ack[i].value)

        # verify fields are accessible in the object ----------------
        self.assertEquals(text, ack.text)

        # serialize the object to the channel -----------------------
        buf = chan.buffer
        chan.clear()
        n = ack.writeStandAlone(chan)
        self.assertEquals(0, n)                         # returns msg index
        chan.flip()

        print("ACTUAL LENGTH OF SERIALIZED ACK OBJECT: %u" % chan.limit)

        # deserialize the channel, making a clone of the message ----
        (readBack, n2) = MsgImpl.read(chan, self.sOM)
        self.assertIsNotNone(readBack)
        self.assertTrue(ack.__eq__(readBack))

        # produce another message from the same values --------------
        ack2 = AckMsg(values)
        chan2 = Channel(BUFSIZE)
        n = ack2.writeStandAlone(chan2)
        chan2.flip()
        (copy2, n3) = AckMsg.read(chan2, self.sOM)
        self.assertTrue(ack.__eq__(readBack))
        self.assertTrue(ack2.__eq__(copy2))
        self.assertEquals(n, n3)                # GEEP

    # actual unit tests #############################################

    def testAckWithAndWithoutText(self):
        self.assertIsNotNone(self.sOM)
        self.assertTrue(isinstance(self.sOM, M.ProtoSpec))
        self.assertEquals('org.xlattice.ringd', self.sOM.name)

        self.assertEquals(0, len(self.sOM.enums))
        self.assertEquals(11, len(self.sOM.msgs))
        self.assertEquals(0, len(self.sOM.seqs))

        text = 'nothing much'
        self.doTestAck(text)                    # msg is 16 bytes long
        text = ''
        self.doTestAck(text)                    # msg is 4 bytes

    def testLEMsgSerialization(self):

        # parse the protoSpec

        # XXX highly questionable:
        #   verify that this adds 1 (msg) + 5 (field count) to the number
        #   of entries in getters, putters, etc

        self.assertIsNotNone(self.sOM)
        self.assertTrue(isinstance(self.sOM, M.ProtoSpec))
        self.assertEquals('org.xlattice.ringd', self.sOM.name)

        self.assertEquals(0, len(self.sOM.enums))
        self.assertEquals(11, len(self.sOM.msgs))
        self.assertEquals(0, len(self.sOM.seqs))

        # XXX a foolish test, but we use the variable 'leMsgSpec' below
        leMsgSpec = self.sOM.msgs[5]
        msgName = leMsgSpec.name
        self.assertEquals('logEntry', msgName)

        # Create a channel ------------------------------------------
        # its buffer will be used for both serializing # the instance
        # data and, by deserializing it, for creating a second instance.
        chan = Channel(BUFSIZE)
        buf = chan.buffer
        self.assertEquals(BUFSIZE, len(buf))

        # create the LogEntryMsg class ------------------------------
        LogEntryMsg = makeMsgClass(self.sOM, 'logEntry')

        # create a message instance ---------------------------------
        values = self.leMsgValues()        # a list of quasi-random values
        leMsg = LogEntryMsg(values)
        (timestamp, key, length, nodeID, src, path) = tuple(values)

        # DEBUG
        print("TIMESTAMP = %d" % timestamp)
        print("KEY       = %s" % key)
        print("LENGTH    = %s" % length)
        # END

        self.assertEquals(leMsgSpec.name, leMsg.name)
        # we don't have any nested enums or messages
        self.assertEquals(0, len(leMsg.enums))
        self.assertEquals(0, len(leMsg.msgs))

        self.assertEquals(6, len(leMsg.fieldClasses))
        self.assertEquals(6, len(leMsg))        # number of fields in instance
        for i in range(len(leMsg)):
            self.assertEquals(values[i], leMsg[i].value)

        # verify fields are accessible in the object ----------------
        #(timestamp, key, length, nodeID, src, path) = tuple(values)
        self.assertEquals(timestamp, leMsg.timestamp)
        self.assertEquals(key, leMsg.key)
        self.assertEquals(length, leMsg.length)
        self.assertEquals(nodeID, leMsg.nodeID)
        self.assertEquals(src, leMsg.src)
        self.assertEquals(path, leMsg.path)

        # serialize the object to the channel -----------------------
        buf = chan.buffer
        chan.clear()
        n = leMsg.writeStandAlone(chan)
        self.assertEquals(5, n)                         # returns msg index
        oldPosition = chan.position                     # TESTING flip()
        chan.flip()
        self.assertEquals(oldPosition, chan.limit)      # TESTING flip()
        self.assertEquals(0, chan.position)   # TESTING flip()
        actual = chan.limit

        print("ACTUAL LENGTH OF SERIALIZED OBJECT: %u" % actual)

        # deserialize the channel, making a clone of the message ----
        (readBack, n2) = MsgImpl.read(chan, self.sOM)
        self.assertIsNotNone(readBack)
        self.assertTrue(leMsg.__eq__(readBack))

        # produce another message from the same values --------------
        leMsg2 = LogEntryMsg(values)
        chan2 = Channel(BUFSIZE)
        n = leMsg2.writeStandAlone(chan2)
        chan2.flip()
        (copy2, n3) = LogEntryMsg.read(chan2, self.sOM)
        self.assertTrue(leMsg.__eq__(readBack))
        self.assertTrue(leMsg2.__eq__(copy2))
        self.assertEquals(n, n3)                # GEEP

if __name__ == '__main__':
    unittest.main()
