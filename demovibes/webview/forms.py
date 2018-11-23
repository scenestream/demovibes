from webview import models as M
from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from PIL import Image
#import mimetypes
import dscan
import logging

BAN_MIN = getattr(settings, "BANTIME_MIN", 5)
BAN_MAX = getattr(settings, "BANTIME_MAX", 60)
BAN_DEF = getattr(settings, "BANTIME_INITIAL", 15)

log = logging.getLogger("dv.webview.forms")

class OnelinerHistory(forms.Form):
    username = forms.CharField(max_length=40)
    start = forms.IntegerField(min_value=0, max_value=200,initial=0)
    results = forms.IntegerField(min_value=10, max_value=100,initial=10)


class _UploadFormBase(forms.ModelForm):
    def clean_file(self):
        data = self.cleaned_data['file']

        if not hasattr(data, 'temporary_file_path'):
            log.error("uploaded file was kept in memory")

        if dscan.is_configured() and hasattr(data, 'temporary_file_path'):
            file = data.temporary_file_path()
            df = dscan.ScanFile(file)
            if not df.readable:
                raise forms.ValidationError("Unsupported audio format! Check the FAQ to see what's accepted")

            #I dropped the bitrate requirement. nothing keeps people from reencoding shitty files
            # which will further reduce quality. also with ogg and aac, lower bitrates are more common
            #if df.bitrate < 128 and df.bitrate != 0:
            #    raise forms.ValidationError("We only accept audio with a bitrate of 128 kbps or higher")

        #how the hell pymand finds the file without path is a mystery to me
        if not dscan.is_configured():
            import mad
            mf = mad.MadFile(data)
            bitrate = mf.bitrate() / 1000
            layer = mf.layer()
            if bitrate < 128 or layer != 3:
                raise forms.ValidationError("We only accept mpeg layer 3 (MP3) encoded files with bitrate of 128 kbps or higher")

        return data


class UploadForm(_UploadFormBase):
    class Meta:
        model = M.Song
        fields = ["file", "title"]


class SongMetadataForm(forms.ModelForm):
    class Meta:
        fields = ["release_year", "remix_of_id", "groups", "labels", "info", "type", "platform", "pouetid", "ytvidid", "ytvidoffset"]
        model = M.SongMetaData

class MetadataUploadForm(_UploadFormBase):
    class Meta:
        model = M.SongMetaData
        fields = []
        if M.site_supports_song_file_replacements_by_user():
            fields.append('file')

    def __init__(self, *args, **kwargs):
        file_is_required = kwargs.pop('file_is_required', False)
        super(MetadataUploadForm, self).__init__(*args, **kwargs)

        # Don't pass an instance of meta the first time: it makes the file
        # field pre-filled and clearable, while we wan't it to appear empty
        # and optionally be required.
        if not 'file' in args:
            assert not 'instance' in args, "Don't pass instance with initial non-POST ctor"

        field = 'file'
        if file_is_required and field in self.fields:
            self.fields[field].required = True

            # Change the label the first time only (when not POSTing yet).
            # It appears harmless to change during POST but is useless anyway
            # so just don't do it.
            if not args:
                self.fields[field].label = _('Replacement File')


class MetadataCommentForm(forms.ModelForm):
    class Meta:
        model = M.SongMetaData
        fields = ['comment']


class EditSongMetadataForm(forms.ModelForm):
    class Meta:
        fields = ["artists", "release_year", "remix_of_id", "groups", "labels", "info", "type", "platform", "pouetid", "ytvidid", "ytvidoffset", "comment"]
        model = M.SongMetaData

