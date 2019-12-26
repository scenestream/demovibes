from webview import models
from webview.models import get_now_playing_song
from django.core.cache import cache
from django.conf import settings
from django.http import HttpResponseForbidden
from functools import wraps
from django.utils.decorators import available_attrs
from django.template.loader import render_to_string

from django.core.urlresolvers import reverse

from django.db.models import Sum

from django.utils.html import escape

import logging
import socket
import datetime
import random
import j2shim
import time

logger = logging.getLogger("dv.webview.common")

try:
    import memcache
    # Temp test code FIXME
    mc = memcache.Client(['127.0.0.1:11211'], debug=0)
except:
    logger.debug("Could not load memcache module")
    memcache = None

MIN_QUEUE_SONGS_LIMIT = getattr(settings, "MIN_QUEUE_SONGS_LIMIT", 0)
QUEUE_TIME_LIMIT = getattr(settings, "QUEUE_TIME_LIMIT", False)
SELFQUEUE_DISABLED = getattr(settings, "SONG_SELFQUEUE_DISABLED", False)
LOWRATE = getattr(settings, 'SONGS_IN_QUEUE_LOWRATING', False)

NGINX_MEMCACHE = memcache and getattr(settings, 'NGINX', {}).get("memcached")

def nginx_memcache_it(key, use_eventkey = True):
    def func1(func):
        def func2(*args, **kwargs):
            r = func(*args, **kwargs)
            url = reverse(key) + "?"
            latest_event = get_latest_event()

            logger.debug("NGINX: Latest event is %s", latest_event)

            if use_eventkey:
                # Clients often connect with older id's, for various reasons
                # This should make it far more likely that they get current data
                # and actually hit the cache in the first place
                for x in range(latest_event - 6, latest_event + 1, 1):
                    cachekey = url + "event=%s" % x
                    logger.debug("NGINX: Setting cache for key %s", cachekey)
                    mc.set(cachekey, r.encode("utf8"), 30)
            else:
                logger.debug("NGINX: Setting cache for key %s", url)
                mc.set(url, r.encode("utf8"), 30)
            return r

        if not NGINX_MEMCACHE:
            logger.info("NGINX: Memcache settings not configured")
            return func
        return func2
    return func1


def atomic(key, timeout=30, wait=60):
    """
    Lock a function so it can not be run in parallell

    Key value identifies function to lock
    """
    lockkey = "lock-" + key
    def func1(func):
        def func2(*args, **kwargs):
            c = 0
            has_lock = cache.add(lockkey, 1, timeout)
            while not has_lock and c < wait * 10:
                c = c + 1
                time.sleep(0.1)
                has_lock = cache.add(lockkey, 1, timeout)
            if has_lock:
                try:
                    return func(*args, **kwargs)
                finally:
                    cache.delete(lockkey)
        return func2
    return func1

def ratelimit(limit=10,length=86400):
    """
    Limit function to <limit> runs per ip address, over <length> seconds.

    Expects first function parameter to be a request object.
    """
    def decorator(func):
        def inner(request, *args, **kwargs):
            ip_hash = str(hash(request.META['REMOTE_ADDR']))
            result = cache.get(ip_hash)
            if result:
                result = int(result)
                if result == limit:
                    logger.warning("Rate limited : %s", request.META['REMOTE_ADDR'])
                    return HttpResponseForbidden("Ooops, too many requests!")
                else:
                    cache.incr(ip_hash)
                    return func(request,*args,**kwargs)
            cache.add(ip_hash,1,length)
            return func(request, *args, **kwargs)
        return wraps(func, assigned=available_attrs(func))(inner)
    return decorator

def play_queued(queue_item):
    try:
        queue_item.song.times_played = queue_item.song.times_played + 1
    except TypeError:
        queue_item.song.times_played = 1
    queue_item.song.save()
    queue_item.time_played=datetime.datetime.now()
    queue_item.played = True
    queue_item.save()
    temp = get_now_playing(True)
    temp = get_history(True)
    temp = get_queue(True)
    models.add_event(eventlist=("queue", "history", "nowplaying"))


