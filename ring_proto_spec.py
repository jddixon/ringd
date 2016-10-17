# ~/dev/py/ringd/ringProtoSpec.py


RING_PROTO_SPEC = """
protocol org.xlattice.ringd

# ===================================================================
# ONLY ADD NEW MESSAGE TYPES TO THIS SECTION BY APPENDING THEM!
# The order of declaration of these types may be meaningful.
# ===================================================================

message     ack
 text       lString?

message     bye
 text       lString?

message     error
 code       vuInt32
 text       lString?

message     hello
 dunno      lString?

message     keepAlive
 text       lString?

message     logEntry
 timestamp  fuInt32         # 0: seconds from epoch
 key        fBytes20        # 1: content key
 length     vuInt32         # 2: number of bytes in content
 nodeID     fBytes20        # 3: nodeID of ring host accepting content
 src        lString         # 4: arbitrary contents; ASCII or unicode
 path       lString         # 5: POSIX path using / as separator

message     ok
 text       lString?

# ===================================================================
# DO NOT USE MESSAGE TYPES BELOW THIS LINE
# These message types are not yet being used; until they are moved
# into the section above, can edit and move types and insert new types
# freely.
# ===================================================================

message     ihave
 key        fBytes20
 length     vuInt32         # allows you to allocate an appropriate buffer

message     get
 key        fBytes20

message     put
 key        fBytes20
 content    lBytes          # length is embedded in the lBytes

message     unknown
 key        fBytes20

# ===================================================================
# These define what constitutes an acceptable ring message sequence.
# The 'iHave' sequence is unsatisfactory.  'unknown' is a non-fatal
# response equivalent to "Don't have and don't know where to get it".
# ===================================================================

seq
 # initiator (client)   responder (server) reply

 hello      :   ack | error .
 keepAlive  :   ok
 logEntry   :   ok  | error .
 iHave      :   ok  | error . | (get    : ok | error . | put )
 get        :   put | unknown | error   .
 put        :   ok  | error .
 bye        :   ok  .

# The dot ('.') signifies that the connection is closed.  Connections are
# always closed after an error is detected.

# In the event of a timeout, the connection is just closed by the host
# detecting the condition.  Either side can do this.
"""
