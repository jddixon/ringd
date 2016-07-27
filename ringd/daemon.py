# ~/dev/py/ringd/ringd/daemon.py

__all__ = ['clearLogs', 'invokeTheDaemon',
           ]

import os
import socket
import sys
import time
import u
import upax

from xlattice.ftLog import LogMgr
from xlattice.procLock import ProcLock

import fieldz.fieldTypes as F
import fieldz.msgSpec as M
import fieldz.typed as T

from ringd import *
from ringd.chanIO import *

from fieldz.chan import Channel
from fieldz.msgImpl import makeMsgClass, makeFieldClass, MsgImpl

# DAEMON ------------------------------------------------------------


def clearLogs(options):
    logDir = options.logDir
    print("DEBUG: clearLogs, logDir = '%s'" % logDir)
    if os.path.exists(logDir):
        if logDir.startswith('/') or logDir.startswith('..'):
            raise RuntimeError("cannot delete %s/*" % logDir)
        files = os.listdir(logDir)
        if files:
            if options.verbose:
                print("found %u files" % len(files))
            for file in files:
                os.unlink(os.path.join(logDir, file))


def actuallyRunTheDaemon(options):
    """
    All necessary resources having been obtained, actually runs the
    daemon.
    """
    verbose = options.verbose
    chan = Channel(BUFSIZE)
    s = None
    (cnx, addr) = (None, None)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', options.port))
    s.listen(1)
    try:
        running = True
        while running:
            print("\nWAITING FOR CONNECTION")              # DEBUG
            cnx, addr = s.accept()
            try:
                acceptMsg = "CONNECTION FROM %s" % str(addr)
                if verbose:
                    print(acceptMsg)
                print("BRANCH TO options.accessLog.log()")
                sys.stdout.flush()
                options.accessLog.log(acceptMsg)
                print("BACK FROM options.access.log()")
                sys.stdout.flush()

                while True:
                    chan.clear()

#                   print "BRANCH TO recvFromCnx"  ; sys.stdout.flush()
                    msgNdx = recvFromCnx(cnx, chan)  # may raise exception

                    (msg, realNdx) = MsgImpl.read(chan, sOM)
#                   print "  MSG_NDX: CALCULATED %s, REAL %s" % (
#                                             msgNdx, realNdx)
                    # switch on message type
                    if msgNdx == 0:
                        print("GOT ZONE MISMATCH MSG")
                        print("    timestamp      %s" % msg.timestamp)
                        print("    seqNbr         %s" % msg.seqNbr)
                        print("    zoneName       %s" % msg.zoneName)
                        print("    expectedSerial %s" % msg.expectedSerial)
                        print("    actualSerial   %s" % msg.actualSerial)
                        text = \
                            "mismatch, domain %s: expected serial %s, got %s" % (
                                msg.zoneName, msg.expectedSerial, msg.actualSerial)
                        options.alertzLog.log(text)

                    elif msgNdx == 1:
                        # timestamp, seqNb
                        print("GOT CORRUPT LIST MSG")
                        print("    timestamp      %s" % msg.timestamp)
                        print("    seqNbr         %s" % msg.seqNbr)
                        text = "corrupt list: %s" % (msg.seqNbr)
                        options.alertzLog.log(text)

                    elif msgNdx == 2:
                        # has one field, remarks
                        print("GOT SHUTDOWN MSG")
                        print("    remarks        %s" % msg.remarks)
                        running = False
                        s.close()
                        # XXX STUB: log the message
                        text = "shutdown: %s" % (msg.remarks)
                        options.alertzLog.log(text)

                    cnx.close()
                    break                   # permit only one message/cnx

            except KeyboardInterrupt as ke:
                print("<keyboard interrupt received while connection open>")
                if cnx:
                    cnx.close()
                running = False

    except KeyboardInterrupt as ke:
        print("<keyboard interrupt received while listening>")
        # listening socket will be closed
    finally:
        if cnx:
            cnx.close()
        if s:
            s.close()

#####################################################################
# GET LOCK ON APP; FINALLY BLOCK FOR THAT LOCK
#####################################################################


