#!/bin/python

import sys
import os
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gio

class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Things will go here
        self.box1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.box2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.box3 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.set_child(self.box1)
        self.box1.append(self.box2)
        self.box1.append(self.box3)

        self.set_default_size(600, 250)
        self.set_title("Tidal2D")

        self.header = Gtk.HeaderBar()
        self.set_titlebar(self.header)
        self.open_button = Gtk.Button(label="Open")
        self.header.pack_start(self.open_button)
        self.open_button.connect('clicked', self.show_open_dialog)
        self.open_button.set_icon_name("document-open-symbolic")

        self.open_dialog = Gtk.FileDialog.new()
        self.open_dialog.set_title("Select a Folder")

        menu = Gio.Menu.new()
        self.popover = Gtk.PopoverMenu()
        self.popover.set_menu_model(menu)

        self.hamburger = Gtk.MenuButton()
        self.hamburger.set_popover(self.popover)
        self.hamburger.set_icon_name("open-menu-symbolic")

        self.header.pack_start(self.hamburger)

        GLib.set_application_name("tidal-gtk")

        action = Gio.SimpleAction.new("about", None)
        action.connect("activate", self.show_about)
        self.add_action(action)

        menu.append("About", "win.about")

        self.box2.set_spacing(10)
        self.box2.set_margin_top(10)
        self.box2.set_margin_bottom(10)
        self.box2.set_margin_start(10)
        self.box2.set_margin_end(10)

        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_min_content_height(400)
        self.scroll.set_min_content_width(200)
        self.listbox = Gtk.ListBox()
        self.listbox.connect("row-selected", self.selection_changed)
        self.scroll.set_child(self.listbox)
        self.box2.append(self.scroll)

        self.project_path = ""

    def show_open_dialog(self, button):
        self.open_dialog.select_folder(self, None, self.open_dialog_open_callback)

    def open_dialog_open_callback(self, dialog, result):
        try:
            file = dialog.select_folder_finish(result)
            if file is not None:
                self.project_path = file.get_path()
                self.listbox.remove_all()
                dir_list = os.listdir(file.get_path())
                for item in dir_list:
                    label = Gtk.Label.new(item)
                    row = Gtk.ListBoxRow()
                    row.set_child(label)
                    self.listbox.append(row)
        except GLib.Error as error:
            print(f"Error opening file: {error.message}")

    def show_about(self, action, param):
        self.about = Gtk.AboutDialog()
        self.about.set_transient_for(self)
        self.about.set_modal(self)

        self.about.set_authors(["Sebastien MacDougall-Landry"])
        self.about.set_copyright("Copyright 2023 Sebastien MacDougall-Landry")
        self.about.set_license_type(Gtk.License.GPL_3_0)
        self.about.set_website("https://github.com/EmperorPenguin18")
        self.about.set_website_label("GitHub")
        self.about.set_version("0.1")
        self.about.set_visible(True)

    def selection_changed(self, box, row):
        self.box1.remove(self.box3)
        self.box3 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.box1.append(self.box3)
        filename = self.project_path+os.sep+row.get_child().get_label()
        button = Gtk.Button.new_with_label("Open externally")
        button.connect('clicked', self.open_external, filename)
        name, ext = os.path.splitext(filename)
        if ext == ".bmp" or ext == ".png" or ext == ".jpg":
            image = Gtk.Image.new_from_file(filename)
            self.box3.append(image)
        if ext == ".wav" or ext == ".ogg":
            media = Gtk.MediaFile.new_for_filename(filename)
            media.play()
        if ext == ".lua":
            f = open(filename, "r")
            label = Gtk.Label.new(f.read())
            f.close()
            self.box3.append(label)
        if ext == ".json":
            print('sus')
        else:
            self.box3.append(button)

    def open_external(self, button, param):
        os.system(f"xdg-open {param}")

class MyApp(Gtk.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        self.win = MainWindow(application=app)
        self.win.present()

def main():
    app = MyApp(application_id="com.github.tidal-gtk")
    app.run(sys.argv)

if __name__ == "__main__":
    main()