def find_queue_time_limit(user, song):
    """
    Return seconds left of limit
    """
    next = False
    if QUEUE_TIME_LIMIT:
        limit = models.TimeDelta(**QUEUE_TIME_LIMIT[0])
        duration = models.TimeDelta(**QUEUE_TIME_LIMIT[1])
        start = datetime.datetime.now() - duration

        #Fetch all queued objects by that user in given time period
        Q = models.Queue.objects.filter(requested__gt = start, requested_by = user).order_by("id")

        total_seconds = limit.total_seconds() - song.get_songlength()

        if Q.count():
            queued_seconds = Q.aggregate(Sum("song__song_length"))["song__song_length__sum"] #Length of all songs queued
            seconds_left = total_seconds - queued_seconds
            earliest = Q[0].requested
            next = earliest + duration
            if seconds_left <= 0:
                seconds_left = seconds_left + song.get_songlength()
                return (True, seconds_left, next)
            return (False, seconds_left, next)
        return (False, total_seconds, next)
    return (False, False, next)


def get_dj_hours(date, num_hours):
    rnd = random.Random(date.year+date.month+date.day)
    hours = []
    num_hours = min(num_hours, 24)
    while len(hours) < num_hours:
        hour = rnd.randrange(0, 24)
        if hour not in hours:
            hours.append(hour)

    return hours

# This atomic decoration is great and all, but it doesn't
#  work when you actually catch and handle all exceptions.
@atomic("queue-song")
def queue_song(song, user, event = True, force = False):
    event_metadata = {'song': song.id, 'user': user.id}

    if user.get_profile().is_hellbanned():
        return False

    if SELFQUEUE_DISABLED and song.is_connected_to(user):
        models.send_notification("You can't request your own songs!", user)
        return False

    # To update lock time and other stats
    #  select_for_update is used to lock the song row, so no other request
    #  can modify it at the same time.
    song = models.Song.objects.select_for_update().get(id=song.id)

    num_dj_hours = getattr(settings, 'DJ_HOURS', 0)

    if not force and num_dj_hours:
        # Don't allow requests to be played during DJ hours

        play_start = models.Queue(song=song).get_eta()
        hours_at_start = get_dj_hours(play_start, num_dj_hours)

        play_end = play_start + datetime.timedelta(seconds=song.get_songlength())
        if play_end.day == play_start.day:
            hours_at_end = hours_at_start
        else:
            hours_at_end = get_dj_hours(play_end, num_dj_hours)

        if play_start.hour in hours_at_start or play_end.hour in hours_at_end:
            if datetime.datetime.now().hour in hours_at_start:
                s = "Queuing songs is disabled during DJ Random sessions. DJ Random has the floor!!!"
            else:
                s = "Queuing songs during hour of expected play time is not allowed. DJ Random will have the floor!!!"
            models.send_notification(s, user)
            return False

    key = "songqueuenum-" + str(user.id)

    EVS = []
    Q = False
    time = song.create_lock_time()
    result = True
    long_tune_length = 420 # sieben Minuten

    total_req_count = models.Queue.objects.filter(played=False).count()
    if total_req_count < MIN_QUEUE_SONGS_LIMIT and not song.is_locked():
        Q = models.Queue.objects.filter(played=False, requested_by=user)
        user_req_and_play_count = Q.count()
        total_req_and_play_count = total_req_count

        now_playing = get_now_playing_song()
        if now_playing:
            total_req_and_play_count += 1
            if now_playing.requested_by == user:
                user_req_and_play_count += 1

        # Is user the only one requesting (and also same user as requester of
        # currently playing song) ? Then allow forced queueing.
        # In all other cases there's at least one other requester and
        # then the normal rules apply.
        if user_req_and_play_count == total_req_and_play_count:
            force = True
        # Disallow queuing of multiple long tunes. 
        if (song.song_length >= long_tune_length and Q.filter(song__song_length__gte = long_tune_length).filter(requested_by = user)) or (song.song_length >= long_tune_length and get_now_playing_song().requested_by == user and get_now_playing_song().song.song_length >= long_tune_length):   
            logger.debug("ltlen: %s; Q: %s" % (long_tune_length, Q))
            models.send_notification("You may only queue one long tune at a time.", user)
            result = False


    time_full, time_left, time_next = find_queue_time_limit(user, song)
    time_left_delta = models.TimeDelta(seconds=time_left)

    if not force:
        if time_full:
            result = False
            models.send_notification("Song is too long. Remaining timeslot : %s. Next timeslot change: <span class='tzinfo'>%s</span>" %
                        (time_left_delta.to_string(), time_next.strftime("%H:%M")), user)

        requests = cache.get(key, None)
        if not Q:
            Q = models.Queue.objects.filter(played=False, requested_by=user)
        if requests == None:
            requests = Q.count()
        else:
            requests = len(requests)

        if result and requests >= settings.SONGS_IN_QUEUE:

            models.send_notification("You have reached your unplayed queue entry limit! Please wait for your requests to play.", user)
            result = False

        if result and song.is_locked():
            # In a case, this should not append since user (from view) can't reqs song locked
            models.send_notification("Song is already locked", user)
            result = False

        if result and LOWRATE and song.rating and song.rating <= LOWRATE['lowvote']:
            if Q.filter(song__rating__lte = LOWRATE['lowvote']).count() >= LOWRATE['limit']:
                models.send_notification("Anti-Crap: Song Request Denied (Rating Too Low For Current Queue)", user)
                result = False

    if result:
        song.locked_until = datetime.datetime.now() + time
        song.save()
        Q = models.Queue(song=song, requested_by=user, played = False)
        Q.eta = Q.get_eta()
        Q.save()
        EVS.append('a_queue_%i' % song.id)

        #Need to add logic to decrease or delete when song gets played
        #cache.set(key, requests + 1, 600)

        if event:
            get_queue(True) # generate new queue cached object
            EVS.append('queue')
            msg = "%s has been queued." % escape(song.title)
            msg += " It is expected to play at <span class='tzinfo'>%s</span>." % Q.eta.strftime("%H:%M")
            if time_left != False:
                msg += " Remaining timeslot : %s." % time_left_delta.to_string()
            models.send_notification(msg, user)
        models.add_event(eventlist=EVS, metadata = event_metadata)
        return Q

