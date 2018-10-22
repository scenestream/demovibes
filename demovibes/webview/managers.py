from django.db import models, connection
from django.db.models.fields import FieldDoesNotExist

class LockingManager(models.Manager):
    """ Add lock/unlock functionality to manager.

    Example::

        class Job(models.Model):

            manager = LockingManager()

            counter = models.IntegerField(null=True, default=0)

            @staticmethod
            def do_atomic_update(job_id)
                ''' Updates job integer, keeping it below 5 '''
                try:
                    # Ensure only one HTTP request can do this update at once.
                    Job.objects.lock()

                    job = Job.object.get(id=job_id)
                    # If we don't lock the tables two simultanous
                    # requests might both increase the counter
                    # going over 5
                    if job.counter < 5:
                        job.counter += 1
                        job.save()

                finally:
                    Job.objects.unlock()


    """

    def lock(self, *tables):
        """ Lock table.

        Locks the object model table so that atomic update is possible.
        Simulatenous database access request pend until the lock is unlock()'ed.

        Note: If you need to lock multiple tables, you need to do lock them
        all in one SQL clause and this function is not enough. To avoid
        dead lock, all tables must be locked in the same order.

        See http://dev.mysql.com/doc/refman/5.0/en/lock-tables.html
        """
        try:
            cursor = connection.cursor()
            table = self.model._meta.db_table
            for T in tables:
                table = table + " WRITE , %s" % T._meta.db_table
            cursor.execute("LOCK TABLES %s WRITE" % table)
            row = cursor.fetchone()
            return row
        except:
            self.has_lock = False

    def unlock(self):
        try:
            """ Unlock the table. """
            cursor = connection.cursor()
            cursor.execute("UNLOCK TABLES")
            row = cursor.fetchone()
            return row
        except:
            self.has_unlock = False

class ActiveSongManager(models.Manager):
    """
    This manager only returns the songs marked as Active.

    For sites using the legacy_flag, songs with status Needs Re-Encoding are
    also considered (because stream rips are marked as such).

    Bound to Song.active
    """
    def get_query_set(self):
        songs = super(ActiveSongManager, self).get_query_set()
        if songs and hasattr(songs[0], 'legacy_flag'):
            return ((songs.filter(status='A')
                    | songs.filter(status='N')).exclude(legacy_flag='M'))
        else:
            return songs.filter(status='A')
