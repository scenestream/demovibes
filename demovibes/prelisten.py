# -*- coding: utf-8 -*-

import os
import subprocess

from django.conf import settings
import logging

log = logging.getLogger("dv.prelisten")


class Prelisten(object):
    def __init__(self, file_path, song_id):
        self.file_path = file_path
        self.id = song_id
        self.prelisten_dir = \
            os.path.join(getattr(settings, 'MEDIA_ROOT', False)
                         + 'media/music/prelisten/')

    def path(self):
        return os.path.join(self.prelisten_dir, str(self.id) + '.mp3')

    def ensure_prelisten(self):
        filename, file_ext = os.path.splitext(self.file_path)
        #  Prelisten files will be stored to a prelisten dir; we can use a cron job to peridically purge it
        wav_path = self.prelisten_dir + str(self.id) + ".wav"
        mp3_path = self.path()
        flag_path = self.prelisten_dir + str(self.id) + ".enc"
        # check if the prelisten file already exists, or is in progress
        if os.path.isfile(mp3_path) or os.path.isfile(flag_path):
          return
        # if the file is already an mp3, make a symlink instead
        if file_ext == '.mp3':
            os.symlink(self.file_path, mp3_path)
            return
        # otherwise use dscan and lame to create one
        # first create a 'flag' file that says encoding is in progress
        # the view checks for this to avoid launching multiple encoding threads for the same file
        open(flag_path, 'a').close()
        dscan = getattr(settings, 'DEMOSAUCE_SCAN', False)
        lame = getattr(settings, 'LAME', "/usr/bin/lame")
        ret = subprocess.call([dscan, "-o", wav_path, self.file_path])
        if ret != 0:
            log.debug("Could not dscan %s to %s: %s" % (self.file_path, wav_path, "some reason"))
            return
        ret = subprocess.call([lame, "-S", wav_path, mp3_path])
        if ret != 0:
            log.debug("Could not lame %s to %s: %s" % (wav_path, mp3_path, "some reason"))
            return
        os.unlink(wav_path)
        os.unlink(flag_path)
        log.debug("Created prelisten file for %s at %s." % (self.file_path, mp3_path))

    def has_prelisten(self):
        # This is a hack so that the templates can avoid showing a dead player if the prelisten file hasn't been generated yet
        if os.path.isfile(self.path()):
            return True
        return False
