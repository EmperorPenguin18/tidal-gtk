build: tidal-gtk.py
	chmod +x tidal-gtk.py

install: tidal-gtk.py tidal-gtk.desktop
	cp tidal-gtk.py /usr/bin/tidal-gtk
	cp tidal-gtk.desktop /usr/share/applications/
