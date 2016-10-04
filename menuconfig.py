import os
import sys
import curses
from curses import panel
import pprint

try:
    import kconfiglib
except:
    sys.path.append("./Kconfiglib")
    import kconfiglib

class Symbol(object):

    def __init__(self, screen, item):
        self.screen = screen
        self.window = screen.subwin(0,0)
        self.item = item
        self.panel = panel.new_panel(self.window)
        self.panel.hide()
        panel.update_panels()

    def prompt(self):
        value = self.item.get_user_value()
        if self.item.get_type() == kconfiglib.BOOL:
            value_str = "[*]" if value == "y" else "[ ]"
        else:
            value_str = "(%s)" % value
        msg = "%s %s" % (value_str, self.item.get_prompts()[0])
        return msg

    def edit(self):
        if self.item.get_type() == kconfiglib.BOOL:
            if self.item.get_user_value() == "y":
                self.item.set_user_value("n")
            else:
                self.item.set_user_value("y")
        else:
            self.panel.top()
            self.panel.show()
            self.window.clear()
            self.window.addstr(0,1, "Enter value:",curses.A_NORMAL)
            curses.echo()
            value = self.window.getstr(1,1,128)
            curses.noecho()
            self.item.set_user_value(value)
            self.panel.hide()

# From http://stackoverflow.com/a/14205494
class Menu(object):

    def __init__(self, stdscreen, title, items):
        self.window = stdscreen.subwin(0,0)
        self.window.keypad(1)
        self.panel = panel.new_panel(self.window)
        self.panel.hide()
        panel.update_panels()

        self.position = 0
        self.title = title
        self.items = []
        for item in items:
            if item.is_symbol():
                symbol = Symbol(stdscreen, item)
                self.items.append((symbol,symbol.edit))
            if item.is_menu():
                submenu = Menu(stdscreen,item.get_title(),item.get_items())
                self.items.append((submenu,submenu.display))

    def navigate(self, n):
        self.position += n
        if self.position < 0:
            self.position = 0
        elif self.position >= len(self.items):
            self.position = len(self.items)-1

    def display(self):
        self.panel.top()
        self.panel.show()
        self.window.clear()

        while True:
            self.window.refresh()
            curses.doupdate()
            for index,item in enumerate(self.items):
                if index == self.position:
                    mode = curses.A_REVERSE
                else:
                    mode = curses.A_NORMAL

                self.window.clrtoeol()
                self.window.addstr(1+index,1, item[0].prompt(), mode)

            key = self.window.getch()

            if key in [curses.KEY_ENTER, ord('\n')]:
                self.items[self.position][1]()

            elif key == curses.KEY_UP:
                self.navigate(-1)

            elif key == curses.KEY_DOWN:
                self.navigate(1)

            elif key == curses.KEY_LEFT:
                break

        self.window.clear()
        self.panel.hide()
        panel.update_panels()
        curses.doupdate()

    def prompt(self):
        msg = '%s --->' % self.title
        return msg

class MenuConfig(object):
    def __init__(self, screen, cfgfile):
        self.screen = screen
        # Load the root Kconfig (this will load all sourced files also)                           
        self.conf = kconfiglib.Config(cfgfile)
        # Also load any existing generated configuration
        if os.path.exists(".config"):
            self.conf.load_config(".config")
        # Initialize curses screen
        curses.curs_set(0)
        # Create main menu
        main_menu = Menu(screen,"Top",self.conf.get_top_level_items())
        main_menu.display()
        self.conf.write_config(".config")

def main(stdscr):
    if len(sys.argv) <= 1:
        # Look for a root Kconfig in the current directory
        cfgfile = os.path.abspath('.').replace('\\', '/') + "/" + "Kconfig"
    else:
        # Use the root Kconfig is passed on the command line
        cfgfile = os.path.abspath('.').replace('\\', '/') + "/" + sys.argv[1]
    # Create main window
    app = MenuConfig(stdscr,cfgfile)

if __name__ == "__main__":
        
    curses.wrapper(main)
