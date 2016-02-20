# ringd/__init__.py

import os
from io import StringIO
from ringHostInfoProto  import RING_HOST_INFO_PROTO_SPEC
from ringProtoSpec      import RING_PROTO_SPEC
from fieldz.parser      import StringProtoSpecParser

__all__ = ['__version__',   '__version_date__', 'BUFSIZE',
           'RINGD_PORT',
           'RINGD_APP_DIR',
           'RINGD_APP_NAME',
           'RINGD_PROTO',
           'RING_HOST_INFO_FILE',     
           'RING_HOST_INFO_PROTO',  # the layout of that file
           ]

# - exported constants ----------------------------------------------
__version__      = '0.2.0'
__version_date__ = '2016-02-19'
BUFSIZE                 = 64*1024   # must be big enough for all using protocols

# -------------------------------------------------------------------
# We need to be able to override all of these constants from the 
# command line.
# -------------------------------------------------------------------

RINGD_PORT              = 55556
RINGD_APP_DIR           = '/var/app'
RINGD_APP_NAME          = 'ringd'

RING_HOST_INFO_FILE     = 'hostInfo'
RING_HOST_INFO_PROTO    = \
        StringProtoSpecParser(StringIO(RING_HOST_INFO_PROTO_SPEC)).parse()
RINGD_PROTO   = StringProtoSpecParser(StringIO(RING_PROTO_SPEC)).parse()