#@nginx_memcache_it("dv-ax-nowplaying")
def get_now_playing(create_new=False):
    logger.debug("Getting now playing")
    key = "nnowplaying"

    try:
        songtype = get_now_playing_song(create_new)
        song = songtype.song
    except:
        return ""

    R = cache.get(key)
    if not R or create_new:
        comps = models.Compilation.objects.filter(songs__id = song.id)
        R = j2shim.r2s('webview/t/now_playing_song.html', { 'now_playing' : songtype, 'comps' : comps })
        cache.set(key, R, 300)
        logger.debug("Now playing generated")
    R = R.replace("((%timeleft%))", str(songtype.timeleft()))
    return R

@nginx_memcache_it("dv-ax-history")
def get_history(create_new=False):
    key = "nhistory"
    logger.debug("Getting history cache")
    R = cache.get(key)
    if not R or create_new:
        nowplaying = get_now_playing_song()
        limit = nowplaying and (nowplaying.id - 50) or 0
        logger.debug("No existing cache for history, making new one")
        history = models.Queue.objects.select_related(depth=3).filter(played=True).filter(id__gt=limit).order_by('-time_played')[1:21]
        R = j2shim.r2s('webview/js/history.html', { 'history' : history })
        cache.set(key, R, 300)
        logger.debug("Cache generated")
    return R

