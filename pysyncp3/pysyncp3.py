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
import ConfigParser

from gi.repository import Gtk
from xdg.BaseDirectory import xdg_config_dirs

# python-eyeD3 required for parsing tags
try:
    import eyeD3
    TAG_SUPPORT = True
except ImportError:
    TAG_SUPPORT = False

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
TOTALCOUNT = 0
CONFIG = xdg_config_dirs[0] + '/usyncp3.conf'
ICON_DIR = '/usr/share/icons/gnome/'


class PYSYNCP3(object):
    """ browse folders in ui and sync them to USB """
    def __init__(self):
        """ Initialise the main window and start """
        self.builder = Gtk.Builder()
        self.builder.add_from_file("/usr/share/pysyncp3/pysyncp3.ui")
        self.builder.connect_signals(self)
        if not TAG_SUPPORT:
            self.popwindow = self.builder.get_object("popup_window")
            closeerror = self.builder.get_object("closepop")
            closeerror.connect("clicked", self.closeerror)
            self.popwindow.set_markup('PYSYNCP3 ERROR: Please install python-eyed3')
            self.popwindow.show()
            Gtk.main()
        else:
            # main window
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
            self.settingsbutton = self.builder.get_object("settingsbutton")
            self.backbutton = self.builder.get_object("backbutton")
            self.homebutton = self.builder.get_object("homebutton")
            self.suffixbox = self.builder.get_object('suffixentry')
            self.refreshmediabutton = self.builder.get_object("refreshmediabutton")
            self.syncfolderbutton = self.builder.get_object("syncfolderbutton")
            self.syncrandombutton = self.builder.get_object("syncrandombutton")
            self.statusbar = self.builder.get_object('statuslabel')
            # conf window
            self.confwindow = self.builder.get_object("configwindow")
            self.libraryentry = self.builder.get_object('libraryentry')
            self.styleentry = self.builder.get_object('styleentry')
            self.homeentry = self.builder.get_object('homeentry')
            self.applybutton = self.builder.get_object("applyconf")
            self.closebutton = self.builder.get_object("closeconf")
            # dialog windows
            self.popwindow = self.builder.get_object("popup_window")
            self.popbutton = self.builder.get_object("closepop")
            self.enddialog = self.builder.get_object("end_dialog")
            self.endclosebutton = self.builder.get_object("endclosebutton")
            # load basic elements / connect actions
            self.prepwindow()
            self.originalfolder = None
            self.current_dir = None
            self.randomcount = None
            self.filelist = None
            self.synclist = None
            # read conf file
            self.conf = ConfigParser.RawConfigParser()
            self.conf.read(CONFIG)
            self.homefolder = self.conf.get('conf', 'home')
            self.library = self.conf.get('conf', 'defaultlibrary')
            self.libraryformat = self.conf.get('conf', 'outputstyle')
            # start
            self.run()

    def run(self, *args):
        """ Fill and show the main window """
        self.listfolder(self.homefolder)
        self.fill_random()
        self.scan_for_media()
        self.window.show()
        Gtk.main()

    def prepwindow(self):
        """ run prep outside init """
        # connect events
        self.window.connect("destroy", self.quit)
        self.settingsbutton.connect("clicked", self.showconfig)
        self.foldertree.connect("key-press-event", self.keypress)
        self.foldertree.connect("row-activated", self.folderclick)
        self.settingsbutton.connect("clicked", self.showconfig)
        self.refreshmediabutton.connect("clicked", self.scan_for_media)
        self.syncfolderbutton.connect("clicked", self.sync_folder)
        self.syncrandombutton.connect("clicked", self.sync_random)
        self.backbutton.connect("clicked", self.goback)
        self.homebutton.connect("clicked", self.gohome)
        self.applybutton.connect("clicked", self.saveconf)
        self.closebutton.connect("clicked", self.closeconf)
        self.popbutton.connect("clicked", self.closepop)
        self.endclosebutton.connect("clicked", self.closeendpop)
        # prepare folder list
        cell = Gtk.CellRendererText()
        foldercolumn = Gtk.TreeViewColumn("Select Folder:", cell, text=0)
        self.foldertree.append_column(foldercolumn)
        self.foldertree.set_model(self.folderlist)
        # check for config file and info
        self.checkconfig()

    def fill_random(self, *args):
        """ set initial default active checkbox """
        self.randomtrack.set_active(True)
        self.randomalbum.set_active(False)
        self.randomartist.set_active(False)

    def showconfig(self, *args):
        """ fill and show the config window """
        self.homeentry.set_text(self.homefolder)
        self.libraryentry.set_text(self.library)
        self.styleentry.set_text(self.libraryformat)
        self.confwindow.show()
        return

    def saveconf(self, *args):
        """ save any config changes and update live settings"""
        self.conf.read(CONFIG)
        self.conf.set('conf', 'home', self.homeentry.get_text())
        self.conf.set('conf', 'defaultlibrary', self.libraryentry.get_text())
        self.conf.set('conf', 'outputstyle', self.styleentry.get_text())
        self.homefolder = self.homeentry.get_text()
        self.library = self.libraryentry.get_text()
        self.libraryformat = self.styleentry.get_text()
        # write to conf file
        conffile = open(CONFIG, "w")
        self.conf.write(conffile)
        conffile.close()
        return

    def closeconf(self, *args):
        """ hide the config window """
        self.confwindow.hide()
        return

    def closepop(self, *args):
        """ hide the config window """
        self.popwindow.hide()
        return

    def closeendpop(self, *args):
        """ hide the config window """
        self.statusbar.set_text('')
        self.enddialog.hide()
        return

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
        self.listfolder(back_dir)
        return

    def keypress(self, actor, event):
        """ capture backspace key for folder navigation """
        if event.get_keycode()[1] == 22:
            self.goback()

    def closeerror(self, *args):
        """ hide the config window """
        self.popwindow.destroy()
        Gtk.main_quit(*args)
        return False

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
            try:
                string = string.replace(URL_ASCII[count], '_')
            except UnicodeDecodeError:
                pass
            count = count + 1
        return string

    def fill_string(self, items, destin):
        """ function to replace the variables with the tags for each file """
        tmp_title = None
        tmp_artist = None
        tmp_album = None
        tmp_albumartist = None
        tmp_genre = None
        tmp_track = None
        tmp_disc = None
        tmp_year = None
        tmp_comment = None
        try:
            item = eyeD3.Tag()
            item.link(items)
            print item.getTitle()
        except NameError:
            # Tag error
            print 'tagerror!'
            item = None
        # pull tag info for the current item
        if item:
            tmp_title = item.getTitle()
            if tmp_title == 'None':
                tmp_title = None
            if tmp_title:
                tmp_title = tmp_title.replace('/', '_')
            tmp_artist = item.getArtist('TPE1')
            if tmp_artist == 'None':
                tmp_artist = None
            if tmp_artist:
                tmp_artist = tmp_artist.replace('/', '_')
            tmp_album = item.getAlbum()
            if tmp_album == 'None':
                tmp_album = None
            if tmp_album:
                tmp_album = tmp_album.replace('/', '_')
            tmp_albumartist = item.getArtist('TPE2')
            if tmp_albumartist == 'None':
                tmp_albumartist = None
            if tmp_albumartist:
                tmp_albumartist = tmp_albumartist.replace('/', '_')
            try:
                tmp_genre = str(item.getGenre())
            except eyeD3.tag.GenreException:
                tmp_genre = None
            if tmp_genre == 'None':
                tmp_genre = None
            if tmp_genre:
                tmp_genre = tmp_genre.replace('/', '_')
                if ')' in tmp_genre:
                    tmp_genre = tmp_genre.split(')')[1]
            tmp_track = str(item.getTrackNum()[0])
            if tmp_track == 'None':
                tmp_track = None
            if tmp_track:
                if '/' in tmp_track:
                    tmp_track = tmp_track.split('/')[0]
                if len(tmp_track) == 1:
                    tmp_track = '0' + str(tmp_track)
                if len(tmp_track) > 2:
                    tmp_track = tmp_track[:2]
            tmp_disc = str(item.getDiscNum()[0])
            if tmp_disc == 'None':
                tmp_disc = None
            if tmp_disc:
                if '/' in tmp_disc:
                    tmp_disc = tmp_disc.split('/')[0]
                if len(tmp_disc) == 2:
                    tmp_disc = tmp_disc[-1]
            tmp_year = item.getYear()
            if tmp_year == 'None':
                tmp_year = None
            tmp_comment = item.getComment()
            if tmp_comment == 'None':
                tmp_comment = None
            if tmp_comment:
                tmp_comment = tmp_comment.replace('/', '_')
            # replace temp strings with actual tags
            if tmp_title:
                destin = destin.replace('%title%', tmp_title)
            if tmp_albumartist:
                destin = destin.replace('%albumartist%', tmp_albumartist)
            else:
                destin = destin.replace('%albumartist%', '%artist%')
            if tmp_artist:
                destin = destin.replace('%artist%', tmp_artist)
            if tmp_album:
                destin = destin.replace('%album%', tmp_album)
            if tmp_genre:
                destin = destin.replace('%genre%', tmp_genre)
            if tmp_track:
                destin = destin.replace('%track%', tmp_track)
            if tmp_disc:
                destin = destin.replace('%disc%', tmp_disc)
            if tmp_year:
                destin = destin.replace('%year%', tmp_year)
            if tmp_comment:
                destin = destin.replace('%comment%', tmp_comment)
            destin = destin + items[(items.rfind('.')):]
            return destin
        return

    def listfolder(self, *args):
        """ function to list the folder column """
        self.current_dir = args[0]
        self.current_dir = self.current_dir.replace('//', '/')
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
        # list files when no more folders found
        if len(self.folderlist) == 0:
            for items in self.filelist:
                if not items[0] == '.':
                    self.folderlist.append([items])
        return

    def sync_folder(self, *args):
        """ sync files to media device """
        self.synclist = []
        self.originalfolder = self.current_dir
        currentitem =  self.mediacombo.get_active_iter()
        try:
            destinfolder = (self.medialist.get_value(currentitem, 0) + '/' +
                                self.suffixbox.get_text())
        except TypeError:
            self.popwindow.set_markup('ERROR: Please insert a USB device and' +
                                       ' refresh device list.')
            self.popwindow.show()
            return False
        if os.statvfs(os.path.dirname(destinfolder)).f_bfree <= 10000:
            self.popwindow.set_markup('ERROR: Low space on USB drive.')
            self.popwindow.show()
            return False
        self.sync_source(self.current_dir)
        if not len(self.synclist) == 0:
            for items in self.synclist:
                if os.statvfs(os.path.dirname(destinfolder)).f_bfree <= 10000:
                    self.popwindow.set_markup('ERROR: Low space on USB drive.')
                    self.popwindow.show()
                    return False
                self.statusbar.set_text('Copied ' + os.path.basename(items))
                destin = os.path.join(destinfolder + '/' +
                                       self.libraryformat)
                destin = self.fill_string(items, destin)
                self.statusbar.set_text('Copying... ' + os.path.basename(items))
                if not os.path.isdir(os.path.dirname(destin)):
                    os.makedirs(os.path.dirname(destin))
                try:
                    # Try to copy as original filename
                    shutil.copy(items, destin)
                except IOError:
                    # FAT32 Compatability
                    shutil.copy(items, self.remove_utf8(destin))
            self.enddialog.set_markup('Folder sync complete.')
            self.enddialog.show()

    def sync_source(self, *args):
        """ Get file list for syncing """
        if not args[0] == '' and not type(args[0]) == Gtk.Button:
            sourcefolder = args[0]
        currentfolder = os.listdir(sourcefolder)
        currentfolder.sort()
        for items in currentfolder:
            source = os.path.join(sourcefolder + '/' + items)
            #destin = os.path.join(destinfolder + str.replace(sourcefolder,
            #                        self.originalfolder, '') + '/' + items)
            if os.path.isdir(source):
                self.sync_source(source)
            if source[(source.rfind('.')):] == '.mp3':
                self.synclist.append(source.decode('utf-8'))
        return

    def get_random_type(self, *args):
        """ determine the type of random sync """
        randomitem = None
        if self.randomtrack.get_active():
            randomitem = 'track'
        elif self.randomalbum.get_active():
            randomitem = 'album'
        elif self.randomartist.get_active():
            randomitem = 'artist'
        else:
            randomitem = None
        return randomitem

    def sync_random(self, *args):
        """ Main random function  """
        tmp = self.get_random_type()
        self.synclist = []
        self.randomlist = []
        self.originalfolder = self.current_dir
        currentitem =  self.mediacombo.get_active_iter()
        try:
            destinfolder = (self.medialist.get_value(currentitem, 0) + '/' +
                                self.suffixbox.get_text())
        except TypeError:
            self.popwindow.set_markup('ERROR: Please insert a USB device and' +
                                       ' refresh device list.')
            self.popwindow.show()
            return False
        if os.statvfs(os.path.dirname(destinfolder)).f_bfree <= 10000:
            self.popwindow.set_markup('ERROR: Low space on USB drive.')
            self.popwindow.show()
            return False
        if tmp == 'track':
            #print 'tracksssssssss'
            self.randomlist = None
            self.random_track(self.originalfolder, destinfolder)
            return
        self.sync_source(self.current_dir)
        if not len(self.synclist) == 0:
            if not self.randomlist == None:
                for items in self.synclist:
                    try:
                        item = eyeD3.Tag()
                        item.link(items)
                        item.setVersion(eyeD3.ID3_V2_4)
                        item.setTextEncoding(eyeD3.UTF_8_ENCODING)
                    except Exception, err:
                        print 'line 244'
                        print type(err)
                        print err
                        # Tag error
                        item = None
                    if tmp == 'artist':
                        #print 'artist XXXX'
                        tmp_artist = item.getArtist('TPE1')
                        if tmp_artist == 'None':
                            tmp_artist = None
                        if tmp_artist:
                            tmp_artist = tmp_artist.replace('/', '_')
                            if not tmp_artist in self.randomlist:
                                self.randomlist.append(tmp_artist)
                    elif tmp == 'album':
                        #print 'ALBUMSSSSSSS'
                        tmp_album = item.getAlbum()
                        if tmp_album == 'None':
                            tmp_album = None
                        if tmp_album:
                            tmp_album = tmp_album.replace('/', '_')
                            if not tmp_album in self.randomlist:
                                self.randomlist.append(tmp_album)
            if os.statvfs(os.path.dirname(destinfolder)).f_bfree <= 10000:
                self.popwindow.set_markup('ERROR: Low space on USB drive.')
                self.popwindow.show()
                return False
            if not self.randomlist:
                return
            else:
                STOP = False
                count = 0
                # sync random files until out of items or full
                while not os.statvfs(os.path.dirname(destinfolder)).f_bfree <= 10000 and not STOP and not count == 10:
                    tmp = random.choice(self.randomlist)
                    for items in self.synclist:
                        if tmp in items:
                            if os.statvfs(os.path.dirname(destinfolder)).f_bfree <= 10000:
                                STOP = True
                                self.popwindow.set_markup('ERROR: Low space on USB drive.')
                                self.popwindow.show()
                                return False
                            self.statusbar.set_text('Copied ' + os.path.basename(items))
                            destin = os.path.join(destinfolder + '/' +
                                                   self.libraryformat)
                            destin = self.fill_string(items, destin)
                            self.statusbar.set_text('Copying... ' + os.path.basename(items))
                            try:
                                if not os.path.isdir(os.path.dirname(destin)):
                                    os.makedirs(os.path.dirname(destin))
                            except AttributeError:
                                # caused by fill_string errors with files.
                                return False
                            try:
                                # Try to copy as original filename
                                shutil.copy(items, destin)
                            except IOError:
                                # FAT32 Compatability
                                shutil.copy(items, self.remove_utf8(destin))
                    count = count + 1    
                self.enddialog.set_markup('Folder sync complete.')
                self.enddialog.show()
                return

    def random_track(self, *args):
        """ find and copy random music files to your chosen USB device """
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
        tmp_count = 255
        if len(self.synclist) < tmp_count:
            tmp_count = len(self.synclist)
        while trackcount < tmp_count and not os.statvfs(os.path.dirname(destinbase)
                                                    ).f_bfree == 10000:
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
                except OSError:
                    print 'Creating ' + destin + ' failed.'
        self.statusbar.set_text('Random sync completed.')

    def scan_for_media(self, *args):
        """ fill the UI with available USB media devices """
        media_dir = '/media'
        # clear list if we have scanned before
        for items in self.medialist:
            self.medialist.remove(items.iter)
        # check ubuntu/mint media folders
        for items in os.listdir(media_dir):
            if items == os.getenv('USERNAME'):
                media_dir = media_dir + '/' + os.getenv('USERNAME')
        # search the media directory for items
        for items in os.listdir(media_dir):
            if not items[:5] == 'cdrom':
                self.medialist.append([media_dir + '/' + items])
        # clear combobox before adding entries
        self.mediacombo.clear()
        self.mediacombo.set_model(self.medialist)
        cell = Gtk.CellRendererText()
        self.mediacombo.pack_start(cell, False)
        self.mediacombo.add_attribute(cell, 'text', 0)
        self.mediacombo.set_active(0)
        return

if __name__ == "__main__":
    PYSYNCP3()