class CreateArtistForm(forms.ModelForm):
    class Meta:
        model = M.Artist
        fields = ["handle", "name", "dob", "home_country",
                "home_location", "hol_id", "twitter_id", "last_fm_id",
                "info", "artist_pic", "webpage", "wiki_link", "groups",
                "labels", "scene_relevance"
            ]

    def clean_artist_pic(self):
        artist_pic = self.cleaned_data['artist_pic']
        if not artist_pic:
            return None

        max_size = getattr(settings, 'MAX_ARTIST_AVATAR_SIZE', 65536)
        max_height = getattr(settings, 'MAX_ARTIST_AVATAR_HEIGHT', 250)
        max_width = getattr(settings, 'MAX_ARTIST_AVATAR_WIDTH', 250)

        if len(artist_pic) > max_size:
            raise forms.ValidationError('Image must be no bigger than %d bytes' % max_size)

        image = Image.open(artist_pic)
        img_w, img_h = image.size
        if img_w > max_width or img_h > max_height:
            raise forms.ValidationError('Image is bigger than allowed size dimensions! (Height : %d, width : %d)' % (max_height, max_width))

        return self.cleaned_data['artist_pic']

class CreateSessionForm(forms.Form):
    description = forms.CharField(required=False, label = "Description")
    time = forms.DateTimeField(input_formats=['%Y-%m-%d %H:%M'], label="Play time", help_text = "Format: YYYY-mm-dd HH:HM")

class GenericInfoForm(forms.Form):
    content_type = forms.ModelChoiceField(queryset = M.ContentType.objects.all(), widget = forms.HiddenInput)
    object_id = forms.CharField(widget=forms.HiddenInput)

class CreateScreenshotForm(forms.ModelForm):

    class Meta:
        model = M.Screenshot
        fields = ["name", "image", "description"]

    def clean_image(self):
        image = self.cleaned_data['image']
        if not image:
            return None

        max_height = getattr(settings, 'SCREEN_UPLOAD_HEIGHT', 800)
        max_width = getattr(settings, 'SCREEN_UPLOAD_WIDTH', 800)

        image = Image.open(image)
        img_w, img_h = image.size
        if img_w > max_width or img_h > max_height:
            raise forms.ValidationError('Screenshot is bigger than allowed size dimensions! (Max Height : %d, Width : %d)' % (max_height, max_width))

        return self.cleaned_data['image']

class CreateLabelForm(forms.ModelForm):
    class Meta:
        model = M.Label
        fields = ["name", "webpage", "wiki_link", "logo", "pouetid", "hol_id", "found_date", "cease_date", "info"]

    def clean_logo(self):
        logo = self.cleaned_data['logo']
        if not logo:
            return None

        max_size = getattr(settings, 'MAX_LABEL_AVATAR_SIZE', 65536)
        max_height = getattr(settings, 'MAX_LABEL_AVATAR_HEIGHT', 250)
        max_width = getattr(settings, 'MAX_LABEL_AVATAR_WIDTH', 250)

        if len(logo) > max_size:
            raise forms.ValidationError('Image must be no bigger than %d bytes' % max_size)

        image = Image.open(logo)
        img_w, img_h = image.size
        if img_w > max_width or img_h > max_height:
            raise forms.ValidationError('Image is bigger than allowed size dimensions! (Height : %d, width : %d)' % (max_height, max_width))

        return self.cleaned_data['logo']

class CreateGroupForm(forms.ModelForm):
    class Meta:
        model = M.Group
        fields = ["name", "group_logo", "webpage", "wiki_link", "pouetid", "found_date", "info"]

    def clean_group_logo(self):
        group_logo = self.cleaned_data['group_logo']
        if not group_logo:
            return None

        max_size = getattr(settings, 'MAX_GROUP_AVATAR_SIZE', 65536)
        max_height = getattr(settings, 'MAX_GROUP_AVATAR_HEIGHT', 250)
        max_width = getattr(settings, 'MAX_GROUP_AVATAR_WIDTH', 250)

        if len(group_logo) > max_size:
            raise forms.ValidationError('Image must be no bigger than %d bytes' % max_size)

        image = Image.open(group_logo)
        img_w, img_h = image.size
        if img_w > max_width or img_h > max_height:
            raise forms.ValidationError('Image is bigger than allowed size dimensions! (Height : %d, width : %d)' % (max_height, max_width))

        return self.cleaned_data['group_logo']

