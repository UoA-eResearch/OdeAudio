from math import inf

from kivy import Config
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput

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


@np.vectorize
def range_map(x0, x1, y0, y1, v):
    """Map a value v from one range [x0, x1] to another [y0, y1]"""
    return y0 + (y1 - y0) * (v - x0) / (x1 - x0)


def map_zip(x, y, x_from, x_to, y_from, y_to):
    return zip(
        range_map(*x_from, *x_to, x),
        range_map(*y_from, *y_to, y)
    )


class MathAudioApplet(Widget):
    y_min = NumericProperty(inf)
    y_max = NumericProperty(-inf)
    points = ListProperty([])

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
                              np.asarray([self.cA, self.eB, self.cB, self.eA]))
        self.sound = AudioStream(self.solver.callback)

        self.keyboard = MyKeyboardListener()
        self.keyboard.register(self.pause, keycode=32)
        self.keyboard.register(self.reset, text='r')
        self.keyboard.register(self.exit, keycode=27)
        self.keyboard.register(self.toggle_plot, text='p')
        self.add_widget(self.keyboard)
        self.popup = None

        self.cLim = (0.6, 1.4)
        self.eLim = (0.6, 1.4)

        self.update_guides()

    cursor = ObjectProperty(None)
    cA = NumericProperty(1.0)
    cB = NumericProperty(1.0)
    eA = NumericProperty(1.0)
    eB = NumericProperty(0.8)

    str_cA = StringProperty("")
    str_cB = StringProperty("")
    str_eA = StringProperty("")
    str_eB = StringProperty("")

    pause_text = StringProperty("Paused")

    def pause(self):
        self.sound.pause()
        if self.sound.stream.stopped:
            self.pause_text = "Paused"
        else:
            self.pause_text = ""

    def reset(self):
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


    show_plot = BooleanProperty(False)

    def toggle_plot(self):
        self.show_plot = not self.show_plot

    def exit(self):
        self.sound.close()
        self.solver.close()

    def update(self, dt):

        self.solver.thread_step()

        # Plot ODE output in the background
        # if self.show_plot:
        #     i = self.solver.start_index
        #     x = np.asarray(self.solver.T[-20000:])
        #     if len(x):
        #         xp = range_map(x.min(initial=inf), x.max(initial=0), 0, self.width, x)
        #         y = np.asarray(self.solver.Y[-20000:])
        #         self.y_min = float(y.min(initial=self.y_min))
        #         self.y_max = float(y.max(initial=self.y_max))
        #         yp = range_map(self.y_min, self.y_max, self.height, 0, y)
        #
        #         self.points = zip(xp, yp)

    def update_guides(self):
        # Guides for cA/cB
        screen_transform = (self.cLim, (0, self.width/2), self.cLim, (0, self.height))

        self.cCursor = [
            range_map(*self.cLim, 0, self.width/2, self.cB),
            range_map(*self.cLim, 0, self.height, self.cA)
        ]

        x_cA = np.linspace(*self.cLim)
        self.cPoints1 = map_zip(x_cA, (self.eA + self.eB) - x_cA, *screen_transform)
        self.cPoints2 = map_zip(x_cA, (self.eA ** 2 * self.eB) / (x_cA ** 2), *screen_transform)
        self.cPoints3 = map_zip(x_cA, (x_cA * self.eA) / self.eB, *screen_transform)

        # Guides for eA/eB
        screen_transform = (self.eLim, (self.width / 2, self.width), self.eLim, (0, self.height))

        self.eCursor = [
            range_map(*self.eLim, self.width/2, self.width, self.eB),
            range_map(*self.eLim, 0, self.height, self.eA)
        ]

        x_eA = np.linspace(*self.eLim)
        self.ePoints1 = map_zip(x_eA, (self.cA + self.cB) - x_eA, *screen_transform)
        self.ePoints2 = map_zip(x_eA, (self.cA ** 2 * self.cB) / (x_eA ** 2), *screen_transform)
        self.ePoints3 = map_zip(x_eA, (x_eA * self.cA) / self.cB, *screen_transform)

    def on_touch_up(self, touch):
        # cA eA cB eB
        if self.cursor.center_x < self.width * 0.5:
            self.cB = float(range_map(0, self.width * .5, *self.cLim, self.cursor.center_x))
            self.cA = float(range_map(0, self.height, *self.cLim, self.cursor.center_y))
        else:
            self.eB = float(range_map(self.width * .5, self.width, *self.cLim, self.cursor.center_x))
            self.eA = float(range_map(0, self.height, *self.cLim, self.cursor.center_y))

        self.str_cA = f'{self.cA:.3f}'
        self.str_cB = f'{self.cB:.3f}'

        self.str_eA = f'{self.eA:.3f}'
        self.str_eB = f'{self.eB:.3f}'

        self.update_guides()

        self.solver.change_args(self.cA, self.eB, self.cB, self.eA)

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
