# -*- coding: utf-8 -*-

import hashlib
import os
import subprocess
import thread

from django.conf import settings
import logging

log = logging.getLogger("dv.prelisten")


class Prelisten(object):
    REL_URL = 'media/prelisten/'
    dir = os.path.join(getattr(settings, 'MEDIA_ROOT', False) + REL_URL)
    root_dir_exists = os.path.isdir(dir)

    has_encoder = False
    try:
        subprocess.call('lame', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        has_encoder = True
    except:  # Bare excepts not encouraged but we really want to catch all!
        pass

    def __init__(self, file_path):
        self.file_path = file_path
        self.is_valid = (Prelisten.root_dir_exists
                         and Prelisten.has_encoder
                         and (not not self.file_path)
                         and os.path.isfile(self.file_path))

    def valid(self):
        return self.is_valid

    def busy(self):
        return os.path.isfile(self.flag_path())

    def hash(self):
        hash_object = hashlib.md5(self.file_path)
        return hash_object.hexdigest()

    def url(self):
        return os.path.join('/' + Prelisten.REL_URL, self.hash() + '.mp3')

    def path(self, extension='.mp3'):
        return os.path.join(Prelisten.dir, self.hash() + extension)

    def flag_path(self):
        return self.path('.enc')

    def exists(self):
        if not self.valid():
            return False

        return os.path.isfile(self.path())

    def generate(self):
        """
        Generates a prelisten file if needed.

        Returns True if already available, False otherwise.

        The return value is used by templates to either show an audio player
        or a message while a prelisten file is being generated.
        """

        if not self.valid():
            return False

        # Prelisten files will be stored in a prelisten dir; we can use a
        # cron job to periodically purge it.

        # Check if the prelisten file is in progress...
        if self.busy():
            return False

        # ... or already exists.
        if self.exists():
            return True

        unused_filename, file_ext = os.path.splitext(self.file_path)
        # If the file is already an mp3, make a symlink instead.
        if file_ext in ['.mp3', '.MP3']:
            os.symlink(self.file_path, self.path())
            return True

        # Otherwise first create a 'flag' file that says encoding is in
        # progress...
        open(self.flag_path(), 'a').close()

        # ... and use dscan and LAME to create a prelistening file in a thread.
        thread.start_new_thread(self.do_create, ())
        return False

    def do_create(self):
        dscan = getattr(settings, 'DEMOSAUCE_SCAN', False)
        lame = getattr(settings, 'LAME', "/usr/bin/lame")
        wav_path = self.path('.wav')

        ret = subprocess.call([dscan, "-o", wav_path, self.file_path])
        if ret != 0:
            log.debug("Could not dscan %s to %s: %s"
                      % (self.file_path, wav_path, "some reason"))
            return

        mp3_path = self.path()
        encoding_path = mp3_path + '.encoding'
        ret = subprocess.call([lame, '-S', '--preset', 'standard',
                               wav_path, encoding_path])

        ok = (ret == 0)
        if ok:
            os.rename(encoding_path, mp3_path)
            os.unlink(self.flag_path())

        os.unlink(wav_path)

        if ok:
            log.debug("Created prelisten file for %s at %s."
                      % (self.file_path, mp3_path))
        else:
            log.debug("Could not lame %s to %s: %s"
                      % (wav_path, encoding_path, "some reason"))
