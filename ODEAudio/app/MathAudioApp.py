from math import inf

from kivy import Config
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput

from image.background import get_image
from utility.lerps import range_map, map_zip

Config.set('graphics', 'width', 1200)
Config.set('graphics', 'height', 600)

from kivy.core.window import Window
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ObjectProperty, StringProperty, ListProperty, BooleanProperty

import numpy as np

from ODEAudio.audio.play_stream import AudioStream
from ODEAudio.app.keyboard import MyKeyboardListener
from odes.julia_solver import JSolver


class MathAudioApplet(Widget):
    y_min = NumericProperty(inf)
    y_max = NumericProperty(-inf)

    points0 = ListProperty([])
    points1 = ListProperty([])
    points2 = ListProperty([])
    points3 = ListProperty([])
    points4 = ListProperty([])

    cCursor = ListProperty([0, 0])
    eCursor = ListProperty([0, 0])

    cPoints1 = ListProperty([])
    cPoints2 = ListProperty([])
    cPoints3 = ListProperty([])

    ePoints1 = ListProperty([])
    ePoints2 = ListProperty([])
    ePoints3 = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.solver = JSolver(np.asarray([-4, -5, -5, -5, -5]),
                              np.asarray([self.cA, self.eA, self.cB, self.eB]))
        self.sound = AudioStream(self.solver.callback)

        self.keyboard = MyKeyboardListener()
        self.keyboard.register(self.pause, keycode=32)
        self.keyboard.register(self.reset, text='r')
        self.keyboard.register(self.exit, keycode=27)
        for i in range(10):
            self.keyboard.register(self.set_channel, text=str(i))
        self.add_widget(self.keyboard)
        self.popup = None

        self.aLim = (.4, 1.6)
        self.bLim = (0.5, 2)

        bg_image = get_image(self.aLim, self.bLim)
        bg_image.save('bg_left.png')

        self.update_guides()

    cursor = ObjectProperty(None)
    cA = NumericProperty(0.8)
    cB = NumericProperty(1.255)
    eA = NumericProperty(1.0)
    eB = NumericProperty(0.8)

    lChan = NumericProperty(0)
    rChan = NumericProperty(1)

    str_cA = StringProperty("")
    str_cB = StringProperty("")
    str_eA = StringProperty("")
    str_eB = StringProperty("")

    pause_text = StringProperty("Paused")

    def pause(self, *args):
        self.sound.pause()
        if self.sound.stream.stopped:
            self.pause_text = "Paused"
        else:
            self.pause_text = ""

    def reset(self, *args):
        self.sound.stream.stop()
        self.pause_text = "Paused"

        textInput = TextInput(text=', '.join([str(v) for v in self.solver.y_init]),
                              multiline=False)
        textInput.bind(on_text_validate=self.reset_solver)
        self.popup = Popup(title='Set y init', content=textInput, auto_dismiss=False)
        self.popup.open()

    def reset_solver(self, value):
        values = value.text.split(',')
        y_init = np.asarray([float(v) for v in values])

        self.popup.dismiss()
        self.popup = None
        self.keyboard.focus()

        self.solver.reset(y_init)

    def set_channel(self, str_channel):
        channel = int(str_channel)
        if channel == 0:
            self.solver.set_channel(4, 1)
            self.rChan = 4
        elif channel < 6:
            self.solver.set_channel(channel-1, 0)
            self.lChan = channel - 1
        else:
            self.solver.set_channel(channel - 6, 1)
            self.rChan = channel - 6

    def exit(self):
        self.sound.close()
        self.solver.close()

    def set_points(self, i, val):
        if i == 0:
            self.points0 = val
        elif i == 1:
            self.points1 = val
        elif i == 2:
            self.points2 = val
        elif i == 3:
            self.points3 = val
        elif i == 4:
            self.points4 = val

    def update(self, dt):
        self.solver.thread_step()

        if self.solver.update_freq:
            new_points = self.solver.get_trace()
            if new_points is not None:
                x, y = new_points

                for i, x0, x1 in zip(
                    range(5),
                    np.arange(0, 1.0, .2) * self.width,
                    np.arange(.2, 1.2, .2) * self.width
                ):
                    self.set_points(i, zip(
                        range_map(0, 1, x0, x1, x),
                        range_map(0, 1, 0, self.height * .2, y[:, i])
                    ))

    def update_guides(self):
        # Guides for cA/cB
        screen_transform = (self.aLim, (0, self.width/2), self.bLim, (0.2 * self.height, self.height))

        self.cCursor = [
            range_map(*self.aLim, 0, self.width / 2, self.cA),
            range_map(*self.bLim, 0.2 * self.height, self.height, self.cB)
        ]

        x_cA = np.linspace(*self.aLim)
        self.cPoints1 = map_zip(x_cA, (self.eA + self.eB) - x_cA, *screen_transform)
        self.cPoints2 = map_zip(x_cA, (self.eA ** 2 * self.eB) / (x_cA ** 2), *screen_transform)
        self.cPoints3 = map_zip(x_cA, (x_cA * self.eA) / self.eB, *screen_transform)

        # Guides for eA/eB
        screen_transform = (self.aLim, (self.width / 2, self.width), self.bLim, (0.2 * self.height, self.height))

        self.eCursor = [
            range_map(*self.aLim, self.width / 2, self.width, self.eA),
            range_map(*self.bLim, 0.2 * self.height, self.height, self.eB)
        ]

        x_eA = np.linspace(*self.aLim)
        self.ePoints1 = map_zip(x_eA, (self.cA + self.cB) - x_eA, *screen_transform)
        self.ePoints2 = map_zip(x_eA, (self.cA ** 2 * self.cB) / (x_eA ** 2), *screen_transform)
        self.ePoints3 = map_zip(x_eA, (x_eA * self.cA) / self.cB, *screen_transform)

    def on_touch_up(self, touch):
        # cA eA cB eB
        if self.cursor.center_x < self.width * 0.5:
            self.cA = float(range_map(0, self.width * .5, *self.aLim, self.cursor.center_x))
            self.cB = float(range_map(0.2 * self.height, self.height, *self.bLim, self.cursor.center_y))
        else:
            self.eA = float(range_map(self.width * .5, self.width, *self.aLim, self.cursor.center_x))
            self.eB = float(range_map(0.2 * self.height, self.height, *self.bLim, self.cursor.center_y))

        self.str_cA = f'{self.cA:.3f}'
        self.str_cB = f'{self.cB:.3f}'

        self.str_eA = f'{self.eA:.3f}'
        self.str_eB = f'{self.eB:.3f}'

        self.update_guides()

        self.solver.change_args(self.cA, self.eA, self.cB, self.eB)

    def on_resize(self, *args):
        self.update_guides()


class Cursor(Widget):
    def on_touch_move(self, touch):
        self.center = (touch.x, touch.y)

    def on_touch_down(self, touch):
        self.center = (touch.x, touch.y)


class MathAudioApp(App):
    def build(self):
        app = MathAudioApplet()
        Window.bind(size=app.on_resize)
        Clock.schedule_interval(app.update, 1/30)
        return app


if __name__ == '__main__':
    MathAudioApp().run()
