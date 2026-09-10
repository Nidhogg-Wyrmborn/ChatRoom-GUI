# Chat Room Project

This ChatRoom project was created as an exercise in boredom

## How to install

- go to releases
- download a zip
- extract
- run `py Main.py`
- it will install required packages
- restart the program (you may need to keyboard interrupt)

## Servers

To run a server run `py Main.py -s`
It will automatically start a server

#### Note:
To stop the server you must have everyone disconnect!
This will be changed in a later update

## Clients

To run a client there are 2 methods:
#### method 1:
- run `py Main.py -c`
- it will ask for a username and then scan for servers on the local network
- select a server (if multiple are present)
- once connected success!

#### method 2:
- run `py ClientGUI.pyw`
- it will open a GUI
- in the menu bar select Client
  - Scan for servers
- after it scans for servers (as long as one is running)
- select Client
  - Connect to Server
  - a server that has been detected
- the client will then connect to a server and authenticate

## Error Reporting:

If you have found an error, please report it either in the discord forum or in the Issues tracker