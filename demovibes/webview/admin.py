from demovibes.webview.models import *
from django.contrib import admin
from django.contrib.contenttypes import generic

from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

UserAdmin.list_display = ('id', 'username', 'email', 'is_active', 'date_joined');

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

class LogoAdmin(admin.ModelAdmin):
	search_fields = ["creator", "description"]
	list_display = ["id", "creator"]
	list_filter = ["active", "legacy"]

class CompilationSongInline(admin.TabularInline):
    model = CompilationSongList
    raw_id_fields = ["song"]

class SongLinkInline(generic.GenericTabularInline):
    qs_key = "S"
    extra = 1
    model = GenericLink
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "link":
            kwargs["queryset"] = GenericBaseLink.objects.filter(linktype = self.qs_key)
        return super(SongLinkInline, self).formfield_for_foreignkey(db_field, request, **kwargs)

class GroupLinkInline(SongLinkInline):
    qs_key = "G"

class UserLinkInline(SongLinkInline):
    qs_key = "U"

class LabelLinkInline(SongLinkInline):
    qs_key = "L"

class ArtistLinkInline(SongLinkInline):
    qs_key = "A"

class UserprofileAdmin(admin.ModelAdmin):
    search_fields = ['user__username']
    list_display = ['user', 'country', 'custom_css']
    inlines = [UserLinkInline]

class ScreenshotInline(admin.TabularInline):
    model = ScreenshotObjectLink
    extra = 1

class DownloadInline(admin.TabularInline):
    model = SongDownload
    extra = 3

class SongMetaAdmin(admin.ModelAdmin):
    search_fields = ['song__title']
    list_display = ['song', 'checked', 'active', 'user']
    list_filter = ['checked', 'active']
    filter_horizontal = ['artists', 'groups', 'labels']
    date_hierarchy = 'added'
    exclude = ["active"]

class SongAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'artist', 'uploader', 'bitrate', 'added', 'explicit']
    list_editable = ['status']
    search_fields = ['title', 'status']
    list_filter = ['status']
    fieldsets = [
        ("General"        ,{ 'fields' : ['title', 'file', 'explicit', 'status', 'license']}),
        ("Technical Stuff"    ,{ 'fields' : ['song_length', 'bitrate','samplerate','replay_gain']}),
        ("Playback"    ,{ 'fields' : ['loopfade_time', "playback_fadeout", "playback_bass_mode", "playback_bass_inter", "playback_bass_ramp", "playback_bass_mix",]}),
    ]
    if has_legacy_flag():
		list_display.append('legacy_flag')
		fieldsets[0][1]['fields'].insert(4, 'legacy_flag')
    inlines = [DownloadInline, SongLinkInline]
    date_hierarchy = 'added'

    def get_readonly_fields(self, request, obj=None):
        key = 'legacy_flag'
        if key in SongAdmin.list_display:
            return [key]

        return []

    def validate_status_field(self, new_status):
        had_file = not not self.song.file
        will_have_new_file = 'file' in self.request.FILES

        legacy_flag = getattr(self.song, 'legacy_flag', None)
        if will_have_new_file and new_status in ['K', 'N'] \
           and (legacy_flag != 'M' or new_status == 'K'):
            raise ValidationError(_('File is being replaced: Status should not be Needs Re-Encoding (intended for recovered files) or Kaput (intended for missing files). Change status to Active or something else valid and select a file again.'))
        elif not had_file and not will_have_new_file and Song.status_requires_file(new_status):
            raise ValidationError(_('File is missing: Status should not be playable (Active, Jingle, or Needs Re-Encoding). Either change status to something unplayable (e.g. Kaput which is intended for missing files) or select a replacement file.'))

        if legacy_flag:
            if not will_have_new_file and new_status == 'A' and legacy_flag == 'R':
                raise ValidationError(_('File is recovered: Status should not be Active (intended for replaced files). Either change status to e.g. Needs Re-Encoding (intended for recovered and playable songs) or select a replacement file.'))

            if will_have_new_file and legacy_flag != ' ':
                # Can't change POST['legacy_flag'] here because legacy_flag is
                # a read-only field and not taken into account.
                if new_status in ['N']:
                    self.song.legacy_flag = 'R'
                else:
                    self.song.legacy_flag = ' '

        from django.forms.fields import TypedChoiceField
        super(TypedChoiceField, self.form_instance.base_fields['status']).validate(new_status)

    def get_form(self, request, obj=None, **kwargs):
        self.request = request
        self.song = obj

        form = super(SongAdmin, self).get_form(request, obj=obj, **kwargs)
        self.form_instance = form

        # Override file field requirement and validation
        form.base_fields['file'].required = False
        form.base_fields['status'].validate = self.validate_status_field

        return form

