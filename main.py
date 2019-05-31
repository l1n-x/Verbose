#!/usr/bin/env python3
#Python Libraries
from os import path, listdir
import socket
from sys import argv
import threading

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

#Android Libraries
# from jnius import autoclass
# from android.runnable import run_on_ui_thread

#Custom Libraries
from libs.uix.baseclass.startscreen import StartScreen

directory = path.split(path.abspath(argv[0]))[0]

# def thread(my_func):
#     '''@thread - Запуск метода в потоке'''
#     def wrapper (*args, **kwargs):
#         my_thread = threading.Thread(target = my_func, args = args, kwargs = kwargs)
#         my_thread.start()
#     return wrapper

class VerboseApp(App):
    theme_cls = ThemeManager()
    theme_cls.primary_palette = 'Blue'
    theme_cls.theme_style = 'Light'
    m_press = get_color_from_hex('#000080')
    messages = ListProperty()
    
    # @run_on_ui_thread
    # def _set_keyboard(self):
    #     python_activity = autoclass('org.kivy.android.PythonActivity').mActivity
    #     window = python_activity.getWindow()
    #     window.setSoftInputMode(16)
    
    def __init__(self, **kwargs):
        self.title = 'Verbose'
        self.icon = 'data/images/icon.png'
        super(VerboseApp, self).__init__(**kwargs)
        Window.bind(on_keyboard=self.events_program)
        Window.soft_input_mode = 'below_target'
        #self.use_kivy_settings = False
        self.list_previous_screens = ['profile']
        self.window = Window
        self.manager = None
        self.md_theme_picker = None
        self.shutdown = False
        self.server = ("185.20.225.163",9090)
        self.host = socket.gethostbyname(socket.gethostname())
        self.port = 0
        self.s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.s.connect(self.server)
        self.s.setblocking(0)
        self.s.sendto(("I'm here!").encode("utf-8"),(self.server))
    
    # def open_settings(self, *largs): #Отключение настроек Kivy
    #     pass

    def build(self):
        self.load_all_kv_files(path.join(self.directory, 'libs', 'uix', 'kv'))
        # self._set_keyboard()
        self.screen = StartScreen()
        self.manager = self.screen.ids.manager
        return self.screen

    def load_all_kv_files(self, directory_kv_files):
        for kv_file in listdir(directory_kv_files):
            kv_file = path.join(directory_kv_files, kv_file)
            if path.isfile(kv_file):
                with open(kv_file, encoding='utf-8') as kv:
                    Builder.load_string(kv.read())

    def events_program(self, instance, keyboard, keycode, text, modifiers):
        '''Вызывается при нажатии кнопки Меню или Back Key на мобильном устройстве.'''

        if keyboard in (1001, 27):
            self.back_screen(event=keyboard)
        return True
    
    def back_screen(self, event=None):
        '''Менеджер экранов. Вызывается при нажатии Back Key и шеврона "Назад" в ToolBar.'''
        if event in (1001, 27):
            try:
                self.manager.current = self.list_previous_screens.pop()
            except:
                self.manager.current = 'profile'

    def on_start(self):
        self.rect = threading.Thread(target=self.receving,args = ("RecvThread",self.s))
        self.rect.start()

    def on_stop(self):
        self.shutdown = False
        self.rect.join()
        self.s.close()

    def show_profile(self,*args):
        self.manager.current = 'profile'
        self.screen.ids.action_bar.title = 'Профиль'
            
    def show_dialogs(self,*args):
        self.manager.current = 'dialogs'
        self.screen.ids.action_bar.title = 'Сообщения'

    def show_corresp(self,username,*args):
        self.manager.current = 'corresp'
        self.screen.ids.action_bar.title = username

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

    def theme_pick(self):
        if not self.md_theme_picker:
            self.md_theme_picker = MDThemePicker()
        self.md_theme_picker.open()

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
    Window.size = (360,640)
    main()
