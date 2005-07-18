#!/usr/bin/python

import os, sys
import traceback
from mutagen.id3 import ID3

class Report(object):
    def __init__(self, pathname):
        self.name = pathname
        self.files = 0
        self.unsync = 0
        self.missings = 0
        self.errors = []
        self.exceptions = {}
        self.versions = {}

    def missing(self, filename):
        self.missings += 1
        self.files += 1

    def error(self, filename):
        Ex, value, trace = sys.exc_info()
        self.exceptions.setdefault(Ex, 0)
        self.exceptions[Ex] += 1
        self.errors.append((filename, Ex, value, trace))
        self.files += 1

    def success(self, id3):
        self.versions.setdefault(id3.version, 0)
        self.versions[id3.version] += 1
        self.files += 1
        if id3.f_unsynch: self.unsync += 1

    def __str__(self):
        strings = ["-- Report for %s --" % self.name]
        if self.files == 0:
            return strings[0] + "\n" + "No MP3 files found.\n"
        
        good = self.files - len(self.errors)
        strings.append("Loaded %d/%d files (%d%%)" % (
            good, self.files, (float(good)/self.files) * 100))
        strings.append("%d files with unsynchronized frames." % self.unsync)
        strings.append("%d files without tags." % self.missings)

        strings.append("\nID3 Versions:")
        items = self.versions.items(); items.sort()
        for v,i in items:
            strings.append("  %s\t%d" % (".".join(map(str, v)), i))

        if self.exceptions:
            strings.append("\nExceptions:")
            items = self.exceptions.items(); items.sort()
            for Ex, i in items:
                strings.append("  %-20s\t%d" % (Ex.__name__, i))

        if self.errors:
            strings.append("\nERRORS:\n")
            for filename, Ex, value, trace in self.errors:
                strings.append("\nReading %s:" % filename)
                strings.append("".join(traceback.format_exception(Ex, value, trace)[1:]))
        else: strings.append("\nNo errors!")

        return "\n".join(strings)

def check_dir(path):
    from traceback import print_exc
    from mutagen.id3 import ID3NoHeaderError, ID3UnsupportedVersionError
    rep = Report(path)
    print "Scanning", path
    for path, dirs, files in os.walk(path):
        for fn in files:
            if not fn.lower().endswith('.mp3'): continue
            ffn = os.path.join(path, fn)
            try:
                id3 = ID3()
                id3.PEDANTIC = False
                id3.load(ffn)
            except KeyboardInterrupt: raise
            except ID3NoHeaderError: rep.missing(ffn)
            except Exception, err: rep.error(ffn)
            else: rep.success(id3)

    print str(rep)

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1: print "Usage: %s directory ..." % sys.argv[0]
    else:
        for path in sys.argv[1:]: check_dir(path)
