from django.contrib import admin
from . import models

@admin.register(models.Screen)
class ScreenAdmin(admin.ModelAdmin):
    pass

@admin.register(models.IRCServer)
class IRCServerAdmin(admin.ModelAdmin):
    pass

@admin.register(models.IRCScreen)
class IRCScreenAdmin(admin.ModelAdmin):
    pass

@admin.register(models.Event)
class EventAdmin(admin.ModelAdmin):
    pass
@admin.register(models.Message)
class MessageAdmin(admin.ModelAdmin):
    pass
@admin.register(models.EnterExitEvent)
class EnterExitEventAdmin(admin.ModelAdmin):
    pass