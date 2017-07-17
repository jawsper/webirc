from django.utils import timezone
from dateutil.parser import parse as date_parse
from channels import Channel
from channels.generic.websockets import JsonWebsocketConsumer
from webirc.models import IRCScreen, Screen, Message, EnterExitEvent


from django.dispatch import receiver
from django.db.models.signals import post_save

import logging
logger = logging.getLogger(__name__)

@receiver(post_save, sender=Message)
@receiver(post_save, sender=EnterExitEvent)
def broadcast_message(sender, instance, **kwargs):
    # logger.info('message-save')
    event = instance.event
    group = f'user-{event.screen.user.id}'
    JsonWebsocketConsumer.group_send(group, {
        'events':
        {
            str(event.screen.id): [event.serialize()]
        }
    })

@receiver(post_save, sender=IRCScreen)
def on_ircscreen_save(sender, instance, update_fields, **kwargs):
    logger.info(f'ircscreen-save {instance} {kwargs}')
    if 'topic' in update_fields:
        group = f'user-{instance.screen.user.id}'

        JsonWebsocketConsumer.group_send(group, {
            'topics':
            {
                str(instance.screen.id): instance.topic
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
        topics_dict = {}
        # messages_dict = defaultdict(list)
        for screen in Screen.objects.filter(user=message.user):
            screens_dict[screen.id] = screen.title
        for irc_screen in IRCScreen.objects.filter(screen__user=message.user):
            topics_dict[irc_screen.screen.id] = irc_screen.topic
            Channel(f'irc.send.{irc_screen.server.id}').send({
                'type': 'names',
                'channel': irc_screen.target
            })

            # for message in Message.objects.filter(screen=screen):
            #     messages_dict[str(screen.id)].append(message.serialize())

        for group in self.connection_groups():
            self.group_send(group, {
                'screens': screens_dict,
                'topics': topics_dict,
            })

    def raw_receive(self, message, **kwargs):
        self.groups = ['user-{}'.format(message.user.id)]
        super().raw_receive(message, user=message.user, **kwargs)

    def receive(self, event, user=None, **kwargs):
        if not 'action' in event:
            return

        if event['action'] == 'message':
            if not 'screen_id' in event or not 'text' in event:
                return

            try:
                screen = Screen.objects.get(user=user, id=event['screen_id'])
            except Screen.DoesNotExist:
                logger.debug(f'invalid screen: {event["screen_id"]}')
                return

            try:
                irc_screen = IRCScreen.objects.get(screen=screen)
            except IRCScreen.DoesNotExist:
                logger.debug('invalid irc screen?')
                return

            channel = f'irc.send.{irc_screen.server.id}'
            raw_message = {
                'type': 'privmsg',
                'target': irc_screen.target,
                'text': event['text']
            }
            Channel(channel).send(raw_message)
        elif event['action'] == 'load_events':
            if not 'screen_id' in event:
                return

            try:
                screen = Screen.objects.get(user=user, id=event['screen_id'])
            except Screen.DoesNotExist:
                logger.debug(f'invalid screen: {event["screen_id"]}')
                return

            if 'moment' in event:
                moment = date_parse(event['moment'])
                before = event.get('before', False)
            else:
                moment = timezone.now()
                before = True

            logger.debug(f'screen: {screen}, moment: {moment}, before: {before}')

            params = dict(screen=screen)
            params['moment__lt' if before else 'moment__gt'] = moment

            event_query = screen.event_set.filter(**params)

            self.send({
                'events':
                {
                    str(screen.id): [
                        event.serialize() for event in reversed(event_query.order_by('-moment')[:100])
                    ]
                }
            })
        elif event['action'] == 'screen_name':
            if not 'screen_id' in event:
                return

            try:
                screen = Screen.objects.get(user=user, id=event['screen_id'])
            except Screen.DoesNotExist:
                logger.debug(f'invalid screen: {event["screen_id"]}')
                return

            self.send({
                'screens':
                {
                    str(screen.id): screen.title
                }
            })


    def raw_disconnect(self, message, **kwargs):
        self.groups = ['user-{}'.format(message.user.id)]
        super().raw_disconnect(message, **kwargs)

