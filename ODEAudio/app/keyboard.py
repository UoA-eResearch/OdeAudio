from kivy.core.window import Window
from kivy.uix.widget import Widget


class MyKeyboardListener(Widget):

    def __init__(self, **kwargs):
        super(MyKeyboardListener, self).__init__(**kwargs)
        self._keyboard = None
        self.text_actions = {}
        self.code_actions = {}

        self.focus()

    def focus(self):
        self._keyboard = Window.request_keyboard(
            self._keyboard_closed, self, 'text')
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def register(self, action: callable, text=None, keycode=None):
        if text:
            assert not keycode
            self.text_actions[text] = action
        else:
            assert keycode
            self.code_actions[keycode] = action

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        # Don't return true if escape pressed, so that kivy catches key press and exits
        exiting = keycode[1] == 'escape'

        if text in self.text_actions:
            self.text_actions[text]()
            if not exiting:
                return True

        if keycode[0] in self.code_actions:
            self.code_actions[keycode[0]]()
            if not exiting:
                return True

        # If we hit escape, release the keyboard
        if exiting:
            keyboard.release()

        return False
