import socketio # see env.yml for version
import time

SOCKET_LOGGING = False

# this class provides method to get data from BCP
class BcpSocketInterface:
    def __init__(self):
        # loggers are useful but do slow things down
        self.sio = socketio.Client(logger=SOCKET_LOGGING, 
                engineio_logger=SOCKET_LOGGING)
        h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.82 Safari/537.36'}
        self.sio.connect('wss://api.blockchain.poker/socket.io/',
                headers=h)
        self.requestHandler = SocketEventResponseHandler(self.sio)

    def authenticate(self, username, password):
        authData = {"user": username, 
            "password": password,
            "fingerprint": 1} # fingerprint appears necessary but value is not important
        authResponse = self.requestHandler.emitForResponse("authenticate", authData)
        return (authResponse["validPassword"], authResponse)

    def getHandHistory(self):
        return self.requestHandler.emitForResponse("getRecentHands", {})

    def getHand(self, key):
        return self.requestHandler.emitForResponse("getHistory", {"hand": key})

    def tearDown(self):
        self.sio.disconnect()

# this class specifically handles the mechanics of the socket emit & response
class SocketEventResponseHandler:
    def __init__(self, client: socketio.Client):
        self.client = client
        self.responseData = {}
        self.responseFlag = False
        self.responseTimeout = 1 # seconds
    def emitForResponse(self, eventName: str, data: dict):
        try:
            self.client.emit(eventName, data, callback=self.callback)
            t = time.time()
            while not self.responseFlag and (time.time() - t) <= self.responseTimeout:
                pass # wait for responseData
            self.responseFlag = False
            return self.responseData
        except:
            self.client.disconnect()
            return {}
    def callback(self, data):
        self.responseData = data
        self.responseFlag = True