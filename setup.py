#
# setup.py
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

import ez_setup
ez_setup.use_setuptools()

from setuptools import setup

setup(
    author="Andrew Resch",
    author_email="andrewresch@gmail.com",
    description="Torrent Utilities",
    long_description="""A collection of utilities to create, modify, view and
    verify torrent metadata files""",
    entry_points="""
        [console_scripts]
            torrentmake = torrentutils.main:torrent_make
            torrentview = torrentutils.main:torrent_view
            torrentedit = torrentutils.main:torrent_edit
            torrentverify = torrentutils.main:torrent_verify
    """,
    license="GPLv3",
    name="torrentutils",
    packages=["torrentutils", "torrentutils.lib"],
    url="http://code.google.com/p/torrentutils",
    version="1.0"
)
