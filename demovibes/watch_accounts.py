import time

def watch_users(User):
	ou = None
	while True:
	    nu = User.objects.order_by("-id")[0]
	    if ou != nu:
	        print "New user:", nu, nu.email, nu.date_joined
	        i = raw_input(" Keep user? [y/n]")
	        if i in ["n"]:
		    print " Deleting", nu
	            nu.delete()
	        else:
	            ou = nu
	        time.sleep(1)
