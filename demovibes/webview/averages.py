from django.core.management import setup_environ
import settings

setup_environ(settings)

from django.db.models import Avg
from webview.models import *

import datetime

def write_averages(outfile="votes.html", min_votes = 10):
    f = open(outfile, "w")
    date = "<p>Generated at %s</p>" % datetime.datetime.now()
    f.write("""<html><head><title>Votes avg</title>
    <script src="/static/js/sort/tablesort.min.js" type="text/JavaScript"></script> 
    </head><body>%s<table>\n""" % date)
    f.write("""<tr> <th class="sortable">User</th> <th class="sortable">Average</th> <th class="sortable">Total votes</th> </tr>""")
    for u in User.objects.all().order_by("username"):
        q = SongVote.objects.filter(user=u)
        nr = q.count()
        if nr < min_votes:
            continue
        a = q.aggregate(Avg("vote"))['vote__avg']
        if a:
            s = "<tr><td>%s</td><td>%s</td><td>%s</td></tr>\n"% (u.username, a, nr)
            f.write(s)
    f.write("</table></body></html>")
    f.close()


if __name__ == '__main__':
    write_averages()
