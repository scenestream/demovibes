# -*- coding: utf-8 -*-

import os
import subprocess

from django.conf import settings
import logging

log = logging.getLogger("dv.prelisten")


class Prelisten(object):
    REL_URL = 'media/music/prelisten/'

    def __init__(self, file_path, song_id):
        self.file_path = file_path
        self.id = song_id
        self.prelisten_dir = \
            os.path.join(getattr(settings, 'MEDIA_ROOT', False)
                         + Prelisten.REL_URL)

    def url(self):
        return os.path.join('/' + Prelisten.REL_URL, str(self.id) + '.mp3')

    def path(self):
        return os.path.join(self.prelisten_dir, str(self.id) + '.mp3')

    def exists(self):
        # This is a hack so that the templates can avoid showing a dead player
        # if the prelisten file hasn't been generated yet
        return os.path.isfile(self.path())

    def ensure_prelisten(self):
        # Prelisten files will be stored in a prelisten dir; we can use a
        # cron job to periodically purge it.
        flag_path = self.prelisten_dir + str(self.id) + ".enc"

        # Check if the prelisten file already exists, or is in progress.
        if self.exists() or os.path.isfile(flag_path):
            return

        mp3_path = self.path()
        unused_filename, file_ext = os.path.splitext(self.file_path)
        # If the file is already an mp3, make a symlink instead.
        if file_ext == '.mp3':
            os.symlink(self.file_path, mp3_path)
            return

        # Otherwise use dscan and lame to create one.
        # First create a 'flag' file that says encoding is in progress.
        open(flag_path, 'a').close()

        dscan = getattr(settings, 'DEMOSAUCE_SCAN', False)
        lame = getattr(settings, 'LAME', "/usr/bin/lame")
        wav_path = self.prelisten_dir + str(self.id) + ".wav"

        ret = subprocess.call([dscan, "-o", wav_path, self.file_path])
        if ret != 0:
            log.debug("Could not dscan %s to %s: %s"
                      % (self.file_path, wav_path, "some reason"))
            return

        ret = subprocess.call([lame, "-S", wav_path, mp3_path])
        if ret != 0:
            log.debug("Could not lame %s to %s: %s"
                      % (wav_path, mp3_path, "some reason"))
            return

        os.unlink(wav_path)
        os.unlink(flag_path)

        log.debug("Created prelisten file for %s at %s."
                  % (self.file_path, mp3_path))
