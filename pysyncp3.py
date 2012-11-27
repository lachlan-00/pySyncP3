#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" USyncP3: Sync Music to your media devices
    ----------------Authors----------------
    Lachlan de Waard <lachlan.00@gmail.com>
    ----------------Licence----------------
    GNU General Public License version 3

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

import shutil
import os
import random
import mimetypes

from gi.repository import Gtk
from xdg.BaseDirectory import xdg_config_dirs

URL_ASCII = ('%', "#", ';', '"', '<', '>', '?', '[', '\\', "]", '^', '`', '{',
            '|', '}', '€', '‚', 'ƒ', '„', '…', '†', '‡', 'ˆ', '‰', 'Š', '‹',
            'Œ', 'Ž', '‘', '’', '“', '”', '•', '–', '—', '˜', '™', 'š', '›',
            'œ', 'ž', 'Ÿ', '¡', '¢', '£', '¥', '|', '§', '¨', '©', 'ª', '«',
            '¬', '¯', '®', '¯', '°', '±', '²', '³', '´', 'µ', '¶', '·', '¸',
            '¹', 'º', '»', '¼', '½', '¾', '¿', 'À', 'Á', 'Â', 'Ã', 'Ä', 'Å',
            'Æ', 'Ç', 'È', 'É', 'Ê', 'Ë', 'Ì', 'Í', 'Î', 'Ï', 'Ð', 'Ñ', 'Ò',
            'Ó', 'Ô', 'Õ', 'Ö', 'Ø', 'Ù', 'Ú', 'Û', 'Ü', 'Ý', 'Þ', 'ß', 'à',
            'á', 'â', 'ã', 'ä', 'å', 'æ', 'ç', 'è', 'é', 'ê', 'ë', 'ì', 'í',
            'î', 'ï', 'ð', 'ñ', 'ò', 'ó', 'ô', 'õ', 'ö', '÷', 'ø', 'ù', 'ú',
            'û', 'ü', 'ý', 'þ', 'ÿ', '¦', ':', '*')

LIBRARYSTYLE = ['Artist', 'Album', 'Track']
HOMEFOLDER = os.getenv('HOME')
DISKFREE = True
#count = 0
TOTALCOUNT = 0
CONFIG = xdg_config_dirs[0] + '/usyncp3.conf'
ICON_DIR = '/usr/share/icons/gnome/'


