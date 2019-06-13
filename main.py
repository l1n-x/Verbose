#!/usr/bin/env python3
#Python Libraries
from os import path, listdir
import socket
from sys import argv
import threading
import sqlite3

#Kivy Libraries
import kivy
from kivy.animation import Animation
from kivy.app import App
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ListProperty, ObjectProperty, StringProperty
from kivy.uix.image import Image
from kivy.utils import get_color_from_hex, get_hex_from_color
from kivymd.pickers import MDThemePicker
from kivymd.theming import ThemeManager
from kivymd.utils.cropimage import crop_image
from plyer import notification
#Custom Libraries
from libs.uix.baseclass.startscreen import StartScreen

directory = path.split(path.abspath(argv[0]))[0]
Window.softinput_mode = 'below_target' #Сдвигаем экран до текстового поля

class VerboseApp(App):
    conn = sqlite3.connect(path.join(directory, 'data/user_data'))
    cur = conn.cursor()
    cur.execute('SELECT Theme FROM userconfig')    
    theme_cls = ThemeManager()
    theme_cls.primary_palette = 'Blue'
    theme_cls.theme_style = cur.fetchone()[0]
    server = ("185.20.225.163",9090)
    messages = ListProperty()
    
    def __init__(self, **kwargs):
        self.title = 'Verbose'
        self.icon = 'data/images/icon.png'
        super(VerboseApp, self).__init__(**kwargs)
        Window.bind(on_keyboard=self.back_screen)
        self.userinfo()
        self.use_kivy_settings = False
        self.list_previous_screens = ['profile']
        self.window = Window
        self.manager = None
        self.shutdown = False
        self.s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.s.connect(self.server)
        self.s.setblocking(0)
        self.s.sendto(("I'm here!").encode("utf-8"),(self.server))

    def theme(self,style):       
        if style == 'Dark':
            self.cur.execute("UPDATE userconfig SET Theme = 'Dark' WHERE Theme = 'Light'")
        elif style == 'Light':
            self.cur.execute("UPDATE userconfig SET Theme = 'Light' WHERE Theme = 'Dark'")
        self.conn.commit()

    def userinfo(self):
        self.user_info = {'status':'Не заполнено','born':'Не заполнено',
        'country':'Не заполнено','city':'Не заполнено',
        'tel':'Не заполнено','about':'Не заполнено'}
        self.cur.execute("SELECT * FROM userinfo")
        profile = self.cur.fetchone()
        self.user_info['status'] = profile[0]
        self.user_info['born'] = profile[1]
        self.user_info['country'] = profile[2]
        self.user_info['city'] = profile[3]
        self.user_info['tel'] = profile[4]
        self.user_info['about'] = profile[5]

    def open_settings(self, *largs): #Отключение настроек Kivy
        pass

    def build(self):
        self.load_all_kv_files(path.join(self.directory, 'libs', 'uix', 'kv'))
        self.screen = StartScreen()
        self.manager = self.screen.ids.manager
        return self.screen

    def load_all_kv_files(self, directory_kv_files):
        for kv_file in listdir(directory_kv_files):
            kv_file = path.join(directory_kv_files, kv_file)
            if path.isfile(kv_file):
                with open(kv_file, encoding='utf-8') as kv:
                    Builder.load_string(kv.read())

    def back_screen(self, instance, keyboard, keycode, text, modifiers):
        if keyboard in (1001, 27):
            try:
                self.manager.current = self.list_previous_screens.pop()
                if self.manager.current == 'dialogs':
                    self.screen.ids.action_bar.title = 'Сообщения'
            except:
                pass
        return True

    def on_start(self):
        pass
        # self.rect = threading.Thread(target=self.receving,args = ("RecvThread",self.s))
        # self.rect.start()

    def on_stop(self):
        self.theme(self.theme_cls.theme_style)
        self.shutdown = False
        # self.rect.join()
        self.conn.close()
        self.s.close()

    def on_pause(self):
        self.theme(self.theme_cls.theme_style)

    def show_profile(self,*args):
        self.manager.current = 'profile'
        self.screen.ids.action_bar.title = 'Профиль'
        notification.notify(title = 'Новое сообщение',message = 'Привет друг!', app_name = 'Verbose', app_icon = 'data/images/icon.ico')
            
    def show_dialogs(self,*args):
        self.manager.current = 'dialogs'
        self.screen.ids.action_bar.title = 'Сообщения'
        
    def show_corresp(self,username,*args):
        self.manager.current = 'corresp'
        self.screen.ids.action_bar.title = username
        self.list_previous_screens.append('dialogs')
        
    def show_settings(self,*args):
        self.manager.current = 'settings'
        self.screen.ids.action_bar.title = 'Настройки'
        
    def show_license(self,*args):
        self.screen.ids.license.ids.text_license.text = open(path.join(self.directory, 'LICENSE'), encoding='utf-8').read()
        self.manager.current = 'license'
        self.screen.ids.action_bar.title = 'Лицензия MIT'
    
    def show_about(self,*args):
        self.screen.ids.about.ids.label.text = (
                u'[size=40sp][b]Verbose[/b][/size]\n\n'
                u'[b]Версия:[/b] {version}\n'
                u'[b]Лицензия:[/b] MIT\n\n'
                u'[size=20sp][b]Разработчик[/b][/size]\n\n'
                u'[ref=https://github.com/l1n-x]'
                u'[color={link_color}]Роман Саркисян[/color][/ref]\n\n'
                u'[b]Исходный код:[/b] '
                u'[ref=https://github.com/l1n-x/Verbose]'
                u'[color={link_color}]GitHub[/color][/ref]').format(
                version= '0.0.1',
                link_color=get_hex_from_color(self.theme_cls.primary_color)
                )
        self.manager.current = 'about'
        self.screen.ids.action_bar.title = 'О нас'

    def add_message(self, text, side, color):
        self.messages.append({
            'message_id': len(self.messages),
            'text': text,
            'side': side,
            'bg_color': color
        })
    
    def send_message(self, text):
        self.add_message(text, 'right', '#808080')
        self.sending(text)
        self.scroll_bottom()

    def answer(self,text):
        self.add_message(text.decode("utf-8"), 'left', '#4B7F8B')
        self.scroll_bottom()

    def scroll_bottom(self):
        Animation.cancel_all(self.screen.ids.corresp.ids.msg_store, 'scroll_y')
        Animation(scroll_y=0, t='out_quad', d=.5).start(self.screen.ids.corresp.ids.msg_store)
    
    def receving(self,name,sock):
        while not self.shutdown:
            try:
                while True:
                    data, addr = sock.recvfrom(1024)
                    print(data.decode("utf-8"))
                    if data != '':
                        self.answer(data)
            except:
                pass

    def sending(self,text):
        try:
            if text != "":
                self.s.sendto((text).encode("utf-8"),(self.server))
        except:
            pass

def main():
    VerboseApp().run()

if __name__ in ('__main__','__android__'):
    #Window.size = (360,640)
    main()