def setupTheApp(options):
    """
    Gets a lock on the app directory, sets up log manager and related
    files, runs the daemon, and then unlocks the app directory in a
    finally block.
    """
    appName = options.appName
    lockMgr = None
    accessLog = None
    errorLog = None

    try:
        lockMgr = ProcLock(appName)
        logMgr = LogMgr(options.logDir)
        options.logMgr = logMgr

        accessLog = logMgr.open('access')
        options.accessLog = accessLog

        alertzLog = logMgr.open(appName)
        options.alertzLog = alertzLog

        errorLog = logMgr.open('error')
        foptions.errorLog = errorLog

        actuallyRunTheDaemon(options)
    except:
        print_exc()
        sys.exit(1)
    finally:
        if logMgr is not None:
            logMgr.close()
        if lockMgr is not None:
            lockMgr.unlock()


def setupUServer(options):
    """
    Actually starts a upaxBlockingServer running, then invokes wrapped
    code, then closes server in a finally block.
    """
    noChanges = options.noChanges
    uPath = options.uPath
    usingSHA1 = not options.usingSHA3
    verbose = options.verbose

    uServer = upax.BlockingServer(uPath, usingSHA1)
    options.uServer = uServer
    uLog = uServer.log
    options.uLog = uLog
    if verbose:
        print("there were %7u files in %s at the beginning of the run" % (
            len(uLog), uPath))

#   # ---------------------------------------------------------------
#   # XXX This code expects a collection of files in inDir; it posts
#   # each to uPath -- and so is not relevant for our purposes.  THIS
#   # IS HERE AS AN EXAMPLE OF HOW TO WRITE DATA TO uServer
#   # ---------------------------------------------------------------
#   src = args.pgmNameAndVersion    # what goes in the logEntry src field

#   files = os.listdir(args.inDir)
#   for file in files:
#       pathToFile  = os.path.join(args.inDir, file)
#       if usingSHA1:
#           hash        = u.fileSHA1(pathToFile)
#       else:
#           hash        = u.fileSHA3(pathToFile)
#       if noChanges:
#           if verbose:     print 'would add %s %s' % (hash, pathToFile)
#       else:
#           uServer.put (pathToFile, hash, src)

#   if verbose:
#       print "there are %7u files in %s at the end of the run" % (
#               len(log), uPath)         # FOO
    try:
        setupTheApp(options)
    finally:
        uServer.close()

#####################################################################
# HANDLE JUST_SHOW; GET LOCK ON U_DIR; FINALLY FOR THAT LOCK
#####################################################################


def invokeTheDaemon(options):
    """
    Completes setting up the namespace; if this isn't a "just-show" run,
    gets a lock on uPath, invokes wrapped code, and releases uPath lock
    in a finally block.
    """
    if options.verbose or options.showVersion or options.justShow:
        print(options.pgmNameAndVersion)
    if options.showTimestamp:
        print('run at %s GMT' % timestamp)   # could be prettier
    else:
        print()                               # there's a comma up there

    if options.justShow or options.verbose:
        print('configDir        = ' + str(options.configDir))
        print('justShow         = ' + str(options.justShow))
        print('logDir           = ' + str(options.logDir))
        print('noChanges        = ' + str(options.noChanges))
        print('pathToHostInfo   = ' + str(options.pathToHostInfo))
        print('port             = ' + str(options.port))
        print('showTimestamp    = ' + str(options.showTimestamp))
        print('showVersion      = ' + str(options.showVersion))
        print('testing          = ' + str(options.testing))
        print('timestamp        = ' + str(options.timestamp))
        print('usingSHA3        = ' + str(options.usingSHA3))
        print('uPath            = ' + str(options.uPath))
        print('verbose          = ' + str(options.verbose))

    lockMgr = None
    logMgr = None
    if not options.justShow:
        try:
            lockMgr = ProcLock(options.uPath)
            logMgr = LogMgr(options.logDir)
            options.logMgr = logMgr
            setupUServer(options)
        except:
            print_exc()
            sys.exit(1)
        finally:
            if logMgr is not None:
                logMgr.close()
            if lockMgr is not None:
                lockMgr.unlock()