@nginx_memcache_it("dv-ax-oneliner")
def get_oneliner(create_new=False):
    key = "noneliner"
    logger.debug("Getting oneliner cache")
    R = cache.get(key)
    if not R or create_new:
        logger.debug("No existing cache for oneliner, making new one")
        lines = getattr(settings, 'ONELINER', 10)
        oneliner = models.Oneliner.objects.select_related(depth=2).order_by('-id')[:lines]
        R = j2shim.r2s('webview/js/oneliner.html', { 'oneliner' : oneliner })
        cache.set(key, R, 600)
        logger.debug("Cache generated")
    return R

def get_roneliner(create_new=False):
    key = "rnoneliner"
    logger.debug("Getting reverse oneliner cache")
    R = cache.get(key)
    if not R or create_new:
        logger.debug("No existing cache for reverse oneliner, making new one")
        oneliner = models.Oneliner.objects.select_related(depth=2).order_by('id')[:15]
        R = j2shim.r2s('webview/js/roneliner.html', { 'oneliner' : oneliner })
        cache.set(key, R, 600)
        logger.debug("Cache generated")
    return R

@nginx_memcache_it("dv-ax-queue")
def get_queue(create_new=False):
    key = "nqueue"
    logger.debug("Getting cache for queue")
    R = cache.get(key)
    if not R or create_new:
        logger.debug("No existing cache for queue, making new one")
        queue = models.Queue.objects.select_related(depth=2).filter(played=False).order_by('id')
        R = j2shim.r2s("webview/js/queue.html", { 'queue' : queue })
        cache.set(key, R, 300)
        logger.debug("Cache generated")
    return R

# implement get_recent_posts() analogous to the get_queue above
def get_recent_posts(create_new=False):
    key = "recent_posts"
    R = cache.get(key)
    if not R or create_new:
        posts = models.SongComment.objects.all().order_by('-id')[:20]
        R = j2shim.r2s("webview/js/recent_posts.html", { 'recent_posts' : posts })
        cache.set(key, R, 300)
    return R
                

def get_profile(user):
    """
    Get a user's profile.

    Tries to get a user's profile, and create it if it doesn't exist.
    """
    try:
        profile = user.get_profile()
    except:
        profile = models.Userprofile(user = user)
        profile.save()
    return profile

def get_latest_event():
    curr = cache.get("curr_event")
    if not curr:
        curr = get_latest_event_lookup()
        cache.set("curr_event", curr, 30)
    return curr

def get_latest_event_lookup():
    use_eventful = getattr(settings, 'USE_EVENTFUL', False)
    if use_eventful:
        host = getattr(settings, 'EVENTFUL_HOST', "127.0.0.1")
        port = getattr(settings, 'EVENTFUL_PORT', 9911)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        try:
            s.connect((host, port))
            s.send("event::")
            result = s.recv(1024)
        except socket.timeout:
            return 0
        return result.strip()
    else:
        try:
            return models.AjaxEvent.objects.order_by('-id')[0].id
        except:
            return 0

def add_oneliner(user, message):
    message = message.strip()
    can_post = user.is_superuser or not user.has_perm('webview.mute_oneliner')

    r = user.get_profile().is_muted()
    if can_post and r:
        can_post = False
        models.send_notification('You can not post until <span class="tzinfo">%s</span>. Reason: %s' % (r["time"].strftime("%H:%M"), r["reason"]), user)

    if message and can_post:
        models.Oneliner.objects.create(user = user, message = message)
        get_oneliner(True)
        make_oneliner_xml(True)
        models.add_event(event='oneliner')

def get_event_key(key):
    event = get_latest_event()
    return "%sevent%s" % (key, event)

@nginx_memcache_it("xml-oneliner-cache", False)
def make_oneliner_xml(force=False):
    data = cache.get("oneliner_xml")
    if force or data == None:
        oneliner_data = models.Oneliner.objects.select_related(depth=1).order_by('-id')[:20]
        data = render_to_string('webview/xml/oneliner.xml', {'oneliner_data' : oneliner_data})
        cache.set("oneliner_xml", data, 60)
    return data
