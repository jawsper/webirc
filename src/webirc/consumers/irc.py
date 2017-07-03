from channels.generic import BaseConsumer
from channels.generic.websockets import JsonWebsocketConsumer
import logging
from collections import namedtuple
from webirc.models import Message, Screen, IRCScreen, IRCServer
from django.utils import timezone

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

Event = namedtuple('Event', ('type', 'source', 'target', 'arguments', 'tags'))


class IRCConsumer(BaseConsumer):
    method_mapping = {
        'irc.receive': 'irc_receive',
        # 'irc.send': 'irc_send',
    }

    def _nick_to_sender(self, nick):
        return nick.split('!')[0]


    def _convert_pubmsg(self, content):
        return {
            'tabs': {
                content['target']: content['target']
            },
            'messages': {
                content['target']: [
                    {
                        'text': '<{}> {}'.format(self._nick_to_sender(content['source']), content['arguments'][0])
                    }
                ]
            }
        }
    def _convert_privmsg(self, content):
        return {
            'tabs': {
                self._nick_to_sender(content['source']): content['source']
            },
            'messages': {
                self._nick_to_sender(content['source']): [
                    {
                        'text': '<{}> {}'.format(self._nick_to_sender(content['source']), content['arguments'][0])
                    }
                ]
            }
        }

    def on_privmsg(self, server, event):
        logger.info(f'"{server}": privmsg: {event.arguments[0]}')
        try:
            irc_screen = IRCScreen.objects.get(server=server, target=event.target)
        except IRCScreen.DoesNotExist:
            logger.info(f'screen {event.target} on {server} does not exist, creating')
            screen = Screen(user=server.user, title=f'{server.name} - {event.target}')
            screen.save()
            irc_screen = IRCScreen(screen=screen, server=server, target=event.target)
            irc_screen.save()

        logger.info(f'IRCScreen: {irc_screen}')
        logger.info(f'Screen title: {irc_screen.screen.title}')

        message = Message(
            screen=irc_screen.screen,
            sender=event.source,
            moment=timezone.now(),
            text=event.arguments[0]
            )
        message.save()


    def on_pubmsg(self, server, event):
        self.on_privmsg(server, event)

    def irc_receive(self, message, **kwargs):
        logger.debug(f'irc_receive({message.content})')

        do_nothing = lambda c, e: None

        try:
            server = IRCServer.objects.get(id=message['server_id'])
        except IRCServer.DoesNotExist:
            logger.warning(f'Message arrive for non-existant server {message["server_id"]}')
            return

        event = Event(**message.content['event'])

        method = getattr(self, f'on_{event.type}', do_nothing)
        method(server, event)

    def irc_send(self, message, **kwargs):
        print('irc_send({})'.format(message), kwargs)
        print(message.content)