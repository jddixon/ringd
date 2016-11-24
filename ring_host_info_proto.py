# ~/dev/py/pzog/ringHostInfoProto.py

RING_HOST_INFO_PROTO_SPEC = """
protocol org.xlattice.pzog.ringHostInfo

# This represents the contents of a file containing data on several
# (well, one or more) ring hosts.
message ringHostInfo:
 message hostInfo:
  hostName       lstring     # @0: alphanumeric only
  ipAddr         lstring     # @1: dotted quad; could be fuInt32
  nodeID         fbytes20    # @2: so binary
  pubKey         lstring     # @3: or could be lBytes
  privateKey     lstring     # @4: ditto
 hosts          hostInfo+
"""
