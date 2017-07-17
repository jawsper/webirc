from channels.generic import BaseConsumer
from channels.generic.websockets import JsonWebsocketConsumer
import logging
from collections import namedtuple
from webirc.models import Message, EnterExitEvent, IRCScreen, IRCServer

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

Event = namedtuple('Event', ('type', 'source', 'target', 'arguments', 'tags'))

def get_or_create_screen(server, target):
    try:
        irc_screen = IRCScreen.objects.get(server=server, target=target)
    except IRCScreen.DoesNotExist:
        logger.info(f'screen {target} on {server} does not exist, creating')
        irc_screen = IRCScreen.objects.create_screen(
            user=server.user,
            title=f'{server.name} - {target}',

            server=server,
            target=target
        )
    return irc_screen

class IRCConsumer(BaseConsumer):
    method_mapping = {
        'irc.receive': 'irc_receive',
    }

    def on_privmsg(self, server, event):
        # logger.info(f'"{server}": {event.type}: {event.arguments[0]}')
        irc_screen = get_or_create_screen(server, event.target)

        message_type = Message.TYPE_PRIVMSG
        if 'notice' in event.type:
            message_type = Message.TYPE_NOTICE
        elif event.type == 'action':
            message_type = Message.TYPE_ACTION

        Message.objects.create_event(
            screen=irc_screen.screen,
            type=message_type,
            sender=event.source,
            text=event.arguments[0]
        )

    on_pubmsg = on_privmsg
    on_pubnotice = on_privmsg
    on_privnotice = on_privmsg
    on_action = on_privmsg


    def on_join(self, server, event):
        irc_screen = get_or_create_screen(server, event.target)
        EnterExitEvent.objects.create_event(
            screen=irc_screen.screen,

            type=EnterExitEvent.TYPE_JOIN,
            source=event.source)
    def on_part(self, server, event):
        irc_screen = get_or_create_screen(server, event.target)
        create_args = dict(
            screen=irc_screen.screen,

            type=EnterExitEvent.TYPE_PART,
            source=event.source
        )
        if len(event.arguments) > 0:
            create_args['reason'] = event.arguments[0]
        EnterExitEvent.objects.create_event(**create_args)

    def on_kick(self, server, event):
        """
            kick event:
                type = "kick"
                source = person who kicks
                target = channel from which is kicked
                arguments[0] = person who gets kicked
                arguments[1] = kick reason
        """
        irc_screen = get_or_create_screen(server, event.target)
        event = EnterExitEvent.objects.create_event(
            screen=irc_screen.screen,

            type=EnterExitEvent.TYPE_KICK,
            source=event.source,
            target=event.arguments[0],
            reason=event.arguments[1])

    def on_quit(self, server, event):
        """
            quit event:
                type = "quit"
                source = person who quits
                target = None
                arguments[0] = quit reason
        """
        logger.debug(f'on_quit {event}')

    def on_webirc_names(self, server, event):
        channel, names = event.arguments
        logger.debug(f'on_webirc_names (channel {channel} has {len(names)} names)')
        # print(channel, names)

        try:
            irc_screen = IRCScreen.objects.get(server=server, target=channel)
        except IRCScreen.DoesNotExist:
            return

        group = f'user-{irc_screen.screen.user.id}'

        JsonWebsocketConsumer.group_send(group, {
            'names':
            {
                str(irc_screen.screen.id): names
            }
        })

    def on_currenttopic(self, server, event):
        channel, topic = event.arguments
        print(f'on_currenttopic(channel: {channel}, topic: {topic})')

        try:
            irc_screen = IRCScreen.objects.get(server=server, target=channel)
        except IRCScreen.DoesNotExist:
            return

        irc_screen.topic = topic
        irc_screen.save(update_fields=['topic'])

        # group = f'user-{irc_screen.screen.user.id}'

        # JsonWebsocketConsumer.group_send(group, {
        #     'topics':
        #     {
        #         str(irc_screen.screen.id): topic
        #     }
        # })

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
