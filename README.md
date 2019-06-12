# uTorrentImport
### a cross platform Deluge plugin to import torrents from uTorrent

***NOTE: ONLY WORKS FOR DELUGE 1.3.x! NOT YET COMPATABLE FOR DELUGE 2.0***

**v2.3.8**
*Download [HERE](https://github.com/Laharah/deluge-uTorrentImport/releases/latest)*

* supports WINE mappings
* automatically searches for relevant uTorrent sessions
* Advanced support for renamed folder or relocated files.
* Support for importing the bandwidth settings for each torrent
* Supports setting the Added Date to match uTorrent's date added
* Skipped files are carried over from uTorrent
* **ONE BUTTON. NO COMMAND LINE NEEDED!**


#### Installation and use:

1. Download the appropriate .egg file here (use both if you're not sure):
   [DOWNLOADS](https://github.com/Laharah/deluge-uTorrentImport/releases/latest)
2. Open Deluge, go to Preferences > Plugins > Install Plugin
3. Add the .egg file(s)
4. Turn on the plugin (tick the box)
5. press the button!

![Screenshot](http://zippy.gfycat.com/LimpThreadbareAyeaye.gif)

### Changelog:
#### v2.3:
- Files skipped in uTorrent will not be downloaded by Deluge
- Some bug fixes for unicode torrent file names

#### v2.2.6:
- Added an option for preserving the uTorrent added date
- Added options for importing bandwidth settings for uTorrent torrents
- fixed rare bug with event timings that could prevent a torrent being rechecked
- fixed a bug with WINE path torrent files on separate drives.
- fixed a bug where backed up .torrent files could be saved without extension

#### v2.1.3:
- Added a Dialog to notify the user when the import is finished
- Better error reporting for missing or corrupt resume.dat files.
- Fixed a bug that was causing unnecessary renames
- Fixed a bug that could cause torrents with only one file nested in a folder to be
incorrectly renamed.
- Fixed a bug related to unicode torrent files that could cause the import to halt.

#### v2.1.0:
* Fixed some renamed torrents not rechecking properly
* added support for correctly redirecting individual files relocated by uTorrent
* Lowered chance of torrents beginning to download when adding large amounts of torrents at once. (adding may take more time now)

#### v2.0.2:
* Fixed torrent file unicode errors halting import
