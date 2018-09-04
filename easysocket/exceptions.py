"""EASYSOCKET EXCEPTIONS"""

class AddressBusy(Exception):

    def __init__(self, server):
        msg = '{} Address already being used: "{}:{}"'.format(server.error_msg, *server.address)
        super().__init__(msg)
