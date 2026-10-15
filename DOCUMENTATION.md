# Documentation

This documentation is designed to help create your own custom clients

## Client

Clients will connect to a server through a TCP socket
Clients will expect special packets constructed like so:
`<|TAG|>packet_content<|END_TAG|>`

to ensure server security, all tags must be escaped before sending:
`\<\|TAG\|\>user words blah blah blah`
this is to prevent users from sending tags as plain text and potentially breaking client connections

## Server

The Server will accept connections from a client through a TCP socket
Servers will expect special packets constructed like so:
`<|TAG|>packet_content<|END_TAG|>`

the server can handle custom commands, a special packet must be send on initial connect
the server can send its custom name to a client on request: `<|GET_NAME|>` disconnecting immediately afterwards