class USYNCP3(object):
    """ ??? """
    def __init__(self):
        """ ??? """
        self.builder = Gtk.Builder()
        self.builder.add_from_file("pysyncp3.ui")
        self.builder.connect_signals(self)
        # load ui
        self.window = self.builder.get_object("main_window")
        self.foldertree = self.builder.get_object("folderview")
        self.folderlist = self.builder.get_object('folderstore')
        self.currentdirlabel = self.builder.get_object('currentdirlabel')
        self.medialist = self.builder.get_object('medialiststore')
        self.mediacombo = self.builder.get_object("mediacombobox")
        self.randomgroup = self.builder.get_object('randomgroup')
        self.randomtrack = self.builder.get_object('trackbutton')
        self.randomalbum = self.builder.get_object('albumbutton')
        self.randomartist = self.builder.get_object('artistbutton')
        self.statusbar = self.builder.get_object('statusbar1')
        self.suffixbox = self.builder.get_object('suffixentry')
        # connect events
        self.window.connect("destroy", self.quit)
        self.foldertree.connect("key-press-event", self.keypress)
        self.foldertree.connect("row-activated", self.folderclick)
        # prepare folder list
        cell = Gtk.CellRendererText()
        foldercolumn = Gtk.TreeViewColumn("Select Folder:", cell, text=0)
        filecolumn = Gtk.TreeViewColumn("Select Files", cell, text=0)
        self.foldertree.append_column(foldercolumn)
        self.foldertree.set_model(self.folderlist)
        # get config info
        self.conf = ConfigParser.RawConfigParser()
        self.conf.read(CONFIG)
        self.checkconfig()
        self.homefolder = self.conf.get('conf', 'home')
        self.library = self.conf.get('conf', 'defaultlibrary')
        self.libraryformat = self.conf.get('conf', 'outputstyle')
        # fill UI
        self.listfolder(self.homefolder)
        self.fill_random()
        self.scan_for_media()
        self.run()

    def run(self, *args):
        """ ??? """
        self.window.show()
        Gtk.main()

    def folderclick(self, *args):
        """ traverse folders on double click """
        model, treeiter = self.foldertree.get_selection().get_selected()
        if treeiter:
            new_dir = self.current_dir + '/' + model[treeiter][0]
        if os.path.isdir(new_dir):
            self.listfolder(new_dir)
        return

    def gohome(self, *args):
        """ go to the defined home folder """
        self.listfolder(self.homefolder)

    def goback(self, *args):
        """ go back the the previous directory """
        back_dir = os.path.dirname(self.current_dir)
        self.clearopenfiles()
        self.listfolder(back_dir)
        return

    def keypress(self, actor, event):
        """ capture backspace key for folder navigation """
        if event.get_keycode()[1] == 22:
            self.goback()

    def quit(self, *args):
        """ stop the process thread and close the program"""
        self.window.destroy()
        Gtk.main_quit(*args)
        return False

    def checkconfig(self):
        """ create a default config if not available """
        if not os.path.isfile(CONFIG):
            conffile = open(CONFIG, "w")
            conffile.write("[conf]\nhome = " + os.getenv('HOME') +
                       "\ndefaultlibrary = " + os.getenv('HOME') +
                       "\noutputstyle = %artist% - %album% " +
                       " - %track% - %title%\n")
            conffile.close()
        return

    def remove_utf8(self, *args):
        """ Function to help with FAT32 devices """
        string = args[0]
        count = 0
        # replace disallowed characters with '_'
        while count < len(URL_ASCII):
            string = string.replace(URL_ASCII[count], '_')
            count = count + 1
        return string

    def listfolder(self, *args):
        """ function to list the folder column """
        self.current_dir = args[0]
        self.currentdirlabel.set_text('Current Folder: ' + 
                                      str(os.path.normpath(self.current_dir)))
        if not type(args[0]) == type(''):
            self.current_dir = args[0].get_current_folder()
        try:
            self.filelist = os.listdir(self.current_dir)
            self.filelist.sort(key=lambda y: y.lower())
        except OSError:
            self.listfolder(os.getenv('HOME'))
        # clear list if we have scanned before
        for items in self.folderlist:
            self.folderlist.remove(items.iter)
        # clear combobox before adding entries
        for items in self.foldertree:
            self.foldertree.remove(items.iter)
        # search the supplied directory for items
        for items in self.filelist:
            test_dir = os.path.isdir(self.current_dir + '/' + items)
            if not items[0] == '.' and test_dir:
                self.folderlist.append([items])
        return

    def sync_source(self, *args):
        """ copy files in source folder to media device """
        print type(args[0])
        if not args[0] == '' and not type(args[0]) == Gtk.Button:
            sourcefolder = args[0]
        currentitem =  self.mediacombo.get_active_iter()
        destinfolder = self.medialist.get_value(currentitem, 0)
        currentfolder = os.listdir(sourcefolder)
        currentfolder.sort()
        for items in currentfolder:
            source = os.path.join(sourcefolder + '/' + items)
            destin = os.path.join(destinfolder + str.replace(sourcefolder,
                                    originalfolder, '')
                                     + '/' + items)
            if os.path.isdir(source):
                self.sync_source(source)
            if os.path.isfile(source):
                if not os.path.isdir(os.path.dirname(destin)):
                    try:
                        os.makedirs(os.path.dirname(destin))
                    except OSError:
                        """ FAT32 Compatability """
                        destin = self.remove_utf8(destin)
                        if not os.path.isdir(os.path.dirname(destin)):
                            os.makedirs(os.path.dirname(destin))
                try:
                    """ Try to copy as original filename """
                    shutil.copy(source, destin)
                except IOError:
                    """ FAT32 Compatability """
                    shutil.copy(source, self.remove_utf8(destin))
                print 'Moved ' + items
                print ' '
        return

    def get_random_type(self, *args):
        """ ??? """
        if self.randomtrack.get_active():
            randomitem = 'Track'
        if self.randomalbum.get_active():
            randomitem = 'Album'
        if self.randomartist.get_active():
            randomitem = 'Artist'
        self.randomcount = 0
        for items in LIBRARYSTYLE:
            if items == randomitem:
                print 'Random Sync By: ' + randomitem
                return self.randomcount  + 1
            else:
                self.randomcount = self.randomcount + 1
        return self.randomcount
    
    def random_folder(self, *args):
        """ ??? """
        print 'random folder'
        library = args[0]
        depth = args[1]
        destinbase = args[2]
        test = library + '/' + random.choice(os.listdir(library))
        self.statusbar.pop(40)
        self.statusbar.push(41, 'Random sync completed.')

    def random_track(self, *args):
        """ ??? """
        print 'random track'
        library = args[0]
        destinbase = args[1] + '/RANDOM0'
        randompath = False
        filler = 0
        while not randompath:
            if not os.path.isdir(destinbase[:-1] + str(filler)):
                randomstr = (str(filler) + '/')
                print 'random path creation'
                print randomstr
                os.makedirs(os.path.dirname(destinbase[:-1] + randomstr))
                destinbase = os.path.dirname(destinbase[:-1] + randomstr)
                randompath = True
            else:
                filler = filler + 1
        trackcount = 0
        while trackcount < 255 and not os.statvfs(os.path.dirname(destinbase)).f_bfree == 20000:
            test = library + '/' + random.choice(os.listdir(library))
            while os.path.isdir(test):
                try:
                    test = test + '/' + random.choice(os.listdir(test))
                except IndexError:
                    test = library + '/' + random.choice(os.listdir(library))
            if mimetypes.guess_type(test)[0] == 'audio/mpeg':
                destin = os.path.join(destinbase + '/' + os.path.basename(test))
                trackcount = trackcount + 1
                try:
                    print 'Copying: ' + test
                    shutil.copy(test, self.remove_utf8(destin))
                except:
                    print 'Creating ' + destin + ' failed.'
        self.statusbar.pop(40)
        self.statusbar.push(41, 'Random sync completed.')

    def random_sync(self, *args):
        """ Find and copy random files """
        global DISKFREE
        global count
        library = args[0]
        if type(args[0]) == Gtk.Button:
            library = self.homefolder
        self.statusbar.pop(41)
        self.statusbar.push(40, 'Random sync in progress...')
        self.randomcount = 0
        self.randomcount = self.get_random_type()
        currentitem =  self.mediacombo.get_active_iter()
        randomdestin = self.medialist.get_value(currentitem, 0) + '/' + self.suffixbox.get_text()
        #while DISKFREE and not os.statvfs(os.path.dirname(destinfolder)).f_bfree == 20000:
        if len(LIBRARYSTYLE) == self.randomcount:
            self.random_track(library, randomdestin)
        else:
            print 'Random Folder Sync'
            self.random_folder(library, self.randomcount, randomdestin)
    
    def scan_for_media(self, *args):
        """ ??? """
        media_dir = '/media/'
        # clear list if we have scanned before
        for items in self.medialist:
            self.medialist.remove(items.iter)
        # check ubuntu/mint media folders
        for items in os.listdir('/media'):
            if items == os.getenv('USERNAME'):
                media_dir = media_dir + os.getenv('USERNAME')
        # search the media directory for items
        for items in os.listdir(media_dir):
            if not items == 'cdrom':
                self.medialist.append([media_dir + '/' + items])
        # clear combobox before adding entries
        self.mediacombo.clear()
        self.mediacombo.set_model(self.medialist)
        cell = Gtk.CellRendererText()
        self.mediacombo.pack_start(cell, False)
        self.mediacombo.add_attribute(cell,'text',0)
        self.mediacombo.set_active(0)
        return

    def fill_random(self, *args):
        """ ??? """
        self.randomtrack.set_active(False)
        self.randomalbum.set_active(True)
        self.randomartist.set_active(False)
        
if __name__ == "__main__":
    USYNCP3()
