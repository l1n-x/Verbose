#!/usr/bin/env python3
#Python Libraries
import threading
import sqlite3
import socket
import json
import rsa
from hashlib import sha512
from os import path, listdir
from sys import argv
from datetime import datetime
#Kivy Libraries
import kivy
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import Metrics
from kivy.properties import ListProperty
from kivy.utils import get_hex_from_color
from kivymd.theming import ThemeManager
from kivymd.toolbar import MDToolbar
#Custom Libraries
from libs.uix.baseclass.startscreen import StartScreen

directory = path.split(path.abspath(argv[0]))[0]
Window.softinput_mode = 'below_target' #Сдвигаем экран до текстового поля

def thread(my_func): #Декоратор потока
    '''@thread - Запуск метода в потоке'''
    def wrapper (*args, **kwargs):
        my_thread = threading.Thread(target = my_func, args = args, kwargs = kwargs)
        my_thread.start()
    return wrapper

class Server:
    pass
    # def server_start(self,host,port):
    #     self.s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    #     self.s.bind((host,port))
    #     self.quit = False
    #     self.clients = []
    #     self.listening()
    
    # @thread
    # def listening(self):
    #     while not self.quit:
    #         try:
    #             data, addr = self.s.recvfrom(1024)
    #             if addr not in self.clients:
    #                 self.clients.append(addr)
    #             print(data.decode("utf-8"))
    #             for client in self.clients:
    #                 if addr != client:
    #                     self.s.sendto(data,client)
    #         except:
    #             self.quit = True
    #     self.s.close()

