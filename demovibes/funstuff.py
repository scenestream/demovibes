from webview import models

def fadeoutin():
    models.add_event("""eval:$("img").fadeOut(600);window.setTimeout("$('img').fadeIn(1000)", 700);""")

def img_shrinkgrow():
    models.add_event("""eval:$("img").slideUp(300);window.setTimeout("$('img').slideDown(3000)", 350);""")

def themestat():
    for t in models.Theme.objects.all():
        print t, "->", t.userprofile_set.filter(custom_css="").count()

def send_user_to(user, url):
    """
    Sets window.location to <url> for userobject <user>
    """
    models.add_event("""eval:window.location="%s";""" % url, user)
