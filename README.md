# uTorrentImport
### a cross platform Deluge plugin to import torrents from uTorrent
**v2.1.0**
*Download [HERE](https://github.com/Laharah/deluge-uTorrentImport/tree/master/dist)*

* supports WINE mappings
* automatically searches for relevent uTorrent sessions
* Advanced support for renamed folder or relocated files.
* **ONE BUTTON. NO COMMAND LINE NEEDED!**


#### Installation and use:

1. Download the appropriate .egg file here (use both if you're not sure): [DOWNLOADS]
(https://github.com/Laharah/deluge-uTorrentImport/tree/master/dist)
2. Open Deluge, go to Preferences > Plugins > Install Plugin
3. Add the .egg file(s)
4. Turn on the plugin (tick the box)
5. press the button!

![Screenshot](http://zippy.gfycat.com/LimpThreadbareAyeaye.gif)

### Changelog:
#### v2.1.2
- Added a Dialog to notify the user when the import is finished
- Fixed a bug that was causing unnecessary renames
- Fixed a bug that could cause torrents with only one file nested in a folder to be 
incorrectly renamed.
- Fixed a bug related to unicode torrent files taht could cause the import to halt.

#### v2.1.0:
* Fixed some renamed torrents not rechecking properly
* added support for correctly redirecting individual files relocated by uTorrent
* Lowered chance of torrents beginning to download when adding large amounts of torrents at once. (adding may take more time now)

#### v2.0.2:
* Fixed torrent file unicode errors halting import
