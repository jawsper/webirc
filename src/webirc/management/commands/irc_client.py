from django.core.management.base import BaseCommand
from channels import Channel
from channels.generic.websockets import JsonWebsocketConsumer

import irc.bot
import irc.client
import irc.connection
import irc.buffer

import socket
import ssl

import logging
# logging.basicConfig(format='[%(asctime)s] %(name)s %(levelname)s: %(message)s', level=logging.DEBUG)

logging.getLogger('irc.client').setLevel(logging.INFO)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from webirc.asgi import channel_layer
from webirc.models import IRCServer

def create_message(c, e):
    pass

class DualStackFactory(irc.connection.Factory):
    def connect(self, server_address):
        addrinfo = socket.getaddrinfo(*server_address, type=socket.SOCK_STREAM)[0]
        if len(addrinfo) == 0:
            raise Exception(f"No addresses found for {server_address[0]}:{server_address[1]}")
        addrinfo = addrinfo[0]
        sock = self.wrapper(socket.socket(*addrinfo[:3]))
        self.bind_address and sock.bind(self.bind_address)
        sock.connect(server_address)
        return sock

class IRCClient(irc.bot.SingleServerIRCBot):
    buffer_class = irc.buffer.LenientDecodingLineBuffer

    @classmethod
    def from_webirc_server(cls, server):
        server_spec = irc.bot.ServerSpec(server.hostname, server.port, server.password)
        connect_factory = DualStackFactory(wrapper=ssl.wrap_socket if server.ssl else lambda x: x)
        return cls([server_spec], server.nickname, server.realname, server_id=server.id, connect_factory=connect_factory)

    def __init__(self, *args, server_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.server_id = server_id
        self.connection.add_global_handler('all_events', self.on_all_events, -20)

    def on_all_events(self, c, e):
        if e.type == 'all_raw_messages':
            return
        logger.info(f'event: {e.type}; {e.arguments}')

        Channel('irc.receive').send({
            'server_id': self.server_id,
            'event': {
                'type': e.type,
                'source': e.source,
                'target': e.target,
                'arguments': e.arguments,
                'tags': e.tags
            }
        })

    def run(self):
        logger.debug('run')
        while True:
            try:
                logger.debug('connect')
                self._connect()
                self.connection.set_keepalive(30)
                while True:
                    channel, raw_message = channel_layer.receive([f'irc.send.{self.server_id}'])
                    if channel:
                        logger.info('channel_layer received {} {}'.format(channel, raw_message))
                        target = raw_message['target']
                        text = raw_message['text']
                        self.connection.privmsg(target, text)
                        Channel('irc.receive').send({
                            'server_id': self.server_id,
                            'event': {
                                'type': 'privmsg',
                                'source': self.connection.get_nickname(),
                                'target': target,
                                'arguments': [text],
                                'tags': None,
                            }
                        })
                    self.reactor.process_once(0.2)
            except irc.client.ServerNotConnectedError:
                logger.warning('irc.client.ServerNotConnectedError')
                continue
            except KeyboardInterrupt:
                logger.info('Received SIGINT, bye bye.')
                break
            finally:
                self.disconnect()


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('server_id')

    def handle(self, *args, server_id=None, **options):
        irc_server = IRCServer.objects.get(id=server_id)
        client = IRCClient.from_webirc_server(irc_server)
        client.run()

        # print(args)
        # print(options)
        # JsonWebsocketConsumer.group_send('chat',
        # {
        #     'tabs': {
        #         'freenode-_channel_tkkrlab': 'Freenode - #tkkrlab'
        #         # 'test_tab': 'Hello world!'
        #     },
        #     'messages': {
        #         'freenode-_channel_tkkrlab': [
        #             {
        #                 'time': 'now',
        #                 'sender': 'irc_client',
        #                 'text': 'Hello world!'
        #             }
        #         ]
        #     }
        # })