class QueueAdmin(admin.ModelAdmin):
    list_display = ('song', 'requested', 'played', 'requested_by', 'priority', 'playtime')
    search_fields = ['song', 'requested_by__username']
    list_filter = ['priority', 'played']
    date_hierarchy = 'time_played'
    fields = ['song', 'played', 'requested_by', 'priority', 'playtime', 'time_played']

class SongCommentAdmin(admin.ModelAdmin):
    list_display = ['song', 'user']
    search_fields = ['song__title', 'user__username', 'comment']
    date_hierarchy = 'added'

class GroupAdmin(admin.ModelAdmin):
    search_fields = ['name']
    inlines = [GroupLinkInline]

class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'added')
    search_fields = ('title', 'text')

class ArtistAdmin(admin.ModelAdmin):
    search_fields = ('handle', 'name')
    list_display = ('handle', 'name', 'link_to_user')
    filter_horizontal = ['groups', 'labels']
    list_filter = ['status']
    fieldsets = [
        ("General info", {'fields' : ['handle', 'status', 'name', 'webpage', 'artist_pic', 'groups'] }),
        ("Personalia", {'fields' : ['dob', 'home_country', 'home_location', 'is_deceased', 'deceased_date', 'info'] }),
        ("NectaStuff", {'fields' : ['alias_of','created_by', 'link_to_user', 'labels' ] }),
        ("Other web pages", {'fields' : ['twitter_id', 'wiki_link', 'hol_id', 'last_fm_id'] }),
    ]
    inlines = [ArtistLinkInline]

class CompilationAdmin(admin.ModelAdmin):
    list_display = ('name', 'rel_date', 'date_added', 'created_by', 'status')
    search_fields = ['name'] # For now, we only need to search by the name of the compilation
    filter_horizontal = ['prod_groups', 'prod_artists']
    list_filter = ['status']
    raw_id_fields = ["prod_artists", "prod_groups"]
    exclude = ["cover_art"]
    inlines = [
        CompilationSongInline,
    ]

class LabelAdmin(admin.ModelAdmin):
    search_fields =  ['name']
    inlines = [LabelLinkInline]
    list_display = ('name', 'found_date', 'last_updated', 'created_by')

class LinkAdmin(admin.ModelAdmin):
    search_fields = ('link_title', 'link_url') # Because we might want to find links to a specific site
    list_display = ('name', 'link_title', 'link_url', 'link_type', 'added', 'submitted_by', 'priority')

class FaqAdmin(admin.ModelAdmin):
    search_fields = ('question', 'answer')
    list_display = ('question', 'added', 'added_by', 'priority', 'answer', 'active')

class ScreenshotAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ('name', 'image', 'last_updated', 'description', 'status')
    inlines = [
        ScreenshotInline,
    ]

class RadioStreamAdmin(admin.ModelAdmin):
    search_fields = ('name', 'user', 'country_code')
    list_display = ('name', 'bitrate', 'user', 'streamtype', 'country_code', 'active')
    list_editable = ['active']
    list_filter = ['active', 'streamtype']

class GBLAdmin(admin.ModelAdmin):
    list_display = ['name', 'linktype', 'link']
    list_filter = ['linktype']
    search_fields = ['name', 'link']

class ThemeAdmin(admin.ModelAdmin):
    list_display = ['title', 'creator', "active"]
    list_filter = ['active', "default"]

class LicenseAdmin(admin.ModelAdmin):
    list_display = ['name', 'downloadable']
    list_filter = ['downloadable']
    search_fields = ['name', 'url', 'description']

class ObjLogAdmin(admin.ModelAdmin):
    list_display = ['obj', 'user', "content_type", "added", "text"]
    search_fields = ['user__username', "text", "extra"]
    list_filter = ['user__is_staff']
    date_hierarchy = 'added'

admin.site.register(Group, GroupAdmin)
admin.site.register(Song, SongAdmin)
admin.site.register(SongLicense, LicenseAdmin)
admin.site.register(SongType)
admin.site.register(ObjectLog, ObjLogAdmin)
admin.site.register(Theme, ThemeAdmin)
admin.site.register(RadioStream, RadioStreamAdmin)
admin.site.register(News, NewsAdmin)
admin.site.register(Artist, ArtistAdmin)
admin.site.register(Userprofile, UserprofileAdmin)
admin.site.register(SongPlatform)
admin.site.register(Logo, LogoAdmin)
admin.site.register(GenericBaseLink, GBLAdmin)
admin.site.register(Queue, QueueAdmin)
admin.site.register(SongComment, SongCommentAdmin)
admin.site.register(Compilation, CompilationAdmin)
admin.site.register(Label, LabelAdmin)
admin.site.register(Link, LinkAdmin)
admin.site.register(LinkCategory)
admin.site.register(OnelinerMuted)
admin.site.register(Faq, FaqAdmin)
admin.site.register(Screenshot, ScreenshotAdmin)
admin.site.register(SongMetaData, SongMetaAdmin)
