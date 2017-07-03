from channels.routing import route_class
from . import consumers
from .consumers import irc

channel_routing = [
    route_class(consumers.MyConsumer),
    route_class(irc.IRCConsumer)
]
