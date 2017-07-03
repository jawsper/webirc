from django.utils import timezone
from dateutil.parser import parse as date_parse
from channels import Channel
from channels.generic.websockets import JsonWebsocketConsumer
from webirc.models import IRCScreen, Screen, Message
from collections import defaultdict


from django.dispatch import receiver
from django.db.models.signals import post_save

import logging
logger = logging.getLogger(__name__)

@receiver(post_save, sender=Message)
def broadcast_message(sender, instance, **kwargs):
    logger.info('message-save')
    group = f'user-{instance.screen.user.id}'
    JsonWebsocketConsumer.group_send(group, {
        'messages':
        {
            str(instance.screen.id): [
                instance.serialize()
            ]
        }
    })

class MyConsumer(JsonWebsocketConsumer):
    http_user_and_session = True
    groups = []

    def raw_connect(self, message, **kwargs):
        if not message.user.is_authenticated():
            message.reply_channel.send({'close': True})
            return
        self.groups = ['user-{}'.format(message.user.id)]
        super().raw_connect(message, **kwargs)

    def connect(self, message, **kwargs):
        super().connect(message, **kwargs)
        screens_dict = {}
        # messages_dict = defaultdict(list)
        for screen in Screen.objects.filter(user=message.user):
            screens_dict[screen.id] = screen.title
            # for message in Message.objects.filter(screen=screen):
            #     messages_dict[str(screen.id)].append(message.serialize())

        for group in self.connection_groups():
            self.group_send(group, {
                'screens': screens_dict,
                'names': {
                    1: ['alice', 'bob', 'carl'] * 20
                }
            })

    def raw_receive(self, message, **kwargs):
        self.groups = ['user-{}'.format(message.user.id)]
        super().raw_receive(message, user=message.user, **kwargs)

    def receive(self, message, user=None, **kwargs):
        print(message)
        if not 'action' in message:
            return

        if message['action'] == 'message':
            if not 'screen_id' in message or not 'text' in message:
                return

            try:
                screen = Screen.objects.get(user=user, id=message['screen_id'])
            except Screen.DoesNotExist:
                print(f'invalid screen: {message["screen_id"]}')
                return
            print(screen)

            try:
                irc_screen = IRCScreen.objects.get(screen=screen)
            except IRCScreen.DoesNotExist:
                print('invalid irc screen?')
                return

            channel = f'irc.send.{irc_screen.server.id}'
            raw_message = {
                'type': 'privmsg',
                'target': irc_screen.target,
                'text': message['text']
            }
            Channel(channel).send(raw_message)
        elif message['action'] == 'load_messages':
            if not 'screen_id' in message:
                return

            try:
                screen = Screen.objects.get(user=user, id=message['screen_id'])
            except Screen.DoesNotExist:
                print('invalid screen: {}'.format(message['screen_id']))
                return

            if 'moment' in message:
                moment = date_parse(message['moment'])
                before = message.get('before', False)
            else:
                moment = timezone.now()
                before = True

            print(screen, moment, before)

            params = dict(screen=screen)
            params['moment__lt' if before else 'moment__gt'] = moment

            message_query = Message.objects.filter(**params)

            self.send({
                'messages':
                {
                    str(screen.id): [
                        message.serialize() for message in message_query
                    ]
                }
            })


    def raw_disconnect(self, message, **kwargs):
        self.groups = ['user-{}'.format(message.user.id)]
        super().raw_disconnect(message, **kwargs)

