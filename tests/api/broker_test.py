from abc import ABCMeta, abstractmethod

class Command(metaclass=ABCMeta):
    @abstractmethod
    def execute(self):
        pass


class Invoker:
    def __init__(self):
        self._on_start = None
        self._on_finish = None

    def set_on_start(self, command: Command):
        self._on_start = command

    def set_on_finish(self, command: Command):
        self._on_finish = command

    def on_start(self):
        self._on_start.execute()


class Receiver:
    def received(self, args):
        print(args)



class ConnectCommand(Command):
    def __init__(self, msg, _receiver):
        self.receiver = _receiver
        self.msg = msg

    def execute(self):
        self.receiver.received(self.msg)


invoker = Invoker()
receiver = Receiver()
invoker.set_on_start(ConnectCommand("Say Hi!", receiver))
invoker.on_start()

