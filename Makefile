INSTALLPATH="/usr/share/pysyncp3"
INSTALLTEXT="pysyncp3 is now installed"
UNINSTALLTEXT="pysyncp3 has been removed"

install-req:
	@mkdir -p $(INSTALLPATH)
	@cp pysyncp3/* $(INSTALLPATH) -f
	@cp README $(INSTALLPATH) -f
	@cp AUTHORS $(INSTALLPATH) -f
	@cp LICENSE $(INSTALLPATH) -f
	@cp bin/pysyncp3 /usr/bin/ -f
	@cp share/pysyncp3.png /usr/share/pixmaps -f
	@cp share/pysyncp3.desktop /usr/share/applications/ -f

install: install-req
	@echo $(INSTALLTEXT)

uninstall-req:
	@rm -rf $(INSTALLPATH)
	@rm /usr/share/pixmaps/pysyncp3.png
	@rm /usr/share/applications/pysyncp3.desktop
	@rm /usr/bin/pysyncp3

uninstall: uninstall-req
	@echo $(UNINSTALLTEXT)
