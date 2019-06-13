# -*- coding: utf-8 -*-
from kivy.uix.screenmanager import Screen
from kivy.clock import Clock

class Corresp(Screen):
    def refresh_field(self, field):
            def refresh_field(interval):
                field.focus = True
                field.text = ''
            Clock.schedule_once(refresh_field, .12)