from math import inf

from kivy import Config
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput

from ODEAudio.image.background import get_image
from ODEAudio.utility.lerps import range_map, map_zip, clamp

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
from ODEAudio.odes.julia_solver import JSolver


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
        self.solver = JSolver(np.asarray([-5, -5, -5, -5, -20]),
                              np.asarray([self.cA, self.eA, self.cB, self.eB]))
        self.sound = AudioStream(self.solver.callback)

        # Keyboard listener and triggers
        self.keyboard = MyKeyboardListener()
        self.keyboard.register(self.pause, keycode=32)  # space bar
        self.keyboard.register(self.exit, keycode=27)   # esc
        self.keyboard.register(self.reset, text='n')    # reset variables
        self.keyboard.register(self.set_pars, text='m') # set parameters
        # Nudge variables
        for c in 'qwertasdfg':
            self.keyboard.register(self.nudge, text=c)

        for i in range(10):
            self.keyboard.register(self.set_channel, text=str(i))
        self.add_widget(self.keyboard)
        self.popup = None

        # x/y limits for the left (fixed) panel
        self.LaLim = (.4, 1.6)
        self.LbLim = (0.5, 2)
        # x/y limits for the right (zoomed) panel
        self.RaLim = (.4, 1.6)
        self.RbLim = (0.5, 2)

        self.select_end = (self.width * 0.5, self.height * 0.2)

        bg_image = get_image(self.LaLim, self.LbLim)
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

    def set_pars(self, *args):
        self.sound.stream.stop()
        self.pause_text = "Paused"

        textInput = TextInput(text=', '.join([str(v) for v in self.solver.args]),
                              multiline=False)
        textInput.bind(on_text_validate=self.reset_pars)
        self.popup = Popup(title='Set parameters (cA, eA, cB, eB)', content=textInput, auto_dismiss=False)
        self.popup.open()

    def reset_pars(self, value):
        values = value.text.split(',')
        args = [float(v) for v in values]

        self.popup.dismiss()
        self.popup = None
        self.keyboard.focus()

        self.solver.change_args(*args)

        self.cA = args[0]
        self.eA = args[1]
        self.cB = args[2]
        self.eB = args[3]

        self.str_cA = f'{self.cA:.3f}'
        self.str_cB = f'{self.cB:.3f}'

        self.str_eA = f'{self.eA:.3f}'
        self.str_eB = f'{self.eB:.3f}'

        self.update_guides()

    def nudge(self, text):
        if text == 'q':
            self.solver.nudge([5, 0, 0, 0, 0])
        elif text == 'w':
            self.solver.nudge([0, 5, 0, 0, 0])
        elif text == 'e':
            self.solver.nudge([0, 0, 5, 0, 0])
        elif text == 'r':
            self.solver.nudge([0, 0, 0, 5, 0])
        elif text == 't':
            self.solver.nudge([0, 0, 0, 0, 5])
        elif text == 'a':
            self.solver.nudge([-5, 0, 0, 0, 0])
        elif text == 's':
            self.solver.nudge([0, -5, 0, 0, 0])
        elif text == 'd':
            self.solver.nudge([0, 0, -5, 0, 0])
        elif text == 'f':
            self.solver.nudge([0, 0, 0, -5, 0])
        elif text == 'g':
            self.solver.nudge([0, 0, 0, 0, -5])

    def set_channel(self, str_channel):
        channel = int(str_channel)
        if channel == 0:
            self.solver.set_channel(4, 1)
            self.rChan = 4
        elif channel < 6:
            self.solver.set_channel(channel - 1, 0)
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

    def update_traces(self, force = False):
        if self.solver.update_freq or force:
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
                        range_map(-2, 2, 0, self.height * .2, clamp(-2, 2, y[:, i]))
                    ))

    def update(self, dt):
        self.solver.thread_step()
        self.update_traces()

    def update_guides(self):
        # Guides for cA/cB
        screen_transform = (self.LaLim, (0, self.width / 2), self.LbLim, (0.2 * self.height, self.height))

        self.cCursor = [
            range_map(*self.LaLim, 0, self.width / 2, self.cA),
            range_map(*self.LbLim, 0.2 * self.height, self.height, self.cB)
        ]

        x_cA = np.linspace(*self.LaLim)
        self.cPoints1 = map_zip(x_cA, (self.eA + self.eB) - x_cA, *screen_transform)
        self.cPoints2 = map_zip(x_cA, (self.eA ** 2 * self.eB) / (x_cA ** 2), *screen_transform)
        self.cPoints3 = map_zip(x_cA, (x_cA * self.eA) / self.eB, *screen_transform)

        # Guides for eA/eB
        screen_transform = (self.RaLim, (self.width / 2, self.width), self.RbLim, (0.2 * self.height, self.height))

        self.eCursor = [
            range_map(*self.RaLim, self.width / 2, self.width, self.cA),
            range_map(*self.RbLim, 0.2 * self.height, self.height, self.cB)
        ]

        x_cA = np.linspace(*self.RaLim)
        self.ePoints1 = map_zip(x_cA, (self.eA + self.eB) - x_cA, *screen_transform)
        self.ePoints2 = map_zip(x_cA, (self.eA ** 2 * self.eB) / (x_cA ** 2), *screen_transform)
        self.ePoints3 = map_zip(x_cA, (x_cA * self.eA) / self.eB, *screen_transform)

    select_start = ListProperty([0, 0])
    select_active = BooleanProperty(False)
    select_end = ListProperty([0, 0])

    def on_touch_down(self, touch):
        # Start drag if in left pane
        if touch.x < self.width * 0.5 and touch.y > self.height * 0.2:
            self.select_active = True
            self.select_start = touch.pos

    def on_touch_move(self, touch):
        if (
                touch.x < self.width * 0.5
                and touch.y > self.height * 0.2
                and self.select_active):
            self.select_end = touch.pos

    def on_touch_up(self, touch):
        # End drag if in left pane
        if touch.x < self.width * 0.5 and touch.y > self.height * 0.2:
            self.select_active = False
            self.select_end = touch.pos

            # Update right side limits based on selection
            self.RaLim = tuple(sorted(range_map(0, self.width * .5, *self.LaLim,
                                                (self.select_start[0], self.select_end[0]))))
            self.RbLim = tuple(sorted(range_map(0.2 * self.height, self.height, *self.LbLim,
                                                (self.select_end[1], self.select_start[1]))))
            print(self.RaLim)
            print(self.RbLim)

        # cA eA cB eB
        if touch.x >= self.width * 0.5 and touch.y > self.height * 0.2:
            self.cA = float(range_map(self.width * .5, self.width, *self.RaLim, touch.x))
            self.cB = float(range_map(0.2 * self.height, self.height, *self.RbLim, touch.y))

        self.str_cA = f'{self.cA:.3f}'
        self.str_cB = f'{self.cB:.3f}'

        self.str_eA = f'{self.eA:.3f}'
        self.str_eB = f'{self.eB:.3f}'

        self.update_guides()

        self.solver.change_args(self.cA, self.eA, self.cB, self.eB)

    def on_resize(self, *args):
        self.update_traces(force=True)
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
        Clock.schedule_interval(app.update, 1 / 30)
        app.update_guides()
        return app


if __name__ == '__main__':
    MathAudioApp().run()
