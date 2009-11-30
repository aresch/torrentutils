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

from __future__ import division

import sys
from optparse import OptionParser

import pkg_resources

from .lib import metadata

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

def fsize(fsize_b):
    """
    Formats the bytes value into a string with KiB, MiB or GiB units

    :param fsize_b: the filesize in bytes
    :type fsize_b: int
    :returns: formatted string in KiB, MiB or GiB units
    :rtype: string

    **Usage**

    >>> fsize(112245)
    '109.6 KiB'

    """
    fsize_kb = fsize_b / 1024.0
    if fsize_kb < 1024:
        return "%.1f KiB" % fsize_kb
    fsize_mb = fsize_kb / 1024.0
    if fsize_mb < 1024:
        return "%.1f MiB" % fsize_mb
    fsize_gb = fsize_mb / 1024.0
    return "%.1f GiB" % fsize_gb

def torrent_make():
    usage = "%prog [options] source target"

    # Setup the argument parser
    parser = OptionParser(usage=usage, version="%prog (torrentutils) " + version)
    parser.add_option(
        "-s", "--piece-size", dest="piece_size", action="store", type="int",
        help=pretty_docstring(metadata.TorrentMetadata.piece_size.__doc__)
    )
    parser.add_option(
        "-p", "--pad-files", dest="pad_files", action="store_true", default=False,
        help=pretty_docstring(metadata.TorrentMetadata.pad_files.__doc__)
    )
    parser.add_option(
        "-c", "--comment", dest="comment", action="store", type="string",
        help=pretty_docstring(metadata.TorrentMetadata.comment.__doc__)
    )
    parser.add_option(
        "-P", "--private", dest="private", action="store_true", default=False,
        help=pretty_docstring(metadata.TorrentMetadata.private.__doc__)
    )
    parser.add_option(
        "-t", "--tracker", dest="tracker", action="append", type="string",
        help="To specify more than one tracker just add as many -t options as necessary."
    )
    parser.add_option(
        "-w", "--webseeds", dest="webseed", action="append", type="string",
        help=pretty_docstring(metadata.TorrentMetadata.webseeds.__doc__ +\
        "To specify more than one webseed just add as many -w options as necessary."
        )
    )
    parser.add_option(
        "-n", "--name", dest="name", action="store", type="string",
        help=pretty_docstring(metadata.TorrentMetadata.name.__doc__)
    )
    parser.add_option(
        "-q", "--quiet", dest="quiet", action="store_true", default=False,
        help="Do not print out progress or any status."
    )

    # Get the options and args from the OptionParser
    (options, args) = parser.parse_args()

    if len(args) < 2:
        parser.print_help()
        sys.exit(0)

    md = metadata.TorrentMetadata()
    md.data_path = args[0]

    for option, value in options.__dict__.items():
        if value and hasattr(md, option):
            setattr(md, option, value)

    def progress(completed, num_pieces):
        ratio = completed / num_pieces
        cols = 60
        blocks = int(round((cols - 2) * ratio))
        sys.stdout.write("Percent: %.2f%% Pieces: %s/%s  [" % (ratio*100, completed, num_pieces)\
         + "#" * blocks + "~" * (cols - 2 - blocks) + "]\r")
        if completed == num_pieces:
            print("\n")

    md.save(args[1], None if options.quiet else progress)

def torrent_view():
    usage = "%prog [options] source"

    # Setup the argument parser
    parser = OptionParser(usage=usage, version="%prog (torrentutils) " + version)

     # Get the options and args from the OptionParser
    (options, args) = parser.parse_args()

    if len(args) < 1:
        parser.print_help()
        sys.exit(0)

    for arg in args:
        md = metadata.TorrentMetadata()
        md.load(arg)
        print("Name: %s" % md.name)
        print("Info-hash: %s" % md.info_hash)
        print("Piece Size: %s" % fsize(md.piece_size))
        if md.comment:
            print("Comment: %s" % md.comment)
        print("Private: %s" % md.private)
        print("Pad Files: %s" % md.pad_files)
        if md.trackers:
            print("Trackers:")
            for index, tier in enumerate(md.trackers):
                print("  Tier %s:" % index)
                for tracker in tier:
                    print("    %s" % tracker)

        if md.webseeds:
            print("Webseeds:")
            for webseed in md.webseeds:
                print("  %s" % webseed)

        print("Files:")
        for filename, size in md.files:
            print("  %s | %s" % (fsize(size), filename))

def torrent_edit():
    pass

def torrent_verify():
    pass
