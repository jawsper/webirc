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
