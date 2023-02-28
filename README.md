# Hot Shawarma
Hot Shawarma is a third-party remote control application for Roku smart devices and Roku smart TVs.

## Requirements
Hot Shawarma has been tested and confirmed to work on Ubuntu 18.04 64-bit or later, Mac 10.11.6 or later, and Windows 10 64-bit. It may work in other scenarios, but YMMV. On Windows you may need to install [Visual Studio Redistributable 2008](https://www.microsoft.com/en-us/download/confirmation.aspx?id=11895) from Microsoft.

## Installation (standalone)
You can obtain releases for GNU/Linux and Windows in the releases tab. Simply extract all of the contents to a folder and run the appropriate executable. Mac support is coming soon, but in the meantime you can just run the main HotShawarma.py file [directly from Python](https://www.python.org/downloads/mac-osx/) - contact us if you have questions about this.

## Uninstallation (standalone)
In addition to deleting the folder with the application, you may wish to remove your saved macros, their location is dependent on your operating system:

- For GNU/Linux: ``` /home/<your user name>/.local/share/Hot Shawarma ```
- For macOS and Mac OS X: ``` /Users/<your user name>/Library/Application Support/HotShawarma ```
- For Windows: ``` C:\Users\<your user name>\AppData\Local\Nemmy Games\Hot Shawarma ```

## Installation (packages)
I would very much like to distribute this application as a deb/rpm, in a personal package archive (PPA), a snap, etc. under GNU/Linux, but I have limited experience in these formats. Anyone who can contribute feel free to contact me.

## Licensing
Hot Shawarma is licensed under the terms of the GNU General Public License version 3. See the included gpl-3.0.txt file or https://www.gnu.org/licenses/gpl-3.0.en.html.




## How to set up macros
Hot Shawarma includes support for custom launchers - this can be as simple as launching a channel, but can get more complicated, for example executing actions after the channel has launched.

1. Choose an unset macro button, labeled “(none set)” and click on it.
2. Provide an optional short name in the first box.
3. Each step of the macro should be separated with a space.
4. For macros that require an argument, it should be directly after the letter or symbol. For example “a12” to launch Netflix.
5. The channel ID required for the “a” or “A” shortcut can be obtained by launching your channel from the channel list, or using your remote and reloading the current channel, then mouse-over the channel’s logo to get your channel ID, or look under the channel's icon.
5. Remember to add a delay after launching a channel (time varies) or initiating remote button presses (2 seconds is probably good). Also remember to not use your physical remote when running macros.

### Specific macro options:
* Use a capital A (as opposed to a lowercase a) to launch a channel and not wait for it to finish loading before moving on to the next step. For example A31012 works as a shortcut to the store from the menu, but because it’s not its own channel, it would freeze if you tried to launch it as a31012. Note that the capital “A” variant may not update the current channel, you may need to manually click the update button to see your current channel selection reflected in the application.
* On a smart TV if you’re using the digital tuner (shortcut key “~”) you can tune to a specific channel with for example “~2.2”.
* Changing input with the shortcut key “#” should be followed by a t for tuner (ie. #t) h followed by a number for hdmi (ie. #h1 for hdmi1) or a followed by a number for composite input (ie. a1)
* Volume can be controlled on a smart TV with “!+” and “!-” and channel (if you’re using digital TV) with “@+” and “@-”
* The Enter button (macro shortcut "t") can sometimes be used to complete a text entry field.

## Known issues
* If voice search does not work reliably or consistently for you, press (don't hold!) the voice search button on your remote first then press the voice button in the application.
* Macros do not self-validate.
* On Windows, Rokus may not be discovered if your computer is connected via Ethernet rather than Wifi, depending on the settings of your network. After connecting to Wifi, wait about thirty seconds and try discovering devices again.
* On some TVs you may need to enable “Fast TV start” (Settings > System > Power > Fast TV start), or turn your TV on manually before it’s recognized.
* If your device is plugged into your TV’s USB port I will likely not be recognized until your TV is turned on manually, as most TVs do not ship with USB ports that provide power when the TV is off. Consider plugging in via the power adapter.
* FindRemote may not work consistently, reliably, or at all yet. This is being investigated.
* If you have launched the YouTube channel via Cast from mobile, other channels may refuse to load (and indeed the application may appear to freeze) until you disconnect your mobile device.
* macOS buttons look wrong


## Reporting bugs
If you discover a reproducible bug, other than a known issue above, please report it and please include a debug log as well a detailed, clear, and concise description of the issue you encountered and under what conditions you encountered it.

* You can get one from Windows by running HotShawarma_debug.exe instead of the normal HotShawarma.exe.

* You can get one from GNU/Linux, macOS, and Mac OS X by running the program from terminal.

Copy the entire contents of the debug log to a text file and include it with your report.

## Future updates
I’m somewhat limited in what is available from Roku for me to use, that being said, there’s a few features I’d really like to add:

* Access to private listening mode

* A simple interface for sending keyboard text entry

If  you have any other feature requests report them under issues and tag them as ``` wishlist ```.

Be sure to check for updates every so often or if you experience a bug, it may have already been addressed.

## Contact and social
[![Twitter URL](https://img.shields.io/twitter/url/https/twitter.com/HotShawarmaApp.svg?style=social&label=Follow%20%40HotShawarmaApp)](https://twitter.com/HotShawarmaApp)


## F.A.Q.

### What’s a Shawarma?
[Wikipedia is your friend.](https://en.wikipedia.org/wiki/Shawarma)

### Why did you call it that?
Because it’s delicious, and it just feels right.

### Who is Seth?
How did you even find that?

