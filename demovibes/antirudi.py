from antirudi2 import rudiger
EMAIL = ["meesdorf", "rm1911", "ruedig", "rmuell", "mbpro91"]
USERNAME = ["rm1911", "imgur"]

def check_user(user):
    if [x for x in EMAIL if x in user.email.lower()]:
        return True
    if [x for x in USERNAME if x in user.username.lower()]:
        return True


def rudispotter(data):
    user = data["user"]
    Group = data["groupmodel"]
    if check_user(user):
        G = Group.objects.get(id=3) # Rudibin
        user.groups.add(G)
        up = user.get_profile()
        up.hellbanned = True
        up.save()
