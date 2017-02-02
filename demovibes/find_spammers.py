def find_spammers(User, limit=4000, list_webpages=False):
    a = []
    for x in User.objects.all().order_by("-id")[:limit]:
        if ("[url=h" in  x.get_profile().info or (list_webpages and x.get_profile().web_page)) and x.favorite_set.count() == 0 and not x.get_profile().have_artist():
                a.append(x)
    return a

def get_spammers(User, limit=4000, list_webpages=False):
	a = []
	for x in find_spammers(User, limit, list_webpages):
            print "\n\n", x, x.id, x.get_profile().web_page, "\n", x.get_profile().info, x.get_profile().country
            if input("Add to list? (0 for no, 1 for yes) "):
                a.append(x)
	return a
		