class ThemeForm(forms.ModelForm):
    class Meta:
        model = M.Theme
        fields = ["title", "active", "css", "description"]

class ProfileForm(forms.ModelForm):
    def clean_avatar(self):
        avatar = self.cleaned_data['avatar']
        if not avatar:
            return None

        max_size = getattr(settings, 'MAX_AVATAR_SIZE', 65536)
        max_height = getattr(settings, 'MAX_AVATAR_HEIGHT', 100)
        max_width = getattr(settings, 'MAX_AVATAR_WIDTH', 100)

        if len(avatar) > max_size:
            raise forms.ValidationError('Image must be no bigger than %d bytes' % max_size)

        image = Image.open(avatar)
        img_w, img_h = image.size
        if img_w > max_width or img_h > max_height:
            raise forms.ValidationError('Image is bigger than allowed size dimensions! (Height : %d, width : %d)' % (max_height, max_width))
        return self.cleaned_data['avatar']

    class Meta:
        model = M.Userprofile
        fields = ['infoline', 'visible_to', 'web_page', 'aol_id', 'yahoo_id',
            'icq_id', 'twitter_id', 'hol_id', 'country', 'location', 'avatar',
            'fave_id', 'email_on_pm', 'email_on_group_add', 'email_on_artist_add',
            'pm_accepted_upload', 'paginate_favorites', 'custom_css', 'use_tags',
            'show_screenshots', 'show_youtube', 'info']

class PmForm(forms.ModelForm):
    to = forms.CharField()
    subject = forms.CharField(min_length=3)
    def clean_to(self):
        data = self.cleaned_data['to']
        try:
            U = M.User.objects.get(username=data)
        except:
            raise forms.ValidationError("User does not exist")
        return U
    class Meta:
        model = M.PrivateMessage
        fields = ('to', 'subject', 'message')

class CreateLinkForm(forms.ModelForm):
    class Meta:
        model = M.Link
        fields = ["link_type", "url_cat", "name", "link_title", "link_url", "link_image", "notes"]

    def clean_link_image(self):
        link_image = self.cleaned_data['link_image']
        if not link_image:
            return None

        max_size = getattr(settings, 'MAX_LINK_IMG_SIZE', 16384)
        max_height = getattr(settings, 'MAX_LINK_IMG_HEIGHT', 18)
        max_width = getattr(settings, 'MAX_LINK_IMG_WIDTH', 25)

        if len(link_image) > max_size:
            raise forms.ValidationError('Link Image must be no bigger than %d bytes' % max_size)

        image = Image.open(link_image)
        img_w, img_h = image.size
        if img_w > max_width or img_h > max_height:
            raise forms.ValidationError('Link Image is bigger than allowed size dimensions! (Height : %d, width : %d)' % (max_height, max_width))

        return self.cleaned_data['link_image']

class MuteOnelinerForm(forms.ModelForm):
    username = forms.CharField(max_length=60)
    mute_minutes = forms.IntegerField(max_value=BAN_MAX, min_value=BAN_MIN,
        initial=BAN_DEF, help_text="Value between %s and %s" % (BAN_MIN, BAN_MAX))
    ban_ip = forms.BooleanField(required=False)

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            user = M.User.objects.get(username=username)
        except:
            raise forms.ValidationError('User does not exist')
        return user

    class Meta:
        model = M.OnelinerMuted
        fields = ["reason", "details"]

class CreateCompilationForm(forms.ModelForm):
    class Meta:
        model = M.Compilation
        exclude = ["songs", "prod_artists", "created_by", "prod_groups", "running_time", "status", "cover_art", "last_updated"]

class SLForm(object):
    class Media:
        js = ("js/license_info.js",)

class SongLicenseForm(SLForm, forms.ModelForm):
    class Meta:
        model = M.Song
        fields = ["license"]

class LicenseForm(SLForm, forms.Form):
    license = forms.ModelChoiceField(queryset = M.SongLicense.objects.all(), empty_label="(No license)", required=False)
