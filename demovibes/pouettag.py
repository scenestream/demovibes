import urllib
import xml

def get_pouet_data(id, tag):
    try:
        pouetlink = "http://www.pouet.net/export/prod.xnfo.php?which=%d" % id
        usock = urllib.urlopen(pouetlink)
        xmldoc = xml.dom.minidom.parse(usock)
        usock.close()
        data = xmldoc.getElementsByTagName(tag)[0]
        return data.firstChild.nodeValue
    except:
        return ""



def scan_songs(songs):
    for s in songs:
        if not s.tags:
            print "Song %s (%s)" % (s, s.pouetid)
            print " Date", get_pouet_data(s.pouetid, "date")[-4:]
            print " Category", get_pouet_data(s.pouetid, "category")
            print " Platform", get_pouet_data(s.pouetid, "platform")
            print " Group", get_pouet_data(s.pouetid, "group")
            print " Party", get_pouet_data(s.pouetid, "party")

def replace_tags(tag, tags):
    from tagging.models import Tag
    for ti in tag.items.all():
        for tag in tags:
            Tag.objects.add_tag(ti.object, tag)
        ti.delete()
