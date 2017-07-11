#!/usr/bin/python
# -*- coding: utf-8 -*-
"""ShapeOut - session index handling"""
from __future__ import division, print_function, unicode_literals

from distutils.version import LooseVersion
import copy
import io
import os
from os.path import abspath, basename, join, isdir
import warnings


from .._version import version


def find_data_path(index_item,
                   search_path="./",
                   errors="ignore"):
    """Get the measurement file from entries of an index dictionary
    
    Parameters
    ----------
    index_item: dict
        An index item of one measurement
    search_path: str
        Path to search for the data path
    errors: str
        If the file cannot be found on the file system, then a warning
        is issued if `errors` is set to "ignore", otherwise an IOError
        is raised.
    
    The index dictionary is created for each entry in the
    the index.txt file and contains the keys "name", "fdir", and
    since version 0.6.1 "rdir".
    """
    item = copy.copy(index_item)
    found = False
    
    mfile1 = join(item["fdir"], item["name"])
    
    if os.path.exists(mfile1):
        found = mfile1
    else:
        if "rdir" not in item:
            item["rdir"] = "."
        search_paths = [search_path, item["rdir"]]
        # Also search in base directory of "fdir"
        if item["fdir"].count("\\"):
            # Workaround to get basename for files saved
            # with Windows.
            fbase = item["fdir"].rsplit("\\", 1)[1]
        else:
            fbase = basename(item["fdir"])
        for sp in search_paths:
            # try to find relative path
            dira = abspath(join(abspath(sp), item["rdir"]))
            dirb = abspath(join(dira, fbase))
            mfile2a = join(dira, item["name"])
            mfile2b = join(dirb, item["name"])

            if os.path.exists(mfile2a):
                found = mfile2a
                break
            elif os.path.exists(mfile2b):
                found = mfile2b
                break

    if not found:
        if errors == "ignore":
            warnings.warn("Could not find file: {}".format(mfile1))
            found = mfile1
        else:
            raise IOError("Could not find file: {}".format(mfile1))

    return found



def index_check(index_file, search_path="./"):
    """Check a session file index for existence of all measurement files"""
    if isdir(index_file):
        index_file = join(index_file, "index.txt")
    missing_files = []
    
    index_dict = index_load(index_file)
    keys = list(index_dict.keys())
    # The identifier (in brackets []) contains a number before the first
    # underscore "_" which determines the order of the plots:
    keys.sort(key=lambda x: int(x.split("_")[0]))
    for key in keys:    
        item = index_dict[key]
        if not ("special type" in item and
                item["special type"] == "hierarchy child"):
            mfile = find_data_path(item, search_path)
            if not os.path.exists(mfile):
                missing_files.append([key, mfile, item])
    
    messages = {"missing files": missing_files}
    return messages


def index_load(index_file):
    """Load an index file
    
    Parameters
    ----------
    index_file: str
        Path to the index file or folder containing "index.txt".
    
    Returns
    -------
    index_dict: dict
        Dictionary containing all index information
    """
    cfg = {}

    if isdir(index_file):
        index_file = join(index_file, "index.txt")
    with io.open(index_file, 'r') as f:
        code = f.readlines()
    
    for line in code:
        # We deal with comments and empty lines
        # We need to check line length first and then we look for
        # a hash.
        line = line.split("#")[0].strip()
        if len(line):
            if line.startswith("[") and line.endswith("]"):
                section = line[1:-1]
                if not section in cfg:
                    cfg[section] = {}
                continue
            var, val = line.split("=", 1)
            var, val = var.strip(), val.strip()
            if len(var) != 0 and len(str(val)) != 0:
                cfg[section][var] = val

    return cfg


def index_save(index_file, index_dict):
    """Save index dictionary to a file

    Parameters
    ----------
    index_file: str
        Path to index file or folder
    index_dict : dict
        Index dictionary
    """
    if isdir(index_file):
        index_file = join(index_file, "index.txt")
    out = ["# ShapeOut measurement index",
           "# Software version {}".format(version)
           ]
    keys = list(index_dict.keys())
    keys.sort()
    for key in keys:
        out.append("[{}]".format(key))
        section = index_dict[key]
        ikeys = list(section.keys())
        ikeys.sort()
        for ikey in ikeys:
            out.append("{} = {}".format(ikey,section[ikey]))
        out.append("")
    
    with io.open(index_file, "w") as f:
        for i in range(len(out)):
            out[i] = out[i]+"\r\n"
        f.writelines(out)


def index_update(index_file, index_dict):
    """Update an index file with new entries"""
    datadict = index_load(index_file)
    for key in index_dict:
        datadict[key].update(index_dict[key])
    index_save(index_file, datadict)


def index_version(index_file):
    """Obtain the ShapeOut version used to save an index
    
    Parameters
    ----------
    path: str
        Path to an index file or a directory containting "index.txt".

    Returns
    -------
    version: disturils.version.LooseVersion
        The version used
        
    Notes
    -----
    Sessions saved with ShapeOut prior to version 0.7.6 did not
    save the version in the session file and the version is set
    to "0.0.1".
    """
    if isdir(index_file):
        index_file = join(index_file, "index.txt")
    # Obtain version of session
    with io.open(index_file, "r") as fd:
        data = fd.readlines()
    
    vline = data[1].lower().strip()
    if vline.count("software version"):
        vers = LooseVersion(vline.split()[-1])
    else:
        vers = LooseVersion("0.0.1")
    return vers
    