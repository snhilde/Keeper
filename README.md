# Keeper
Working clone of Google Keep for Linux

# Table of Contents
* [Installation](#installation)
* [Prerequisites](#prerequisites)
* [Build Details](#build-details)
* [Getting Started](#getting-started)
* [Usage](#usage)
* [Future Additions](#future-additions)
* [Contributing](#contributing)
* [Author](#author)
* [License](#license)


## Installation
To download through GitHub:
* `git clone https://github.com/snhilde/keeper`

Otherwise:
* download the zip
* open the archive with `unzip path/to/file.zip`

To install and run the program:
* if using Linux, copy the [executable](#build-details) to a folder within your PATH.
* for other systems, you will need to build the executable yourself. Once you have the prerequisites(#prerequisites) in place, run
```
pyinstaller --onefile /path/to/main.py
```
In the build files, look in the `dist` subdirectory for the executable. Move it to somewhere within your PATH.

## Prerequisites
Keeper uses Beautiful Soup 4 to import your notes from Google Keep. To install
this library, run this command in your terminal:
```
pip install beautifulsoup4
```
For the GUI, Keeper uses tkinter bindings. This library should come with your
default installation.

Keeper also uses these standard libraries:
* typing
* glob
* os
* re
* time

To build your own executable, you will need PyInstaller:
```
pip install pyinstaller
```

## Build Details
The included executable was built on this system:
* Linux 4.18.9
* Arch Linux current as of 09/12/2018
* Python 3.7.0
* Beautiful Soup 4.6.3
* PyInstaller 3.4

## Getting Started
If you want to import notes from Google Keep, then you first have to visit [Google Takeout](https://takeout.google.com). Select Keep from the options, download your archive, and unpack it. To import the notes into Keeper, select everything you want within the program. Keeper will do the rest.

## Usage
* To add notes, click the '+' button on the bottom right corner.
* To import notes, click the 'import' button in the same area.
* To delete notes, right-click on the note and confirm the dialog.
* To modify a note, click on it and edit the title (top) and/or body (bottom). When done, click on the '<-' back button at the top left or press 'Escape'. Everything is saved automatically.

## Future Additions
* Add functionality for lists, checkboxes, etc.
* Add ability to save images, hypertext links, charts, and other graphics.
* Change title and body text comparision in EditText to hash rather than byte-by-byte string.

## Contributing
Send a pull request or a message. Additional functionality is welcome, as are suggestions to make the program leaner, faster, and better performing.

## Author
Hilde N

## License
This project is licensed under the MIT License. Do whatever you want with it. See the [LICENSE](LICENSE) file for details
