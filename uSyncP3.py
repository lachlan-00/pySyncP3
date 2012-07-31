#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" USyncP3
    ----------------Authors----------------
    Lachlan de Waard <lachlan.00@gmail.com>
    ----------------Licence----------------
    GNU GPLv3

"""


import shutil
import os
#import subprocess
import random
import mimetypes

from gi.repository import Gtk

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
musiclibrary = '/home/user/music/albums'
librarystyle = ['Artist', 'Album', 'Track']
sourcefolder = os.path.dirname(os.getenv('HOME') + '/music/sync/')
originalfolder = sourcefolder
chooseDrive = ['zenity', '--list', '--text="Select a USB Drive"',
                    '--separator=" "', '--radiolist', '--column=',
                    '--column="USB Drives"']
diskFree = True
count = 0
TOTALCOUNT = 0


class uSyncP3(object):


    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("uSyncP3.ui")
        self.builder.connect_signals(self)
        sourcefolder = os.path.dirname(os.getenv('HOME'))
        self.library = self.builder.get_object("librarychooser")
        self.library.set_current_folder(sourcefolder)
        self.fill_random()
        self.scan_for_media()


    def run(self, *args):
        self.Window = self.builder.get_object("window1")
        self.Window.connect("destroy", self.quit)
        self.Window.show()
        Gtk.main()


    def quit(self, *args):
        Gtk.main_quit(*args)
        return False

    # replace disallowed characters with '_'
    def remove_utf8(self, *args):
        """ Function to help with FAT32 devices """
        string = args[0]
        count = 0
        while count < len(URL_ASCII):
            string = string.replace(URL_ASCII[count], '_')
            count = count + 1
        return string

    def sync_source(self, *args):
        global sourcefolder
        """ copy files in source folder to media device """
        print type(args[0])
        if not args[0] == '' and not type(args[0]) == Gtk.Button:
            sourcefolder = args[0]
        self.medialist = self.builder.get_object('medialiststore')
        self.mediacombo = self.builder.get_object("mediacombobox")
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
        if self.randomtrack.get_active():
            randomitem = 'Track'
        if self.randomalbum.get_active():
            randomitem = 'Album'
        if self.randomartist.get_active():
            randomitem = 'Artist'
        self.randomcount = 0
        for items in librarystyle:
            if items == randomitem:
                print 'Random Sync By: ' + randomitem
                return self.randomcount  + 1
            else:
                self.randomcount = self.randomcount + 1
        return self.randomcount
    
    def random_folder(self, *args):
        print 'random folder'
        library = args[0]
        depth = args[1]
        destinbase = args[2]
        test = library + '/' + random.choice(os.listdir(library))
        self.statusbar.pop(40)
        self.statusbar.push(41, 'Random sync completed.')

    def random_track(self, *args):
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
                    shutil.copy(test, self.remove_utf8(destin)s)
                except:
                    print 'Creating ' + destin + ' failed.'
        self.statusbar.pop(40)
        self.statusbar.push(41, 'Random sync completed.')

    # Find and copy random files
    def random_sync(self, *args):
        global diskFree
        global count
        library = args[0]
        if type(args[0]) == Gtk.Button:
            library = musiclibrary
        self.statusbar = self.builder.get_object('statusbar1')
        self.statusbar.pop(41)
        self.statusbar.push(40, 'Random sync in progress...')
        self.medialist = self.builder.get_object('medialiststore')
        self.mediacombo = self.builder.get_object('mediacombobox')
        self.suffixbox = self.builder.get_object('suffixentry')
        self.randomcount = 0
        self.randomcount = self.get_random_type()
        currentitem =  self.mediacombo.get_active_iter()
        randomdestin = self.medialist.get_value(currentitem, 0) + '/' + self.suffixbox.get_text()
        #while diskFree and not os.statvfs(os.path.dirname(destinfolder)).f_bfree == 20000:
        if len(librarystyle) == self.randomcount:
            self.random_track(library, randomdestin)
        else:
            print 'Random Folder Sync'
            self.random_folder(library, self.randomcount, randomdestin)
    
    def scan_for_media(self, *args):
        self.medialist = self.builder.get_object('medialiststore')
        # clear list if we have scanned before
        for items in self.medialist:
            self.medialist.remove(items.iter)
        # search the media directory for items
        for items in os.listdir('/media'):
            if not items == 'cdrom':
                self.medialist.append(['/media/' + items])
        self.mediacombo = self.builder.get_object('mediacombobox')
        # clear combobox before adding entries
        self.mediacombo.clear()
        self.mediacombo.set_model(self.medialist)
        cell = Gtk.CellRendererText()
        self.mediacombo.pack_start(cell, False)
        self.mediacombo.add_attribute(cell,'text',0)
        self.mediacombo.set_active(0)
        return

    def fill_random(self, *args):
        self.randomgroup = self.builder.get_object('randomgroup')
        self.randomtrack = self.builder.get_object('trackbutton')
        self.randomalbum = self.builder.get_object('albumbutton')
        self.randomartist = self.builder.get_object('artistbutton')
        self.randomtrack.set_active(False)
        self.randomalbum.set_active(True)
        self.randomartist.set_active(False)
        

uSyncP3().run()
