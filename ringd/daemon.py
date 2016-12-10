# ~/dev/py/ringd/ringd/daemon.py

"""
Code for the ringd server, which should be a daemon.
"""

__all__ = ['clear_logs', 'invoke_the_daemon', 'actually_run_the_daemon']

import socket
import sys
#import time
from traceback import print_exc
import os
try:
    from os import scandir
except ImportError:
    from scandir import scandir

import upax

from optionz import dump_options
from xlattice import check_using_sha
from xlattice.ftlog import LogMgr
from xlattice.proc_lock import ProcLock

# import fieldz.field_types as F
# import fieldz.msg_spec as M
# import fieldz.typed as T

from ringd import BUFSIZE
from ringd.chan_io import recv_from_cnx

from fieldz.chan import Channel
from fieldz.msg_impl import MsgImpl

# DAEMON ------------------------------------------------------------


def clear_logs(options):
    """ Delete any simple files found in the log directory. """
    log_dir = options.log_dir
    print(("DEBUG: clearLogs, log_dir = '%s'" % log_dir))
    if os.path.exists(log_dir):
        if log_dir.startswith('/') or log_dir.startswith('..'):
            raise RuntimeError("cannot delete %s/*" % log_dir)
        count = 0
        for entry in scandir(log_dir):
            if entry.is_file():
                os.unlink(entry.path)
                count += 1

    if options.verbose:
        print("found %u files" % count)


def actually_run_the_daemon(options):
    """
    All necessary resources having been obtained, actually runs the
    daemon.
    """
    verbose = options.verbose
    chan = Channel(BUFSIZE)
    skt = None
    (cnx, addr) = (None, None)
    skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    skt.bind(('', options.port))
    skt.listen(1)
    try:
        running = True
        while running:
            print("\nWAITING FOR CONNECTION")              # DEBUG
            cnx, addr = skt.accept()
            try:
                accept_msg = "CONNECTION FROM %s" % str(addr)
                if verbose:
                    print(accept_msg)
                print("BRANCH TO options.accessLog.log()")
                sys.stdout.flush()
                options.access_log.log(accept_msg)
                print("BACK FROM options.access.log()")
                sys.stdout.flush()

                while True:
                    chan.clear()

#                   print "BRANCH TO recvFromCnx"  ; sys.stdout.flush()
                    msg_ndx = recv_from_cnx(cnx, chan)  # may raise exception

                    # XXX s_obj_model (the former sOM) is UNDEFINIED here
                    (msg, real_ndx) = MsgImpl.read(chan, s_obj_model)
                    # DEBUG
                    print("  MSG_NDX: CALCULATED %s, REAL %s" % (
                        msg_ndx, real_ndx))
                    # END
                    # switch on message type
                    if msg_ndx == 0:
                        print("GOT ZONE MISMATCH MSG")
                        # pylint: disable=no-member
                        print("    timestamp       %s" % msg.timestamp)
                        # pylint: disable=no-member
                        print("    seq_nbr         %s" % msg.seq_nbr)
                        # pylint: disable=no-member
                        print("    zone_name       %s" % msg.zone_name)
                        # pylint: disable=no-member
                        print("    expected_serial %s" % msg.expected_serial)
                        # pylint: disable=no-member
                        print("    /Serial   %s" % msg.actual_serial)
                        # pylint: disable=no-member
                        text = \
                            "mismatch, domain %s: expected serial %s, got %s" % (
                                msg.zone_name, msg.expected_serial,
                                msg.actual_serial)
                        options.alertz_log.log(text)

                    elif msg_ndx == 1:
                        # timestamp, seq_nbr
                        print("GOT CORRUPT LIST MSG")
                        # pylint: disable=no-member
                        print("    timestamp      %s" % msg.timestamp)
                        # pylint: disable=no-member
                        print("    seq_nbr         %s" % msg.seq_nbr)
                        # pylint: disable=no-member
                        text = "corrupt list: %s" % (msg.seq_nbr)
                        options.alertz_log.log(text)

                    elif msg_ndx == 2:
                        # has one field, remarks
                        print("GOT SHUTDOWN MSG")
                        # pylint: disable=no-member
                        print("    remarks        %s" % msg.remarks)
                        running = False
                        skt.close()
                        # XXX STUB: log the message
                        # pylint: disable=no-member
                        text = "shutdown: %s" % (msg.remarks)
                        options.alertz_log.log(text)

                    cnx.close()
                    break                   # permit only one message/cnx

            except KeyboardInterrupt:
                print("<keyboard interrupt received while connection open>")
                if cnx:
                    cnx.close()
                running = False

    except KeyboardInterrupt:
        print("<keyboard interrupt received while listening>")
        # listening socket will be closed
    finally:
        if cnx:
            cnx.close()
        if skt:
            skt.close()

