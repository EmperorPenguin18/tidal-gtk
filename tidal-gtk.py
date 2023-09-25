#!/bin/python

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

def on_activate(app):
    win = Gtk.ApplicationWindow(application=app)
    win.present()

def main():
    app = Gtk.Application()
    app.connect('activate', on_activate)
    app.run(None)

if __name__ == "__main__":
    main()
