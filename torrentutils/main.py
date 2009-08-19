#
# main.py
#
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA    02110-1301, USA.
#

import sys
from optparse import OptionParser

import pkg_resources

version = pkg_resources.require("torrentutils")[0].version

def pretty_docstring(s):
    """
    Make a docstring look better when printed.
    """
    s = s.replace("\n", "")
    s = s.strip()
    while "  " in s:
        s = s.replace("  ", " ")
    return s

def torrent_make():
    from .lib import maketorrent

    usage = "%prog [options] source target"

    # Setup the argument parser
    parser = OptionParser(usage=usage, version="%prog (torrentutils) " + version)
    parser.add_option(
        "-s", "--piece-size", dest="piece_size", action="store", type="int",
        help=pretty_docstring(maketorrent.TorrentMetadata.piece_size.__doc__)
    )
    parser.add_option(
        "-p", "--pad-files", dest="pad_files", action="store_true", default=False,
        help=pretty_docstring(maketorrent.TorrentMetadata.pad_files.__doc__)
    )
    parser.add_option(
        "-c", "--comment", dest="comment", action="store", type="string",
        help=pretty_docstring(maketorrent.TorrentMetadata.comment.__doc__)
    )
    parser.add_option(
        "-P", "--private", dest="private", action="store_true", default=False,
        help=pretty_docstring(maketorrent.TorrentMetadata.private.__doc__)
    )
    parser.add_option(
        "-t", "--tracker", dest="tracker", action="append", type="string",
        help="To specify more than one tracker just add as many -t options as necessary."
    )
    parser.add_option(
        "-w", "--webseeds", dest="webseed", action="append", type="string",
        help=pretty_docstring(maketorrent.TorrentMetadata.webseeds.__doc__ +\
        "To specify more than one webseed just add as many -w options as necessary."
        )
    )

    # Get the options and args from the OptionParser
    (options, args) = parser.parse_args()

    if len(args) < 2:
        parser.print_help()
        sys.exit(0)

    md = maketorrent.TorrentMetadata()
    md.data_path = args[0]

    for option, value in options.__dict__.items():
        if value:
            setattr(md, option, value)

    md.save(args[1])

def torrent_view():
    pass

def torrent_edit():
    pass

def torrent_verify():
    pass
