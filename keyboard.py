from pynput.keyboard import Key, Listener, Controller
from pynput.keyboard._win32 import KeyCode  # noqa
from multiprocessing import Process


class KeyboardListener:
    def __init__(self, binding_key='', keyboard_mapping=None):

        self.key_class_buttons = {
            'esc': 'Key.esc', 'f1': 'Key.f1', 'f2': 'Key.f2', 'f3': 'Key.f3', 'f4': 'Key.f4', 'f5': 'Key.f5',
            'f6': 'Key.f6', 'f7': 'Key.f7', 'f8': 'Key.f8', 'f9': 'Key.f9', 'f10': 'Key.f10', 'f11': 'Key.f11',
            'f12': 'Key.f12', 'backspace': 'Key.backspace', 'tab': 'Key.tab', 'caps_lock': 'Key.caps_lock',
            'enter': 'Key.enter', 'shift': 'Key.shift', 'shift_r': 'Key.shift_r', 'ctrl_l': 'Key.ctrl_l',
            'cmd': 'Key.cmd', 'alt_l': 'Key.alt_l', 'space': 'Key.space', 'alt_gr': 'Key.alt_gr', 'cmd_r': 'Key.cmd_r',
            'ctrl_r': 'Key.ctrl_r',
        }
        self.keycode_class_buttons = {
            '`': '"`"', '1': '"1"', '2': '"2"', '3': '"3"', '4': '"4"', '5': '"5"', '6': '"6"', '7': '"7"', '8': '"8"',
            '9': '"9"', '0': '"0"', '-': '"-"', '=': '"="', 'Q': '"Q"', 'q': '"q"', 'W': '"W"', 'w': '"w"', 'E': '"E"',
            'e': '"e"', 'R': '"R"', 'r': '"r"', 'T': '"T"', 't': '"t"', 'Y': '"Y"', 'y': '"y"', 'U': '"U"', 'u': '"u"',
            'I': '"I"', 'i': '"i"', 'O': '"O"', 'o': '"o"', 'P': '"P"', 'p': '"p"', '[': '"["', ']': '"]"',
            '\\': '"\\"', 'A': '"A"', 'a': '"a"', 'S': '"S"', 's': '"s"', 'D': '"D"', 'd': '"d"', 'F': '"F"',
            'f': '"f"', 'G': '"G"', 'g': '"g"', 'H': '"H"', 'h': '"h"', 'J': '"J"', 'j': '"j"', 'K': '"K"', 'k': '"k"',
            'L': '"L"', 'l': '"l"', ';': '";"', "'": "'", 'Z': '"Z"', 'z': '"z"', 'X': '"X"', 'x': '"x"', 'C': '"C"',
            'c': '"c"', 'V': '"V"', 'v': '"v"', 'B': '"B"', 'b': '"b"', 'N': '"N"', 'n': '"n"', 'M': '"M"', 'm': '"m"',
            ',': '","', '.': '"."', '/': '"/"', '!': '"1"', '@': '"2"', '#': '"3"', '$': '"4"', '%': '"5"', '^': '"6"',
            '&': '"7"', '*': '"8"', '(': '"9"', ')': '"0"', '_': '"-"', '+': '"="',
        }
        self.button_comparison = self.key_class_buttons | self.keycode_class_buttons
        self.keyboard_mapping = keyboard_mapping
        self.macros_mapping = {}
        self.keyboard = Controller()
        self.written_script = ''
        binding_key = self.button_comparison.get(binding_key)
        if binding_key:
            self.binding_key = [binding_key.lower(), binding_key.upper(), binding_key.capitalize()] if isinstance(
                binding_key, str) else [binding_key]
        else:
            self.binding_key = None

    def execute_script(self, script):
        try:
            exec(script)
        except Exception as exc:
            pass

    def on_press(self, key):
        if isinstance(key, Key):
            char = key._name_
        elif isinstance(key, KeyCode):
            char = key.char
        else:
            char = key
        Process(target=self.execute_script(self.macros_mapping.get(char))).start()  # noqa

    def on_release(self, key):
        return key != Key.f8

    def listen_keyboard(self):
        for item in self.keyboard_mapping:
            self.macros_mapping[item.text()] = item.script
            self.macros_mapping[item.text().lower()] = item.script
            self.macros_mapping[item.text().upper()] = item.script

        with Listener(
                on_press=self.on_press,
                on_release=self.on_release) as listener:
            listener.join()

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
            self.written_script += f'self.keyboard.press({button});'

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
            self.written_script += f'self.keyboard.release({button});'
        return key != Key.f8

    def write_script(self):
        with Listener(
                on_press=self.write_press,
                on_release=self.write_release) as listener:
            listener.join()
        return self.written_script.replace('self.keyboard.release(Key.f8);', '')
