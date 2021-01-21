import sys, redis, uuid,json

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
            print("msg")
            if (msg := payload.decode("utf-8")).startswith("@:"):
                #Broadcast message
                send_payload = {
                    'type': 'message',
                    'message': msg
                }
                self.factory.broadcast(json.dumps(send_payload))

    def connectionLost(self, reason):
        WebSocketServerProtocol.connectionLost(self, reason)
        self.factory.unregister(self)


class BroadcastServerFactory(WebSocketServerFactory):
    def __init__(self, url):
        WebSocketServerFactory.__init__(self, url)
        self.clients = {}

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
            self.clients[cid] = client
            payload = {
                'type': 'register',
                'yourid':cid
            }
            client.sendMessage(json.dumps(payload).encode())
            payload = {
                'type' : 'client_list',
                'clients':ids
            }
            print(self.clients)
            for cid in self.clients:
                print(cid)
                self.clients[cid].sendMessage(json.dumps(payload).encode())
            #print("Here are the clients", self.clients, ids)

    def unregister(self, client):
        if client in self.clients:
            print("unregistered client {}".format(client.peer))
            self.clients.remove(client)

    def broadcast(self, msg):
        # print("broadcasting message '{}' to {} clients ...".format(msg, len(self.clients)))
        # for c in self.clients:
        #     c.sendMessage(msg.encode('utf-8'))
        print("broadcasting message '{}' to {} clients ...".format(msg, len(self.clients)))
        for cid in self.clients:
            self.clients[cid].sendMessage(msg.encode('utf-8'))

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
