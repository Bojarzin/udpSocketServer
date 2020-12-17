import random
import socket
import time
from _thread import *
import threading
from datetime import datetime
import json

clients_lock = threading.Lock()
connected = 0

# dictionary for clients IP and Port number
clients = {}

def connectionLoop(sock):
   while True:
      # Listen to next message
      data, addr = sock.recvfrom(1024)
      data = str(data)
      #data = json.loads(data)
      print(data)
      # if the address is already in clients,
      if addr in clients:
         # update heartbeat if it has one
         if 'heartbeat' in data:
            clients[addr]['lastBeat'] = datetime.now()
         if 'updateposition' in data:
            clients[addr]['position'] = data['position']
      else:
         # if the address is new
         if 'connect' in data:
            # add to client dictionary
            clients[addr] = {}
            clients[addr]['lastBeat'] = datetime.now()
            clients[addr]['color'] = 0
            clients[addr]['position'] = 0
            # Message object with command and an array of players
            message = {"cmd": 0,"players": []}

            # New object
            p = {}
            # Add ID as a string from the IP and Port obtained
            p['id'] = str(addr)
            # Add a colour field
            p['color'] = 0
            # Add a position field
            p['position'] = 0
            # Add that player to the array
            message['players'].append(p)

            # Create GameState object like the message
            GameState = {"cmd":4, "players": []}

            # For every key in clients
            for c in clients:
               # If that key == same as the connected player
               if (c == addr):
                  # change to command 3
                  message['cmd'] = 3
               else:
                  message['cmd'] = 0
               
               # new JSON string
               m = json.dumps(message, separators=(",",":"))

               # Create player object
               player = {}
               # Set its ID to current key
               player['id'] = str(c)
               # Set its colour to that of the client's
               player['color'] = clients[c]['color']
               # Set its position to that of the client's
               player['position'] = clients[c]['position']
               # Add player to the GameState
               GameState['players'].append(player)
               # Send message object with new client to the other clients
               sock.sendto(bytes(m,'utf8'), (c[0],c[1]))
            
            # Send the GameState to the new client
            m = json.dumps(GameState)
            sock.sendto(bytes(m, 'utf8'), addr)

def cleanClients(sock):
   while True:
      # Array of dropped clients
      droppedClients = []
      # Every client in keys
      for c in list(clients.keys()):
         # If it's been longer than 5 seconds since the prior heartbeat
         if (datetime.now() - clients[c]['lastBeat']).total_seconds() > 5:
            print('Dropped Client: ', c)
            clients_lock.acquire()
            # Delete the client
            del clients[c]
            clients_lock.release()
            # Add dropped client to array
            droppedClients.append(str(c))

      # Send JSON object with all the dropped clients to the other clients
      message = {"cmd":2, "droppedPlayers": droppedClients}
      m = json.dumps(message, separators=(",", ":"))

      if(len(droppedClients) > 0):
         for c in clients:
            sock.sendto(bytes(m, 'utf8'), (c[0], c[1]))
         
      time.sleep(1)

def gameLoop(sock):
   while True:
      # Print each tick
      print("Beep")
      # Create new GameState object
      GameState = {"cmd": 1, "players": []}
      clients_lock.acquire()
     # print (clients)
      for c in clients:
         # For each client, create a player
         player = {}
         # Get a random colour
         clients[c]['color'] = {"R": random.random(), "G": random.random(), "B": random.random()}
         # Give a position
         clients[c]['position'] = {"X": 0, "Y": 0, "Z": 0}
         # Give new player the ID and colour, add it to GameState
         
         #clients[c]['color'] = {
          #  "R": random.random(),
          #  "G": random.random(),
          #  "B": random.random()
         #}
         
         player['id'] = str(c)
         player['color'] = clients[c]['color']
         player['position'] = clients[c]['position']

         GameState['players'].append(player)
      s=json.dumps(GameState)
      # print(s)
      # Send GameState JSON to all clients
      for c in clients:
         sock.sendto(bytes(s,'utf8'), (c[0],c[1]))
      clients_lock.release()
      time.sleep(1)

def main():
   port = 12345
   s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   s.bind(('', port))
   start_new_thread(gameLoop, (s,))
   start_new_thread(connectionLoop, (s,))
   start_new_thread(cleanClients,(s,))
   while True:
      time.sleep(1)

if __name__ == '__main__':
   main()
