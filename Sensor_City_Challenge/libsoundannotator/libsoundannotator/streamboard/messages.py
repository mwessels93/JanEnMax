class BoardMessage(object):
    """ Object used as messages between the Board and processors
    """

    stop = 0
    subscribe = 1
    subscription=2
    networksubscription=3
    testrequiredkeys=4

    def __init__(self, mType, args):
        self.mType = mType
        self.contents = args

    def getContents(self):
        return self.contents

    def getType(self):
        return self.mType

class ProcessorMessage(object):
    """ Object used as messages between the Board and processors
    """

    error = 0
    def __init__(self, mType, contents):
        self.mType = mType
        self.contents = contents

    def getContents(self):
        return self.contents

    def getType(self):
        return self.mType


class NetworkMessageMeta(type):
    def __getattr__(cls, key):
        if key in cls.values:
            return str(key)
        else:
            return None

class NetworkMessage(object):
    __metaclass__ = NetworkMessageMeta
    """ Object used as network message for test handshake between two ends of the pipe
    """

    values = {
        'PING' : "ping",
        'PONG' : "pong"
    }
