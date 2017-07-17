from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

class Screen(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    title = models.CharField(max_length=100)

    def __str__(self):
        return '{} / {}'.format(self.user, self.title)

class IRCServer(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    hostname = models.CharField(max_length=100)
    port = models.IntegerField(default=6667)
    ssl = models.BooleanField(default=False)
    password = models.CharField(max_length=128, default='')
    nickname = models.CharField(max_length=100)
    realname = models.CharField(max_length=100)

    @property
    def name(self):
        return f'{self.hostname}'

    def __str__(self):
        return f'IRCServer: {self.nickname} @ {self.hostname}:{self.port}'

    class Meta:
        verbose_name = 'IRC server'

class IRCScreenManager(models.Manager):
    def create_screen(self, *, user, title, **kwargs):
        screen = Screen.objects.create(user=user, title=title)
        return self.create(screen=screen, **kwargs)

class IRCScreen(models.Model):
    screen = models.ForeignKey(Screen)
    server = models.ForeignKey(IRCServer)
    target = models.CharField(max_length=100)
    topic = models.CharField(max_length=250, null=True, blank=True, default=None)

    def __str__(self):
        return f'IRCScreen(screen="{self.screen}", server="{self.server}", target="{self.target}")'

    class Meta:
        verbose_name = 'IRC screen'

class Event(models.Model):
    TYPE_UNKNOWN = 0
    TYPE_MESSAGE = 1
    TYPE_ENTER_EXIT = 2
    TYPES = (
        (TYPE_UNKNOWN, 'Unknown'),
        (TYPE_MESSAGE, 'Message'),
        (TYPE_ENTER_EXIT, 'Enter/Exit')
    )

    screen = models.ForeignKey(Screen, null=True)
    moment = models.DateTimeField(default=timezone.now)
    type = models.IntegerField(choices=TYPES, default=TYPE_UNKNOWN)

    def serialize(self):
        data = {
            'id': self.id,
            'moment': self.moment.isoformat()
        }
        try:
            data.update(self.message.serialize())
        except ObjectDoesNotExist:
            pass
        try:
            data.update(self.enterexitevent.serialize())
        except ObjectDoesNotExist:
            pass
        return data

    def __str__(self):
        return f'Event(screen={self.screen}, moment={self.moment})'

class SubEventManager(models.Manager):
    def create_event(self, *, screen=None, moment=None, **kwargs):
        if not screen:
            raise Exception("Need screen")
        event = Event(screen=screen)
        if moment:
            event.moment = moment
        event.save()
        return self.create(event=event, **kwargs)

class Message(models.Model):
    objects = SubEventManager()

    TYPE_PRIVMSG = 0
    TYPE_NOTICE = 1
    TYPE_ACTION = 2

    TYPES = (
        (TYPE_PRIVMSG, 'Privmsg'),
        (TYPE_NOTICE, 'Notice'),
        (TYPE_ACTION, 'Action'),
    )

    event = models.OneToOneField(Event, on_delete=models.CASCADE, primary_key=True)
    type = models.IntegerField(choices=TYPES, default=TYPE_PRIVMSG)
    sender = models.CharField(max_length=100)
    text = models.TextField()

    def serialize(self):
        return {
            'type': self.get_type_display().lower(),
            'source': str(self.sender),
            'text': str(self.text),
        }

    def __str__(self):
        return f'Message(sender={self.sender}, text={self.text[:100]})'

class EnterExitEvent(models.Model):
    objects = SubEventManager()

    TYPE_UNKNOWN = 0
    TYPE_JOIN = 1
    TYPE_PART = 2
    TYPE_KICK = 3
    TYPE_QUIT = 4

    TYPES = (
        (TYPE_UNKNOWN, 'Unknown'),
        (TYPE_JOIN, 'Join'),
        (TYPE_PART, 'Part'),
        (TYPE_KICK, 'Kick'),
        (TYPE_QUIT, 'Quit'),
    )

    event = models.OneToOneField(Event, on_delete=models.CASCADE, primary_key=True)
    type = models.IntegerField(choices=TYPES, default=TYPE_UNKNOWN)
    source = models.CharField(max_length=100, default='')
    target = models.CharField(max_length=100, default='', blank=True)
    reason = models.CharField(max_length=100, default='', blank=True)

    def serialize(self):
        return {
            'type': self.get_type_display().lower(),
            'source': self.source,
            'target': self.target,
            'reason': self.reason
        }

    def _text(self):
        f_strings = {
            EnterExitEvent.TYPE_UNKNOWN: '',
            EnterExitEvent.TYPE_JOIN: '{source} joined',
            EnterExitEvent.TYPE_PART: '{source} left',
            EnterExitEvent.TYPE_KICK: '{source} kicked {target}',
            EnterExitEvent.TYPE_QUIT: '{source} quit',
        }
        return f_strings[self.type].format(source=self.source, target=self.target)

    def __str__(self):
        return f'EnterExitEvent({self._text()})'