class VerboseApp(App):
    today = datetime.strftime(datetime.now(), "[%H:%M] %d %m %Y")
    db = sqlite3.connect(path.join(directory, 'data/user_data'))
    cur = db.cursor()
    cur.execute('SELECT Theme FROM Session')    
    theme_cls = ThemeManager()
    theme_cls.primary_palette = 'Blue'
    theme_cls.theme_style = cur.fetchone()[0]
    server = ("185.20.225.163",9090) #address/port  signal server
    messages = ListProperty()

    def __init__(self, **kwargs):
        self.title = 'Verbose'
        self.icon = 'data/images/icon.ico'
        super(VerboseApp, self).__init__(**kwargs)
        Window.bind(on_keyboard=self.back_screen)
        self.avatar = 'data/images/ava_high.png'
        self.list_previous_screens = []
        self.manager = None
        self.shutdown = False
        self.msg_count = 0
        self.username = ''
        self.user_info = {'status':'','tel':'','location':'','born':'','about':''}

    def on_start(self):
        self.cur.execute("SELECT Logged, tel FROM Session")
        logged,self.uPhone= self.cur.fetchone()
        if logged == 1:
            self.userinfo(self.uPhone)
            self.show_profile()
        self.sock_up()        
        self.receving()
        
    def on_stop(self):
        self.shutdown = True
        self.db.close()
        self.s.sendto(("*Status#:Offline").encode("utf-8"),(self.server))
        self.s.close()
    
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
    
    def hash(self,tel,pwd):
        pwd = pwd + tel[:1:-1]
        pwd = sha512(pwd.encode("utf-8"))
        pwd = pwd.hexdigest()
        return pwd
    
    def sock_up(self):
        self.s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.s.connect(self.server)
        self.s.setblocking(0)
        self.s.sendto(("*Status#:Online").encode("utf-8"),(self.server))

    def dyn_text(self, text):
        text = text.strip(' ')
        msg_width = round(Window.width / (20*Metrics.density*Metrics.fontscale))
        if msg_width < len(text):
            for x in range(len(text)):
                if x%msg_width == 0 and x>0:
                    if text[x] != ' ':
                        temp = text.rfind(' ',0,x)
                        if temp == -1:
                            text = text[:x] + '\n' + text[x+1:]
                        else:
                            text = text[:temp] + '\n' + text[temp+1:]
                    else:
                        text = text[:x] + '\n' + text[x+1:]
        return text

    def history(self):
        del_history = []
        for row in self.cur.execute("SELECT * FROM Messages WHERE UserFrom = ? OR UserTo = ?",(self.uPhone,self.uPhone)):
            db_date = row[4].split(' ')
            isdate = self.today.split(' ')
            year = 0
            if db_date[-1] != isdate[-1]:
                year += 12
            if int(db_date[-2])+6 <= int(isdate[-2]) + year:
                del_history.append(row[0])
            else:
                self.messages.append({
                'message_id': len(self.messages),
                'text': self.dyn_text(row[1]),
                'side': row[2],
                'bg_color': row[3]
                })
                self.msg_count = row[0]
        for x in del_history:
            self.cur.execute("DELETE FROM Messages WHERE ID = ?",(x,))
        self.db.commit()
    
    def sync_history(self):
        for x in range(self.msg_count,len(self.messages)):
            self.cur.execute("INSERT INTO Messages(Message, Side, Color, MessageDate) VALUES (?,?,?,?)",\
                (self.messages[x]['text'].replace('\n',' '),self.messages[x]['side'],self.messages[x]['bg_color'],self.today))
        self.db.commit()
        self.msg_count = len(self.messages)

    def theme(self,style):
        if style == 'Dark':
            self.cur.execute("UPDATE Session SET Theme = 'Dark'")
        elif style == 'Light':
            self.cur.execute("UPDATE Session SET Theme = 'Light'")
        self.db.commit()

    def userinfo(self,tel):
        self.cur.execute("SELECT * FROM Users WHERE tel = ?",(tel,))
        CurrUser = self.cur.fetchone()
        self.cur.execute("UPDATE Userinfo SET tel=?, first_name=?, last_name=?, location=?, born=?, about=?", (CurrUser[0],CurrUser[3],CurrUser[4],CurrUser[5],CurrUser[6],CurrUser[7]))
        self.cur.execute("SELECT * FROM Userinfo")
        profile = self.cur.fetchone()
        self.username = profile[0] + ' ' + profile[1]
        self.screen.ids.profile.ids.born.text = 'Дата рождения: ' + str(profile[2])
        self.screen.ids.profile.ids.location.text = 'Страна/Город: ' + str(profile[3])
        self.screen.ids.profile.ids.phone.text = 'Телефон: ' + str(profile[4])
        self.screen.ids.profile.ids.about.text = 'О себе: ' + str(profile[5])

    def back_screen(self, instance, keyboard, keycode, text, modifiers):
        '''1000 - "Назад", 1001 - Меню на андроид, 27 - "Esc" на компьютере'''
        if keyboard in (1001, 27):
            try:
                self.manager.current = self.list_previous_screens.pop()
                if self.manager.current == 'dialogs':
                    self.screen.ids.action_bar.title = 'Сообщения'
            except:
                pass
        return True

    def keys(self):
        self.cur.execute("SELECT pubkey, privkey FROM Session")
        keys = self.cur.fetchone()
        if keys[0] == None or keys[1] == None:
            (self.pub_key, self.priv_key) = rsa.newkeys(512)
            self.cur.execute("UPDATE Session SET pubkey = ?, privkey = ?", (str(self.pub_key),str(self.priv_key)))
            self.db.commit()
        else:
            self.pub_key, self.priv_key = keys

    def auth(self,tel,pwd):
        pwd = self.hash(tel,pwd)        
        self.cur.execute('SELECT * FROM users WHERE tel=? AND password=?',(str(tel),str(pwd)))
        result = self.cur.fetchall()
        if result:
            self.cur.execute("UPDATE Session SET Logged = 1, tel = ?, password = ?",(str(tel),str(pwd)))
            self.db.commit()
            self.uPhone = tel
            self.keys()
            self.history()
            self.userinfo(tel)
            self.show_profile()
        else:
            self.screen.ids.login.ids.error_data.text = 'Неверный логин и(или) пароль.'

    def registration(self,fname,lname,born,country,city,tel,password,about):
        if '' not in (fname,lname,born,country,city,tel,password,about):
            if '+7' not in tel:
                self.screen.ids.registration.ids.error_data.text = 'Телефон введён неверно'
            else:
                if len(born) != 10:
                    self.screen.ids.registration.ids.error_data.text = 'Дата рождения введена неверно'
                else:
                    location = country + ',' + city
                    self.keys()
                    sql = ("INSERT INTO Users(tel,password,pubkey,first_name,last_name,location,born,about) VALUES (?,?,?,?,?,?,?,?)")
                    self.cur.execute(sql,(tel,(self.hash(tel,password)),self.pub_key,fname,lname,location,born,about))
                    self.db.commit()
                    self.show_login()
        else:
            self.screen.ids.registration.ids.error_data.text = 'Проверьте правильность заполнения полей'

    def logout(self):
        self.cur.execute("UPDATE Session SET Logged = 0, tel = 'Не заполнено', password = 'Не заполнено', pubkey = ?, privkey = ?",(None,None))
        self.db.commit()
        self.msg_count = 0
        self.screen.ids.corresp.ids.msg_store.clear_widgets()
        self.screen.ids.login.ids.field_phone.text = ''
        self.screen.ids.login.ids.field_password.text = ''
        self.show_login()
    
    def show_login(self,*args):
        self.manager.current = 'login'
        self.screen.ids.action_bar.title = 'Verbose'

    def show_registration(self,*args):
        self.manager.current = 'registration'
        self.screen.ids.action_bar.title = 'Регистрация'

    def show_profile(self,*args):
        self.manager.current = 'profile'
        self.screen.ids.action_bar.title = self.username
        self.list_previous_screens = ['profile']
            
    def show_dialogs(self,*args):
        self.manager.current = 'dialogs'
        self.screen.ids.action_bar.title = 'Сообщения'
          
    def show_corresp(self,username,*args):
        self.manager.current = 'corresp'
        self.screen.ids.action_bar.title = username
        self.list_previous_screens.append('dialogs')
        self.scroll_bottom()
        
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

    def scroll_bottom(self):
        Animation.cancel_all(self.screen.ids.corresp.ids.msg_store, 'scroll_y')
        Animation(scroll_y=0, t='out_quad', d=.5).start(self.screen.ids.corresp.ids.msg_store)

    def add_message(self, text, side, color):
        self.messages.append({
            'message_id': len(self.messages),
            'text': self.dyn_text(text),
            'side': side,
            'bg_color': color
        })
        self.sync_history()
    
    def send_message(self, text):
        self.add_message(text, 'right', '#808080')
        self.scroll_bottom()
        try:
            if text != "":
                self.s.sendto(text.encode("utf-8"),(self.server))
        except:
            pass
        
    def answer(self,text):
        self.add_message(text.decode("utf-8"), 'left', '#4B7F8B')
        self.scroll_bottom()
    
    @thread
    def receving(self):
        while not self.shutdown:
            try:
                while True:
                    data, addr = self.s.recvfrom(1024)
                    if data != '':
                        self.answer(data)
                    elif data != "*Status#:Online":
                        pass
                    elif data != "*Status#:Offline":
                        pass
            except:
                pass
    
def main():
    VerboseApp().run()

if __name__ == '__main__':
    # Window.size = (360,640)
    main()