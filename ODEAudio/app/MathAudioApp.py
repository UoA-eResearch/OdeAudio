from math import inf

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ObjectProperty, StringProperty, ListProperty

from ODEAudio.audio.play_stream import AudioStream
from ODEAudio.odes.equation import dy, extract
from ODEAudio.integrator import Integrator

import numpy as np

from app.keyboard import MyKeyboardListener


@np.vectorize
def range_map(x0, x1, y0, y1, v):
    """Map a value v from one range [x0, x1] to another [y0, y1]"""
    return y0 + (y1 - y0) * (v - x0) / (x1 - x0)


class MathAudioApplet(Widget):
    y_min = NumericProperty(inf)
    y_max = NumericProperty(-inf)
    points = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.I = Integrator(dy, extract, [-.1, -.101, -.102], [1.001, 0.999])
        self.I.prime()
        self.I.start_thread()
        self.sound = AudioStream(self.I.callback)

        self.keyboard = MyKeyboardListener()
        self.keyboard.register(self.pause, keycode=32)
        self.keyboard.register(self.reset, text='r')
        self.keyboard.register(self.exit, keycode=27)
        self.add_widget(self.keyboard)

    cursor = ObjectProperty(None)
    lambda_e = NumericProperty(0)
    lambda_c = NumericProperty(0)

    str_e = StringProperty("")
    str_c = StringProperty("")

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
        self.I.reset([-.1, -.101, -.102], [self.lambda_c, self.lambda_e])

    def exit(self):
        self.sound.close()
        self.I.close()

    def update(self, dt):
        self.lambda_c = float(range_map(0, self.width, 0.9, 1.1, self.cursor.center_x))
        self.lambda_e = float(range_map(0, self.height, 0.9, 1.1, self.cursor.center_y))
        self.str_e = f'{self.lambda_e:.3f}'
        self.str_c = f'{self.lambda_c:.3f}'

        # i = self.I.start_index
        # x = np.asarray(self.I.T[-20000:])
        # if len(x):
        #     xp = range_map(x.min(initial=inf), x.max(initial=0), 0, self.width, x)
        #     y = np.asarray(self.I.Y[-20000:])
        #     self.y_min = float(y.min(initial=self.y_min))
        #     self.y_max = float(y.max(initial=self.y_max))
        #     yp = range_map(self.y_min, self.y_max, self.height, 0, y)
        #
        #     self.points = zip(xp, yp)

    def on_touch_up(self, touch):
        self.I.change_args(self.lambda_e, self.lambda_c)


class Cursor(Widget):
    def on_touch_move(self, touch):
        self.center = (touch.x, touch.y)

    def on_touch_down(self, touch):
        self.center = (touch.x, touch.y)


class MathAudioApp(App):
    def build(self):
        app = MathAudioApplet()
        Clock.schedule_interval(app.update, 1/30)
        return app


if __name__ == '__main__':
    MathAudioApp().run()
