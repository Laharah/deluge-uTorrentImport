#
# gtkui.py
#
# Copyright (C) 2009 Laharah <laharah22+deluge@gmail.com>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#

from twisted.internet import defer

import gtk
from deluge.log import LOG as log
from deluge.ui.client import client
from deluge.plugins.pluginbase import GtkPluginBase
import deluge.component as component
from common import get_resource


class GtkUI(GtkPluginBase):
    def enable(self):
        self.glade = gtk.glade.XML(get_resource("config.glade"))

        component.get("Preferences").add_page("uTorrentImport",
                                              self.glade.get_widget("prefs_box"))

        component.get("PluginManager").register_hook("on_apply_prefs",
                                                     self.on_apply_prefs)

        component.get("PluginManager").register_hook("on_show_prefs", self.on_show_prefs)
        signal_dictionary = {
            'on_import_button_clicked': self.on_import_button_clicked,
            'on_resume_toggled': self.on_resume_toggled
        }
        log.debug('utorrentimport: signals hooked!')
        self.glade.signal_autoconnect(signal_dictionary)
        self.use_wine_mappings = self.glade.get_widget('use_wine_mappings')
        self.force_recheck = self.glade.get_widget('force_recheck')
        self.resume = self.glade.get_widget('resume')
        self.resume_dat_entry = self.glade.get_widget('resume_dat_entry')
        self.log_view = self.glade.get_widget('log_view')

        client.register_event_handler('uTorrentImportLoggingEvent', self.log_to_user)

    def disable(self):
        component.get("Preferences").remove_page("uTorrentImport")
        component.get("PluginManager").deregister_hook("on_apply_prefs", self.on_apply_prefs)

        component.get("PluginManager").deregister_hook("on_show_prefs", self.on_show_prefs)

    def on_apply_prefs(self):
        log.debug("applying prefs for uTorrentImport")
        self.config.update(self.gather_settings())
        client.utorrentimport.set_config(self.config)

    def log_to_user(self, level, message):
        if level in ('error', 'info'):
            buffer = self.log_view.get_buffer()
            iter = buffer.get_end_iter()
            buffer.insert(iter, message + '\n')
            adj = self.log_view.get_parent().get_vadjustment()
            adj.set_value(adj.get_upper() - adj.get_page_size())

    @defer.inlineCallbacks
    def on_show_prefs(self):
        log.debug("showing utorrentimport prefs")
        self.config = yield client.utorrentimport.get_config()
        log.debug('got config: {0}'.format(self.config))
        self.populate_config(self.config)
        log.debug('config populated')
        self.on_resume_toggled(_)  # Prevents invalid state
        if not self.config['previous_resume_dat_path']:
            default_resume = yield client.utorrentimport.get_default_resume_path()
            log.debug('utorrentimport: got resume.dat path!')
            if default_resume:
                self.resume_dat_entry.set_text(default_resume)

    @defer.inlineCallbacks
    def on_import_button_clicked(self, button):
        self.toggle_button(button)
        self.log_view.get_buffer().set_text('')
        settings = self.gather_settings()
        log.debug('sending import command...')
        result = yield client.utorrentimport.begin_import(
            settings['previous_resume_dat_path'],
            use_wine_mappings=settings['use_wine_mappings'],
            force_recheck=settings['force_recheck'],
            resume=settings['resume'])
        log.debug('recieved result! {0}'.format(result))
        self.toggle_button(button)
        self.show_result(result)

    def show_result(self, results):
        successes, failures = results
        title = u'uTorrentImport Finished'
        dialog = gtk.Dialog(title, None, True, (gtk.STOCK_OK, gtk.RESPONSE_OK))
        message = u'''uTorrentImport has finished importing torrents from uTorrent.\n
        {0} torrents have been added to deluge.\n
        {1} torrents were skipped.\n
        You may wish to restart the deluge UI to update the status
        of the added torrents.'''.format(len(successes), len(failures))

        label = gtk.Label(message)
        dialog.get_content_area().add(label)
        dialog.set_position(gtk.WIN_POS_CENTER)
        dialog.set_gravity(gtk.gdk.GRAVITY_CENTER)
        dialog.show_all()
        dialog.run()
        dialog.destroy()


    def on_resume_toggled(self, _):
        if not self.resume.get_active():
            self._previous_force_recheck = self.force_recheck.get_active()
            self.force_recheck.set_sensitive(False)
            self.force_recheck.set_active(True)
        else:
            self.force_recheck.set_active(self._previous_force_recheck)
            self.force_recheck.set_sensitive(True)

    def toggle_button(self, button):
        if button.get_sensitive():
            button.set_sensitive(False)
        else:
            button.set_sensitive(True)

    def populate_config(self, config):
        """callback for on show_prefs"""
        self.use_wine_mappings.set_active(config['use_wine_mappings'])
        self.force_recheck.set_active(config['force_recheck'])
        self._previous_force_recheck = config['force_recheck']
        self.resume.set_active(config['resume'])
        self.resume_dat_entry.set_text(config['previous_resume_dat_path'])

    def gather_settings(self):
        return {
            'use_wine_mappings': self.use_wine_mappings.get_active(),
            'force_recheck': self.force_recheck.get_active(),
            'resume': self.resume.get_active(),
            'previous_resume_dat_path': self.resume_dat_entry.get_text()
        }
