#!/usr/bin/env python3
#Python Libraries
import socket, threading, time, os
#Kivy Libraries
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.image import Image
from kivy.factory import Factory
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.properties import ListProperty
#KivyMD Libraries
from kivymd.list import ILeftBody, IRightBody
from kivymd.theming import ThemeManager

class FirstAvatar(ILeftBody, Image):
    source = 'res/images/logo.png'

class SecondAvatar(ILeftBody, Image):
    source = 'res/images/kivy-icon.png'

def thread(my_func): #@thread - запуск метода в потоке
    def wrapper (*args, **kwargs):
        my_thread = threading.Thread(target = my_func, args = args, kwargs = kwargs)
        my_thread.start()
    return wrapper

class VerboseApp(App):
    messages = ListProperty()
    theme_cls = ThemeManager()
    theme_cls.primary_palette = 'Blue'
    theme_cls.theme_style = 'Light'
    # def connector(self):
    #     self.server = ("127.0.1.1",9090)
    #     self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #     try:
    #         self.s.connect(server)
    #         self.s.setblocking(0)
    #     except:
    #         pass

    def __init__(self, **kwargs):
        self.title = 'Verbose'
        self.icon = 'res/images/icon.png'
        super(VerboseApp, self).__init__(**kwargs)

    def on_start(self):
        self.shutdown = False
        self.join = False
        self.uname = 'Пользователь'
        host = socket.gethostbyname(socket.gethostname())
        port = 0
        self.server = ("127.0.1.1",9090)
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.s.connect((host,port))
            self.s.setblocking(0)
        except:
            pass
        self.receiving("RecvThread",self.shutdown)
        return super().on_start()

    def build(self):
        self.mw = Builder.load_file("res/kv/Verbose.kv")
        return self.mw

    def on_stop(self):
        self.shutdown = True
        self.s.close()
        return super().on_stop()

    def add_message(self, text, side, color):
        self.messages.append({
            'message_id': len(self.messages),
            'text': text,
            'side': side,
            'bg_color': color
        })

    def scroll_bottom(self):
        Animation.cancel_all(self.mw.ids.msg_storage, 'scroll_y')
        Animation(scroll_y=0, t='out_quad', d=.5).start(self.mw.ids.msg_storage)

    @thread
    def receiving(self, name, fname): #Принимаем сообщения
        while not self.shutdown:
            try:
                while True:
                    data, addr = self.s.recvfrom(1024)
                    self.add_message(data.encode("utf-8"), 'left', '#332211')
                    self.scroll_bottom()
                    time.sleep(0.2)
            except:
                pass

    def send_message(self, message): #Отправляем сообщения
        try:                    
            if message != "":
                self.add_message(message, 'right', '#00BFFF')
                self.s.sendto(message.encode("utf-8"),self.server)
                self.scroll_bottom()
                message = ''
            time.sleep(0.2)
        except:
            pass



if __name__ in ('__main__','__android__'):
    #Window.size = (1080,1920)
    Window.size = (360,640)
    VerboseApp().run()