# ~/dev/py/ringd/ringd/chanIO.py

import socket
import sys
from fieldz.raw import LEN_PLUS_TYPE, readFieldHdr, readRawVarint
import fieldz.typed as T

from ringd import *

__all__ = ['recvFromCnx', 'sendOnCnx', 'sendToEndPoint', ]

#####################################################################
# XXX THIS HAS JUST BEEN COPIED FROM alertz/alertz/chanIO.py
#####################################################################


def recvFromCnx(cnx, chan):
    """
    Receive a serialized message from a connection into a channel.
    On return the channel has been flipped (offset = 0, limit =
    data length).  Returns the msgNbr.
    """

    # ---------------------------------------------------------------
    # SEE fieldz.msgImpl for an example of this kind of Channel
    # manipulation.  Use a Python buffer to select the region of the
    # buffer we want to write into.
    # ---------------------------------------------------------------

    # receive something from the connection
    chan.clear()
    count = cnx.recv_into(chan.buffer, BUFSIZE)
    if count <= 0:
        raise IOError('initial read of message gets zero bytes')

    # read the header to determine the message type and its length
    (pType, msgNbr) = readFieldHdr(chan)
    # DEBUG
    print("CHAN_IO: count = %d; pType = %s, msgNbr = %s" % (
        count, pType, msgNbr))
    # END
    if pType != LEN_PLUS_TYPE:
        raise IOError('message header type is %d, not LEN_PLUS_TYPE' % pType)
    # XXX raise exception of msgNbr <0 or msgNbr > 2

    msgLen = readRawVarint(chan)

    # XXX ignoring pathological possibility that offset > count

    # if we don't have all of the data, loop getting the rest
    while count < msgLen:
        vBuf = buffer(chan.buffer, count)
        count += cnx.recv_into(vBuf, BUFSIZE - count)
    chan.position = count
    chan.flip()
    return msgNbr


def sendOnCnx(chan, cnx):
    """
    Send a serialized message from a channel over an existing connection.
    Suitable for use by servers sending replies or clients continuing a
    conversation.
    """
    pass        # XXX STUB


def sendToEndPoint(chan, host, port):
    """
    Send a serialized message from a channel over a new connection.
    Suitable for use by clients sending a first message to a server.
    """
    if host is None or len(host) == 0:
        raise IOError('null or empty host name')
    if port < 0 or port > 65535:
        raise IOError("port number '%d' is out of range" % port)
    skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    skt.connect((host, port))
    # DEBUG
    print("SEND_TO_END_POINT: host %s port %s limit %s" % (
        host, port, chan.limit))
    # END
    vBuf = buffer(chan.buffer, 0, chan.limit)
    skt.sendall(vBuf)               # raises exception on error
    return skt                      # the sender has to close it
