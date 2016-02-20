# ~/dev/py/pzog/ringHostInfoProto.py

RING_HOST_INFO_PROTO_SPEC="""
protocol org.xlattice.pzog.ringHostInfo

# This represents the contents of a file containing data on several
# (well, one or more) ring hosts.
message ringHostInfo:
 message hostInfo:
  hostName       lString     # @0: alphanumeric only
  ipAddr         lString     # @1: dotted quad; could be fuInt32
  nodeID         fBytes20    # @2: so binary
  pubKey         lString     # @3: or could be lBytes
  privateKey     lString     # @4: ditto
 hosts          hostInfo+
"""
