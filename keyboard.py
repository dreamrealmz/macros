from pynput.keyboard import Key, Listener, Controller
from pynput.keyboard._win32 import KeyCode  # noqa
from buttons import key_class_buttons, keycode_class_buttons, button_comparison


class KeyboardListener:
    def __init__(self, binding_key=''):

        self.key_class_buttons = key_class_buttons
        self.keycode_class_buttons = keycode_class_buttons
        self.button_comparison = button_comparison
        self.macros_mapping = {}
        self.keyboard = Controller()
        self.written_script = ''
        binding_key = self.button_comparison.get(binding_key)
        if binding_key:
            self.binding_key = [binding_key.lower(), binding_key.upper(), binding_key.capitalize()] if isinstance(
                binding_key, str) else [binding_key]
        else:
            self.binding_key = None

    def write_press(self, key):
        if isinstance(key, Key):
            char = key._name_
        elif isinstance(key, KeyCode):
            char = key.char
        else:
            char = key
        command = f'self.keyboard.press({self.button_comparison.get(char)});'
        release_command = f'self.keyboard.press({self.button_comparison.get(char)});'
        button = self.button_comparison.get(char)
        buttons = [button.lower(), button.upper(), button.capitalize()] if isinstance(button, str) else [button]
        if key != Key.f8 and buttons != self.binding_key and (
                command not in self.written_script
                or self.written_script.count(command) <= self.written_script.count(release_command)
        ):
            self.written_script += f'self.keyboard.press({button});time.sleep(0.1);'

    def write_release(self, key):
        if isinstance(key, Key):
            char = key._name_
        elif isinstance(key, KeyCode):
            char = key.char
        else:
            char = key
        button = self.button_comparison.get(char)
        buttons = [button.lower(), button.upper(), button.capitalize()] if isinstance(button, str) else [button]
        if key != Key.f8 and buttons != self.binding_key:
            self.written_script += f'self.keyboard.release({button});time.sleep(0.1);'
        return key != Key.f8

    def write_script(self):
        with Listener(
                on_press=self.write_press,
                on_release=self.write_release) as listener:
            listener.join()
        return self.written_script.replace('self.keyboard.release(Key.f8);', '')
