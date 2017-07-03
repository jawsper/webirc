from django.db import models
from django.conf import settings

class Screen(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    title = models.CharField(max_length=100)

    def __str__(self):
        return '{} / {}'.format(self.user, self.title)

class Message(models.Model):
    screen = models.ForeignKey(Screen)
    sender = models.CharField(max_length=100)
    moment = models.DateTimeField()
    text = models.TextField()

    def serialize(self):
        return {
            'id': self.id,
            'sender': str(self.sender),
            'time': self.moment.isoformat(),
            'text': str(self.text),
        }

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
        return f'IRCServer: {self.user} - {self.hostname}:{self.port}'

    class Meta:
        verbose_name = 'IRC server'


class IRCScreen(models.Model):
    screen = models.ForeignKey(Screen)
    server = models.ForeignKey(IRCServer)
    target = models.CharField(max_length=100)

    def __str__(self):
        return f'IRCScreen(screen="{self.screen}", server="{self.server}", target="{self.target}")'

    class Meta:
        verbose_name = 'IRC screen'

class Event(models.Model):
    TYPE_UNKNOWN = 0
    TYPE_MESSAGE = 1
    TYPE_JOIN = 2
    TYPE_LEAVE = 3

    TYPES = (
        (TYPE_UNKNOWN, 'Unknown'),
        (TYPE_MESSAGE, 'Message'),
        (TYPE_JOIN, 'Join'),
        (TYPE_LEAVE, 'Leave')
    )

    type = models.IntegerField(choices=TYPES, default=TYPE_UNKNOWN)
    source = models.CharField(max_length=100)
    source_raw = models.CharField(max_length=100)
    target = models.CharField(max_length=100)
    target_raw = models.CharField(max_length=100)
    sent = models.DateTimeField()
    received = models.DateTimeField()
    text = models.TextField()