#####################################################################
# GET LOCK ON APP; FINALLY BLOCK FOR THAT LOCK
#####################################################################


def setup_the_app(options):
    """
    Gets a lock on the app directory, sets up log manager and related
    files, runs the daemon, and then unlocks the app directory in a
    finally block.
    """
    app_name = options.app_name
    lock_mgr = None
    access_log = None
    error_log = None

    try:
        lock_mgr = ProcLock(app_name)
        log_mgr = LogMgr(options.log_dir)
        options.log_mgr = log_mgr

        access_log = log_mgr.open('access')
        options.access_log = access_log

        alertz_log = log_mgr.open(app_name)
        options.alertz_log = alertz_log

        error_log = log_mgr.open('error')
        options.error_log = error_log

        actually_run_the_daemon(options)
    finally:
        if log_mgr is not None:
            log_mgr.close()
        if lock_mgr is not None:
            lock_mgr.unlock()


def setup_u_server(options):
    """
    Actually starts a upaxBlockingServer running, then invokes wrapped
    code, then closes server in a finally block.
    """
    no_changes = options.no_changes
    u_path = options.u_path
    using_sha = not options.using_sha3
    verbose = options.verbose

    check_using_sha(using_sha)
    u_server = upax.BlockingServer(u_path, using_sha)
    options.u_server = u_server
    u_log = u_server.log
    options.u_log = u_log
    if verbose:
        print("there were %7u files in %s at the beginning of the run" % (
            len(u_log), u_path))

#   # ---------------------------------------------------------------
#   # XXX This code expects a collection of files in inDir; it posts
#   # each to u_path -- and so is not relevant for our purposes.  THIS
#   # IS HERE AS AN EXAMPLE OF HOW TO WRITE DATA TO uServer
#   # ---------------------------------------------------------------
#   src = args.pgmNameAndVersion    # what goes in the logEntry src field

#   files = os.listdir(args.inDir)
#   for file in files:
#       pathToFile  = os.path.join(args.inDir, file)
#       if using_sha == Q.USING_SHA1:
#           hash        = u.fileSHA1(pathToFile)
#       elif using_sha == Q.USING_SHA2:
#           hash        = u.fileSHA2(pathToFile)
#       elif using_sha == Q.USING_SHA3:
#           hash        = u.fileSHA3(pathToFile)
#       if no_changes:
#           if verbose:     print 'would add %s %s' % (hash, pathToFile)
#       else:
#           uServer.put (pathToFile, hash, src)

#   if verbose:
#       print "there are %7u files in %s at the end of the run" % (
#               len(log), u_path)         # FOO
    try:
        setup_the_app(options)
    finally:
        u_server.close()

#####################################################################
# HANDLE JUST_SHOW; GET LOCK ON U_DIR; FINALLY FOR THAT LOCK
#####################################################################


def invoke_the_daemon(options):
    """
    Completes setting up the namespace; if this isn't a "just-show" run,
    gets a lock on u_path, invokes wrapped code, and releases u_path lock
    in a finally block.
    """
    if options.verbose or options.show_version or options.just_show:
        print(options.pgm_name_and_version)
    if options.show_timestamp:
        print(('run at %s GMT' % options.timestamp))   # could be prettier
    else:
        print()                               # there's a comma up there

    if options.just_show or options.verbose:
        print(dump_options(options))

    lock_mgr = None
    log_mgr = None
    if not options.just_show:
        try:
            lock_mgr = ProcLock(options.u_path)
            log_mgr = LogMgr(options.log_dir)
            options.log_mgr = log_mgr
            setup_u_server(options)
        finally:
            if log_mgr is not None:
                log_mgr.close()
            if lock_mgr is not None:
                lock_mgr.unlock()
