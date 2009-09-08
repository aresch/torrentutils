#
# metadata.py
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
import os
from hashlib import sha1 as sha

from bencode import bencode, bdecode

def get_path_size(path):
    """
    Gets the size in bytes of 'path'

    :param path: the path to check for size
    :type path: string
    :returns: the size in bytes of the path
    :rtype: int

    :raises InvalidPath: if the path does not exist

    """
    if not os.path.exists(path):
        raise InvalidPath("%s is an invalid path" % path)

    if os.path.isfile(path):
        return os.path.getsize(path)

    dir_size = 0
    for (p, dirs, files) in os.walk(path):
        for file in files:
            filename = os.path.join(p, file)
            dir_size += os.path.getsize(filename)
    return dir_size

class InvalidPath(Exception):
    """
    Raised when an invalid path is supplied
    """
    pass

class InvalidPieceSize(Exception):
    """
    Raised when an invalid piece size is set.  Piece sizes must be multiples of
    16KiB.
    """
    pass

class InvalidBencoding(Exception):
    """
    Raised when trying to bdecode invalid data.
    """
    pass

class TorrentMetadata(object):
    """
    This class is used to create or modify .torrent files.

    ** Usage **

    >>> t = TorrentMetadata()
    >>> t.data_path = "/tmp/torrent"
    >>> t.comment = "My Test Torrent"
    >>> t.trackers = [["http://tracker.openbittorent.com"]]
    >>> t.save("/tmp/test.torrent")

    """
    def __init__(self):
        self.__piece_size = 0
        self.__comment = ""
        self.__private = False
        self.__trackers = []
        self.__webseeds = []
        self.__pad_files = False
        self.__data_path = None
        self.__name = ""
        # [(path, size), ...]
        self.__files = []
        # The pieces hash string, this will only be set after a load() or save()
        self.__pieces_hash = ""
        # Only set after a load() or save()
        self.__info_hash = ""

    def load(self, filename):
        """
        Load metadata from a .torrent file.  This is useful if you want to view
        or modify existing metadata.

        :param filename: the .torrent file to load
        :type filename: string

        :raises InvalidPath: if the `filename` does not exist
        :raises InvalidBencoding: if the `filename` does not contain valid
        bencoded data.

        """
        if not os.path.exists(filename):
            raise InvalidPath("The file %s does not exist!" % filename)

        try:
            md = bdecode(open(filename, "rb").read())
        except Exception, e:
            raise InvalidBencoding("The file %s contains invalid data." % filename)

        # Set the properties
        if "comment" in md:
            self.comment = md["comment"]

        if "private" in md["info"] and md["info"]["private"]:
            self.private = True

        if "announce-list" in md:
            self.trackers = md["announce-list"]
        elif "announce" in md:
            self.trackers = [[md["announce"]]]

        webseeds = []
        if "httpseeds" in md:
            webseeds = md["httpseeds"]
        if "url-list" in md:
            webseeds += md["url-list"]
        if webseeds:
            self.webseeds = webseeds

        self.piece_size = md["info"]["piece length"]

        if "name" in md["info"]:
            self.name = md["info"]["name"]

        if "length" in md["info"]:
            # We're dealing with a single file
            self.__files = [(md["info"]["name"], md["info"]["length"])]
        else:
            # Multi-file torrent
            self.__files = []
            for fd in md["info"]["files"]:
                if "/".join(fd["path"]).startswith("_____padding_file_") or ("attr" in fd and "p" in fd["attr"]):
                    # This is a padding file, so lets not display it but set the
                    # pad_files property True
                    self.pad_files = True
                else:
                    # Regular file, so add it to the list
                    self.__files.append(("/".join(fd["path"]), fd["length"]))

        self.__info_hash = sha(bencode(md["info"])).hexdigest()

    def save(self, torrent_path, progress=None):
        """
        Creates and saves the torrent file to `torrent_path`.

        :param torrent_path: where to save the torrent file
        :type torrent_path: string

        :param progress: a function to be called when a piece is hashed
        :type progress: function(num_completed, num_pieces)

        :raises InvalidPath: if the data path has not been set

        """
        if not self.data_path or len(self.__files) < 1:
            raise InvalidPath("Need to set a data path!")

        torrent = {
            "info": {}
            }

        if self.comment:
            torrent["comment"] = self.comment.encode("UTF-8")

        if self.private:
            torrent["info"]["private"] = True

        if self.trackers:
            torrent["announce"] = self.trackers[0][0]
            torrent["announce-list"] = self.trackers
        else:
            torrent["announce"] = ""

        if self.webseeds:
            httpseeds = []
            webseeds = []
            for w in self.webseeds:
                if w.endswith(".php"):
                    httpseeds.append(w)
                else:
                    webseeds.append(w)

            if httpseeds:
                torrent["httpseeds"] = httpseeds
            if webseeds:
                torrent["url-list"] = webseeds

        datasize = sum([x[1] for x in self.__files])

        if self.piece_size:
            piece_size = piece_size * 1024
        else:
            # We need to calculate a piece size
            piece_size = 16384
            while (datasize / piece_size) > 1024 and piece_size < (8192 * 1024):
                piece_size *= 2

        # Calculate the number of pieces we will require for the data
        num_pieces = datasize / piece_size
        if datasize % piece_size:
            num_pieces += 1

        torrent["info"]["piece length"] = piece_size

        # Create the info
        if len(self.__files) > 1:
            torrent["info"]["name"] = os.path.basename(self.data_path)
            files = []
            padding_count = 0
            # Collect a list of file paths and add padding files if necessary
            for index, (path, size) in enumerate(self.__files):
                head, tail = os.path.split(self.data_path)
                if tail:
                    p = path.replace(tail, "", 1)
                else:
                    p = path.replace(head, "", 1)

                p = p.lstrip("/")
                p = p.split("/")
                files.append((size, p))
                # Add a padding file if necessary
                if self.pad_files and (index + 1) < len(self.__files):
                    left = size % piece_size
                    if left:
                        p = list(p)
                        p[-1] = "_____padding_file_" + str(padding_count)
                        files.append((piece_size - left, p))
                        padding_count += 1

            # Run the progress function with 0 completed pieces
            if progress:
                progress(0, num_pieces)

            fs = []
            pieces = []
            # Create the piece hashes
            buf = ""
            for size, path in files:
                path = [s.decode(sys.getfilesystemencoding()).encode("UTF-8") for s in path]
                fs.append({"length": size, "path": path})
                if path[-1].startswith("_____padding_file_"):
                    buf += "\0" * size
                    pieces.append(sha(buf).digest())
                    buf = ""
                    fs[-1]["attr"] = "p"
                else:
                    fd = open(os.path.join(self.data_path, *path), "rb")
                    r = fd.read(piece_size - len(buf))
                    while r:
                        buf += r
                        if len(buf) == piece_size:
                            pieces.append(sha(buf).digest())
                            # Run the progress function if necessary
                            if progress:
                                progress(len(pieces), num_pieces)
                            buf = ""
                        else:
                            break
                        r = fd.read(piece_size - len(buf))
                    fd.close()

            if buf:
                pieces.append(sha(buf).digest())
                if progress:
                    progress(len(pieces), num_pieces)
                buf = ""

            torrent["info"]["pieces"] = "".join(pieces)
            torrent["info"]["files"] = fs

        elif len(self.__files) == 1:
            torrent["info"]["name"] = self.__files[0][0]
            abspath = os.path.join(os.path.dirname(self.data_path), self.__files[0][0])
            torrent["info"]["length"] = get_path_size(abspath)
            pieces = []

            fd = open(abspath, "rb")
            r = fd.read(piece_size)
            while r:
                pieces.append(sha(r).digest())
                if progress:
                    progress(len(pieces), num_pieces)

                r = fd.read(piece_size)

            torrent["info"]["pieces"] = "".join(pieces)

        # Write out the torrent file
        open(torrent_path, "wb").write(bencode(torrent))


    def get_data_path(self):
        """
        Get the current path to the data source.
        """
        return self.__data_path

    def set_data_path(self, path):
        """
        Set a data path for the torrent.  When you `:meth:save` the metadata
        a set of piece hashes will be created for the data contained in the files.

        :param path: the path to the data you wish to add, this can be a file or
        folder.  If the path is a folder, it will add all files recursively.
        :type path: string

        :raises InvalidPath: if the `path` does not exist or if it's not a file
        or folder.

        """
        if not os.path.exists(path):
            raise InvalidPath("The path %s does not exist!" % path)

        if os.path.isdir(path):
            self.__data_path = os.path.abspath(path)
            self.__files = []
            for (dirpath, dirnames, filenames) in os.walk(path):
                for filename in filenames:
                    abspath = os.path.join(os.path.dirname(os.path.abspath(path)), dirpath, filename)
                    self.__files.append((os.path.join(dirpath, filename), get_path_size(abspath)))

        elif os.path.isfile(path):
            self.__data_path = os.path.abspath(path)
            self.__files = [(path, get_path_size(os.path.abspath(path)))]
        else:
            raise InvalidPath("The path %s is not a file or folder!" % path)

        # Reset the pieces hash and info hash if set since they are no longer
        # valid
        self.__pieces_hash = ""
        self.__info_hash = ""

    def remove_file(self, index):
        """
        Remove a file from the torrent.

        :param index: the file index
        :type path: int

        :raises KeyError: if the index is invalid

        """
        if index < 0 or index > (len(self.__files) - 1):
            raise KeyError("File index %s is invalid!" % index)

        self.__files.remove(index)

        # Reset the pieces hash and info hash if set since they are no longer
        # valid
        self.__pieces_hash = ""
        self.__info_hash = ""

    def get_piece_size(self):
        """
        The size of pieces in KiBs.  The size must be a multiple of 16.
        If you don't set a piece size, one will be automatically selected to
        produce a torrent with less than 1024 pieces or the smallest possible
        with a 8192KiB piece size.

        """
        return self.__piece_size

    def set_piece_size(self, size):
        """
        :param size: the desired piece size in KiBs
        :type size: int

        :raises InvalidPieceSize: if the piece size is not a multiple of 16 KiB

        """
        if size % 16 and size:
            raise InvalidPieceSize("Piece size must be a multiple of 16 KiB")
        self.__piece_size = size

    def get_comment(self):
        """
        Comment is some extra info to be stored in the torrent.  This is
        typically an informational string.
        """
        return self.__comment

    def set_comment(self, comment):
        """
        :param comment: an informational string
        :type comment: string
        """
        self.__comment = comment

    def get_private(self):
        """
        Private torrents only announce to the tracker and will not use DHT or
        Peer Exchange.

        See: http://bittorrent.org/beps/bep_0027.html

        """
        return self.__private

    def set_private(self, private):
        """
        :param private: True if the torrent is to be private
        :type private: bool
        """
        self.__private = private

    def get_trackers(self):
        """
        The announce trackers is a list of lists.

        See: http://bittorrent.org/beps/bep_0012.html

        """
        return self.__trackers

    def set_trackers(self, trackers):
        """
        :param trackers: a list of lists of trackers, each list is a tier
        :type trackers: list of list of strings
        """
        self.__trackers = trackers

    def get_webseeds(self):
        """
        The web seeds can either be:
        Hoffman-style: http://bittorrent.org/beps/bep_0017.html
        or,
        GetRight-style: http://bittorrent.org/beps/bep_0019.html

        If the url ends in '.php' then it will be considered Hoffman-style, if
        not it will be considered GetRight-style.
        """
        return self.__webseeds

    def set_webseeds(self, webseeds):
        """
        :param webseeds: the webseeds which can be either Hoffman or GetRight style
        :type webseeds: list of urls
        """
        self.__webseeds = webseeds

    def get_pad_files(self):
        """
        If this is True, padding files will be added to align files on piece
        boundaries.
        """
        return self.__pad_files

    def set_pad_files(self, pad):
        """
        :param pad: set True to align files on piece boundaries
        :type pad: bool
        """
        self.__pad_files = pad

    def get_name(self):
        """
        In a single file torrent, this is the name of the file and in a multi-file
        torrent, it is the name of the directory.
        """
        return self.__name

    def set_name(self, name):
        """
        :param name: the name to use in the info dictionary
        :type name: string

        """
        self.__name = name

    def get_info_hash(self):
        """
        The info-hash of the torrent.  This is a SHA hash of the info dictionary
        of the torrent and will only be available after a load() or save().  If
        the info dictionary is modified after load/save, the info-hash will be
        discarded.

        :returns: the info-hash
        :rtype: string

        """
        return self.__info_hash

    def get_files(self):
        """
        A list of files in the torrent.  This will only have a list of files after
        either a `:meth:set_data_path` operation or a `:meth:load`.

        :returns: a list of files and their lengths
        :rtype: list of 2-tuple(file, length)

        """
        return self.__files

    piece_size = property(get_piece_size, set_piece_size)
    comment = property(get_comment, set_comment)
    private = property(get_private, set_private)
    trackers = property(get_trackers, set_trackers)
    webseeds = property(get_webseeds, set_webseeds)
    pad_files = property(get_pad_files, set_pad_files)
    data_path = property(get_data_path, set_data_path)
    name = property(get_name, set_name)
    info_hash = property(get_info_hash)
    files = property(get_files)
