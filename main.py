from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty
from kivy.core.window import Window
from kivy.config import Config

Config.set('kivy','keyboard_mode','systemanddock')
#360x640 - Комп, 1080x1920 - Смарт
hello_world = 1
Window.size = (1080,1920)

class Container(GridLayout):
    texin = ObjectProperty()
    lain = ObjectProperty()

    def change_text(self):
        self.lain.text = self.texin.text


class MyApp(App):
    def build(self):
        
        return Container()

if __name__ == '__main__':
    MyApp().run()
