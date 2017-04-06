from django.contrib import admin
from .models import Diner, AccessLog, ElementScore

from actions import export_as_excel


@admin.register(Diner)
class DinerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'RFID', 'employee_number', 'created_at',)    
    ordering = ('created_at', 'name') 
    list_editable = ('name', 'RFID', 'employee_number')
    search_fields = ('name', 'RFID', 'employee_number')
    actions = (export_as_excel,)


@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'RFID', 'diner', 'access_to_room', )
    ordering = ('access_to_room',) 
    list_filter = ('diner', 'RFID', 'access_to_room', )
    search_fields = ('RFID',)
    date_hierarchy = 'access_to_room'


@admin.register(ElementScore)
class ElementScoreAdmin(admin.ModelAdmin):
    list_display = ('id', 'element', )
    ordering = ('id',) 
