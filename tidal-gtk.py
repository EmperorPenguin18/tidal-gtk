#!/bin/python

import sys
import os
import json
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gio
import git
import tarfile

def bin2header(data, var_name='var'):
    out = []
    out.append('unsigned char {var_name}[] = {{'.format(var_name=var_name))
    l = [ data[i:i+12] for i in range(0, len(data), 12) ]
    for i, x in enumerate(l):
        line = ', '.join([ '0x{val:02x}'.format(val=c) for c in x ])
        out.append(' {line}{end_comma}'.format(line=line, end_comma=',' if i<len(l)-1 else ''))
    out.append('};')
    out.append('unsigned int {var_name}_len = {data_len};'.format(var_name=var_name, data_len=len(data)))
    return '\n'.join(out)

class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Things will go here
        self.box1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.box2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.box3 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.box4 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.set_child(self.box1)
        self.box1.append(self.box2)
        self.box1.append(self.box3)
        self.box1.append(self.box4)

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

        self.run_button = Gtk.Button(label="Build and Run")
        self.header.pack_start(self.run_button)
        self.run_button.connect('clicked', self.build_and_run)
        self.run_button.set_icon_name("media-playback-start-symbolic")

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

        label = Gtk.Label.new("Project")
        self.box2.append(label)
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_min_content_height(400)
        self.scroll.set_min_content_width(200)
        self.listbox = Gtk.ListBox()
        self.listbox.connect("row-selected", self.selection_changed)
        self.scroll.set_child(self.listbox)
        self.box2.append(self.scroll)

        button = Gtk.Button.new_with_label("Save")
        button.connect("clicked", self.save_object)
        self.box2.append(button)

        self.project_path = ""
        self.filename = ""
        self.obj = {}
        self.event = ""

        collisionevent = Gio.SimpleAction.new("collision", None)
        collisionevent.connect("activate", self.event_collision)
        self.add_action(collisionevent)
        spawnaction = Gio.SimpleAction.new("spawn", None)
        spawnaction.connect("activate", self.action_spawn)
        self.add_action(spawnaction)

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
        self.filename = self.project_path+os.sep+row.get_child().get_label()
        button = Gtk.Button.new_with_label("Open externally")
        button.connect('clicked', self.open_external)
        name, ext = os.path.splitext(self.filename)
        if ext == ".bmp" or ext == ".png" or ext == ".jpg":
            image = Gtk.Image.new_from_file(self.filename)
            self.box3.append(image)
        if ext == ".wav" or ext == ".ogg":
            media = Gtk.MediaFile.new_for_filename(self.filename)
            media.play()
        if ext == ".lua":
            f = open(self.filename, "r")
            label = Gtk.Label.new(f.read())
            f.close()
            self.box3.append(label)
        if ext == ".json":
            self.show_events()
        else:
            self.box3.append(button)

    def open_external(self, button):
        os.system(f"xdg-open {self.filename}")

    def show_events(self):
        f = open(self.filename, "r")
        self.obj = json.loads(f.read())
        f.close()
        self.box3.set_spacing(10)
        self.box3.set_margin_top(10)
        self.box3.set_margin_bottom(10)
        self.box3.set_margin_start(10)
        self.box3.set_margin_end(10)
        title = Gtk.Label.new("Events")
        self.box3.append(title)
        scroll = Gtk.ScrolledWindow()
        scroll.set_min_content_height(400)
        scroll.set_min_content_width(100)
        listbox = Gtk.ListBox()
        listbox.connect("row-selected", self.show_actions)
        scroll.set_child(listbox)
        self.box3.append(scroll)
        try:
            for key in self.obj["events"]:
                label = Gtk.Label.new(key)
                row = Gtk.ListBoxRow()
                row.set_child(label)
                listbox.append(row)
        except KeyError:
            pass
        menu = Gio.Menu.new()
        menu.append("Collision", "win.collision")
        popover = Gtk.PopoverMenu()
        popover.set_menu_model(menu)
        button = Gtk.MenuButton()
        button.set_popover(popover)
        addlabel = Gtk.Label.new("Add event")
        button.set_child(addlabel)
        self.box3.append(button)

    def show_actions(self, box, row):
        self.event = row.get_child().get_label()
        self.box1.remove(self.box4)
        self.box4 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.box1.append(self.box4)
        self.box4.set_spacing(10)
        self.box4.set_margin_top(10)
        self.box4.set_margin_bottom(10)
        self.box4.set_margin_start(10)
        self.box4.set_margin_end(10)
        title = Gtk.Label.new("Actions")
        self.box4.append(title)
        scroll = Gtk.ScrolledWindow()
        scroll.set_min_content_height(400)
        scroll.set_min_content_width(100)
        listbox = Gtk.ListBox()
        listbox.connect("row-selected", self.show_params)
        scroll.set_child(listbox)
        self.box4.append(scroll)
        try:
            for action in self.obj["events"][row.get_child().get_label()]:
                label = Gtk.Label.new(action["type"])
                row = Gtk.ListBoxRow()
                row.set_child(label)
                listbox.append(row)
        except KeyError:
            pass
        menu = Gio.Menu.new()
        menu.append("Spawn", "win.spawn")
        popover = Gtk.PopoverMenu()
        popover.set_menu_model(menu)
        button = Gtk.MenuButton()
        button.set_popover(popover)
        addlabel = Gtk.Label.new("Add action")
        button.set_child(addlabel)
        self.box4.append(button)

    def show_params(self, box, row):
        print(row.get_child().get_label())

    def save_object(self, button):
        try:
            f = open(self.filename, "w")
            f.write(json.dumps(self.obj, indent="\t"))
            f.close()
        except FileNotFoundError:
            pass

    def event_collision(self, action, param):
        self.obj["events"]["collision"] = []

    def action_spawn(self, action, param):
        self.obj["events"][self.event].append({"type": "spawn"})

    def build_and_run(self, button):
        datadir = os.getenv("XDG_DATA_HOME")
        if datadir == None:
            if os.name == 'posix':
                datadir = "/home/"+os.getlogin()+"/.local/share"
            else:
                datadir = "%APPDATA%"
        buildpath = datadir+os.sep+"tidal-gtk"#+os.sep+"build"
        try:
            os.mkdir(buildpath)
        except FileExistsError:
            pass
        try:
            repo = git.Repo.clone_from("https://github.com/EmperorPenguin18/tidal2d", buildpath, multi_options=['--depth 1', '--branch 0.3'])
        except git.exc.GitCommandError:
            pass
        tar = tarfile.open(buildpath+os.sep+"assets.tar", "w")
        tar.add(self.project_path)
        tar.close()
        tar = open(buildpath+os.sep+"assets.tar", "rb")
        header = open(buildpath+os.sep+"src"+os.sep+"embedded_assets.h", "w")
        header.write(bin2header(tar.read(), "embedded_binary"))
        tar.close()
        header.close()
        os.chdir(buildpath)
        os.system("cmake . -DCMAKE_BUILD_TYPE=Debug -DSTATIC=ON")
        os.system("cmake --build .")
        os.system(f".{os.sep}tidal2d")

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
