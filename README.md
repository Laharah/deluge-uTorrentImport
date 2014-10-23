Here's a little script I've written for windows that will import the torrents from uTorrent into deluge. The only other one I could find on the forums was written in PHP for use on linux, and it didn't work very well if you've renamed the torrents after download. So I wrote this one as a client script in python.

First a disclaimer:
I have never distributed anything in python, so I have no idea how to include the required dependencies or the relevant parts of the deluge client into a .egg or similar. I'd like to be able to distribute this for people of all technical ability, but I don't really know how. SO, you must at least have python and know how to install a python package. 

If anyone would like to tell me how to make this script in to a user friendly, self contained egg, or wants to do it themselves I'd be glad to put it up here. 

# Requirements

Python
a version of Deluge for windows that matches a python version you have installed. (click on "py2.7" if you have python 2.7)
Twisted installed for python

# Directions

Place the script in the deluge-1.3.6.egg folder in your deluge install path. (usually C:\Program Files (x86)\Deluge\deluge-1.3.6-py2.6.egg)
**YOU MUST DO THIS FOR THE SCRIPT TO RUN UNLESS YOU HAVE INSTALLED DELUGE AS A PYTHON PATH**

Shutdown uTorrent if it is running (script may not complete if a file from a torrent is in the "open" state. so close any media programs you may have open as well.)

Make sure deluge is running with CLASSIC MODE DISABLED. You can re-enable classic after the import.

Double click or use the command line to run the script.

Torrents will be added in the paused state and will then be set to do a recheck which may take a while.

The script will output a log of any torrents that could not be added successfully.

# Notes

The script assumes that your uTorrent resume.dat is in the default location of %APPDATA%\uTorrent. if this is not the case, you must either include the full path of resume.dat as the first argument to the script or drag and drop resume.dat onto the script file.

Do not run the script on a backup or moved copy of resume.dat. uTorrent uses relative paths when storing the resume data so the script uses the resume.dat path as a relative path to find the .torrent files. The script doesn't edit resume.dat, but if you're paranoid you can make a backup beforehand.

I didn't comment the code because I'm lazy (sorry). If you've got questions or concerns let me know and I can answer them or go back and do the comments if there's a demand for them.

# Linux

On Linux, the script first looks in the [WINE](https://www.winehq.org/) configuration (~/.wine/drive_c/users/$USER/Application Data/uTorrent/resume.dat), and then in the user home dir (~/uTorrent/resume.dat). Of course, you can always give any other path as an argument.

In case of WINE, the script will try to resolve drive letter mappings (defined in ~/.wine/dosdevices) and replace them with their real Linux paths. If you don't fancy that, just add the '--no-wine-mapping' argument.

Please note that this script was just tested with the Windows version of uTorrent 3.4 running within WINE - no idea how any other version behaves.