Kevin Tsao
War Game

Originally Homework #3: Stateful Networks
for CS450: Networking with Professor Chris Kanich
TCP/IP socket programming, asynchronous communication, Python

The purpose of this assignment was to create a basic stateful network protocol that manages asynchronous communication between a server and a given amount of competing clients. 

To complicate matters further, the clients will be competing in a very primitive communication protocol abstracted as the card game War, and the connections can be made lossy, thus removing the guarantee of predictable behavior. Not only must be each game run perfectly - if two clients connect, the game should always have a result even if one player makes illegal moves or disconnects - but any amount of perfect games must also run perfectly concurrently.

My implementation uses the Async IO library for Python to manage the connections. Since we have no guarantee of a number of clients, nor that each client will have a stable connection, nor even that the clients will send the correct messages rather than gibberish, our only choice is to create an event loop that will wait, forever if required, until the proper conditions are met before starting or exiting each game. 

Skeleton code came packaged with the assignment that contributes most of the codebase. My implementation is done within the war.py file marked as "MY WORK" and consists of a few functions. "laggy" is a tester file that simulates a lossy connection, and "example_play" is a pcap file meant to be viewed with Wireshark to show what correct communication should resemble. 
