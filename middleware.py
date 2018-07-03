from ethereum import Ethereum

ethereum = Ethereum()

class healthCheckMW(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        #ethereum.healthcheck()
        return self.app(environ, start_response)