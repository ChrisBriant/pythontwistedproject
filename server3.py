import sys, redis, uuid,json,ast

from twisted.internet import reactor, ssl
from twisted.web.server import Site
from twisted.web.static import File
from twisted.python import log
from autobahn.twisted.websocket import WebSocketServerFactory, WebSocketServerProtocol, listenWS
from autobahn.twisted.resource import WebSocketResource

# TUTORIAL https://medium.com/python-in-plain-english/identify-websocket-clients-with-autobahn-twisted-and-python-3f90b4c135d4

# Source: https://stackoverflow.com/questions/29951718/autobahn-sending-user-specific-and-broadcast-messages-from-external-application
class BroadcastServerProtocol(WebSocketServerProtocol):
    def onOpen(self):
        self.factory.register(self)

    def onConnect(self, request):
        print("Client connecting: {}".format(request.peer))

    def onMessage(self, payload, isBinary):
        if not isBinary:
            received_data = ast.literal_eval(payload.decode("utf-8"))
            print("msg",received_data)
            if (received_data['type'] == 'broadcast'):
                #Broadcast message
                send_payload = {
                    'type': 'message',
                    'message': received_data['message']
                }
                self.factory.broadcast(json.dumps(send_payload))
            elif received_data['type'] == 'client':
                send_payload = {
                    'type': 'message',
                    'message': 'Cheese'
                }
                self.factory.send_client(received_data['client_id'],json.dumps(send_payload))
            elif received_data['type'] == 'create_room':
                room_list = self.factory.create_room(received_data['client_id'],received_data['name'])
            elif received_data['type'] == 'name':
                self.factory.set_name(received_data['client_id'],received_data['name'])
                send_payload = {
                    'type': 'set_name',
                    'message': received_data['name']
                }
                self.factory.send_client(received_data['client_id'],json.dumps(send_payload))
                #Broadcast client list now a name is set
                self.factory.send_client_list()

    def connectionLost(self, reason):
        print("Connection Lost")
        WebSocketServerProtocol.connectionLost(self, reason)
        self.factory.unregister(self)


class BroadcastServerFactory(WebSocketServerFactory):
    def __init__(self, url):
        WebSocketServerFactory.__init__(self, url)
        self.clients = {}
        self.rooms = {}

    def register(self, client):
        # ids = list(self.clients.keys())
        # if client not in self.clients:
        #     print("registered client {}".format(client.peer))
        #     self.clients.append(client)
        #     print("Here are the clients", self.clients, ids)
        registered = [self.clients[i] for i in list(self.clients.keys())]
        ids = list(self.clients.keys())
        if client not in registered:
            while (cid := str(uuid.uuid4())) in ids:
                pass
            print("registered client {} with id {}".format(client.peer, cid))
            self.clients[cid] = dict()
            self.clients[cid]['client'] = client
            self.clients[cid]['name'] = None
            payload = {
                'type': 'register',
                'yourid':cid
            }
            client.sendMessage(json.dumps(payload).encode())
            #print("Here are the clients", self.clients, ids)

    def send_client_list(self):
        #Get the clients and create
        clients_list = list(self.clients.keys())
        print('client list here',clients_list)
        clients_data = [{'id':cli, 'name':self.clients[cli]['name']} for cli in clients_list]
        payload = {
            'type' : 'client_list',
            'clients': json.dumps(clients_data)
        }
        print('The Clients',self.clients)
        for cid in self.clients:
            print(cid)
            try:
                self.clients[cid]['client'].sendMessage(json.dumps(payload).encode())
            except Exception as e:
                print(e)

    def unregister(self, client):
        if client in self.clients:
            print("unregistered client {}".format(client.peer))
            self.clients.remove(client)

    def broadcast(self, msg):
        # print("broadcasting message '{}' to {} clients ...".format(msg, len(self.clients)))
        # for c in self.clients:
        #     c.sendMessage(msg.encode('utf-8'))
        print("broadcasting message '{}' to {} clients ...".format(msg, len(self.clients)))
        cids = self.clients.keys()
        for cid in cids:
            print('here is a client', self.clients[cid])
            self.clients[cid]['client'].sendMessage(msg.encode('utf-8'))

    def send_client(self,client_id,data):
        print('sending to ',client_id)
        self.clients[client_id]['client'].sendMessage(data.encode('utf-8'))

    def set_name(self,client_id,name):
        print('set name',self.clients)
        self.clients[client_id]['name'] = name

    def create_room(self,client_id,room):
        rooms = self.rooms.keys()
        if room not in rooms:
            self.rooms[room] = dict()
            self.rooms[room]['owner'] = client_id
            self.rooms[room]['name'] = room
            self.rooms[room]['members'] = []
            self.rooms[room]['members'].append(client_id)
            cids = self.clients.keys()
            room_list = [ self.rooms[k] for k in self.rooms.keys()]
            send_payload = {
                'type' : 'room_list',
                'rooms': json.dumps(room_list)
            }
            for cid in cids:
                try:
                    self.clients[cid]['client'].sendMessage(json.dumps(send_payload).encode('utf-8'))
                except Exception as e:
                    print(e)
        else:
            #Send a failure notification
            send_payload = {
                'type' : 'room_failure',
                'reason': 'Room already exists'
            }
            self.clients[client_id]['client'].sendMessage(json.dumps(send_payload).encode('utf-8'))




if __name__ == "__main__":
    log.startLogging(sys.stdout)

    contextFactory = ssl.DefaultOpenSSLContextFactory('keys/server.key',
                                                          'keys/server.crt')
    ServerFactory = BroadcastServerFactory
    factory = BroadcastServerFactory("wss://127.0.0.1:8080")

    factory.protocol = BroadcastServerProtocol
    #listenWS(factory)
    resource = WebSocketResource(factory)

    root = File(".")
    root.putChild(b"ws", resource)
    site = Site(root)
    reactor.listenSSL(8080, site, contextFactory)

    reactor.run()
