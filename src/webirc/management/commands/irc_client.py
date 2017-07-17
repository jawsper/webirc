from django.core.management.base import BaseCommand
from channels import Channel

import irc.bot
import irc.client
import irc.connection
import irc.buffer

import socket
import ssl

import logging

logging.getLogger('irc.client').setLevel(logging.INFO)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from webirc.asgi import channel_layer
from webirc.models import IRCServer

def create_message(c, e):
    pass

class DualStackFactory(irc.connection.Factory):
    def connect(self, server_address):
        logger.debug(f'server_address: {server_address}')
        addrinfo = socket.getaddrinfo(*server_address, type=socket.SOCK_STREAM)
        if len(addrinfo) == 0:
            raise Exception(f"No addresses found for {server_address[0]}:{server_address[1]}")
        addrinfo = addrinfo[0]
        logger.debug(f'addrinfo: {addrinfo}')
        sock = self.wrapper(socket.socket(*addrinfo[:3]))
        self.bind_address and sock.bind(self.bind_address)
        sock.connect(server_address)
        return sock
    __call__ = connect

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

    forwarded_events = [
        'pubmsg',
        'privmsg',
        'pubnotice',
        'privnotice',
        'join',
        'part',
        'quit',
        'kick',
        'nick',
        'currenttopic'
        'topicinfo',
        'mode',
        'action',
    ]

    logger_blacklist = [
        'all_raw_messages',
        'pong',
        'whospcrpl', 'endofwho',
        'namreply', 'endofnames',
        'motd', 'endofmotd',
    ]

    def on_all_events(self, c, e):
        if e.type not in self.logger_blacklist:
            logger.info(f'event(type={e.type}, source={e.source}, target={e.target}, args={e.arguments}')

        if not e.type in self.forwarded_events:
            return
        # if e.type == 'all_raw_messages':
        #     # logger.debug(e)
        #     return

        self.send_event(
            type=e.type,
            source=e.source,
            target=e.target,
            arguments=e.arguments,
            tags=e.tags
        )

    def on_join(self, c, e):
        channel = e.target
        self.broadcast_names(channel)

    def on_kick(self, c, e):
        channel = e.target
        self.broadcast_names(channel)

    def on_part(self, c, e):
        channel = e.target
        self.broadcast_names(channel)

    def on_nick(self, c, e):
        pass

    def on_endofnames(self, c, e):
        channel = e.arguments[0]
        self.broadcast_names(channel)

    def on_endofwho(self, c, e):
        channel = e.arguments[0]
        self.broadcast_names(channel)

    def broadcast_names(self, channel):
        names = list(self.channels[channel].users())
        self.send_event(
            type='webirc_names',
            arguments=[channel, names]
        )

    def run(self):
        logger.debug('run')
        while True:
            try:
                logger.debug('connect')
                self._connect()
                self.connection.set_keepalive(30)
                # print(vars(self))
                # print(vars(self.connection))
                while True:
                    channel, raw_message = channel_layer.receive([f'irc.send.{self.server_id}'])
                    if channel:
                        logger.info('channel_layer received {} {}'.format(channel, raw_message))
                        if raw_message['type'] == 'privmsg':
                            target = raw_message['target']
                            text = raw_message['text']
                            self.connection.privmsg(target, text)

                            # send message back to client
                            self.send_event(
                                type='privmsg',
                                source=self.connection.get_nickname(),
                                target=target,
                                arguments=[text]
                            )
                        elif raw_message['type'] == 'names':
                            print('names')
                            self.connection.names([raw_message['channel']])
                    self.reactor.process_once(0.2)
            except irc.client.ServerNotConnectedError:
                logger.warning('irc.client.ServerNotConnectedError')
                continue
            except KeyboardInterrupt:
                logger.info('Received SIGINT, bye bye.')
                break
            finally:
                self.disconnect()

    def send_event(self, *, type,
        source=None, target=None, arguments=None, tags=None):
        import asgiref.base_layer
        try:
            Channel('irc.receive').send({
                'server_id': self.server_id,
                'event': {
                    'type': type,
                    'source': source,
                    'target': target,
                    'arguments': arguments,
                    'tags': tags,
                }
            })
        except asgiref.base_layer.BaseChannelLayer.ChannelFull:
            logger.exception('ChannelFull!')
            import sys
            sys.exit(1)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('server_id')

    def handle(self, *args, server_id=None, **options):
        irc_server = IRCServer.objects.get(id=server_id)
        client = IRCClient.from_webirc_server(irc_server)
        client.run()