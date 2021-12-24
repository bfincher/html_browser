from django.conf.urls import include, url
from django_js_reverse.views import urls_js

from html_browser import settings
from html_browser.views import adminViews as admin_views
from html_browser.views import base_view, content_view
from html_browser.views import userViews as user_views

FILE_NAME_CHARS = r'[\w \-~!@#$%^&*\(\)\+,\.\'’‘\[\]\{\}]'
FOLDER_AND_PATH_REGEX = fr'(?P<folder_and_path_url>\w+(/{FILE_NAME_CHARS}+?)*)/'
prefix = settings.URL_PREFIX

def _getUrlWithPath(name):
    return fr'{prefix}{name}/{FOLDER_AND_PATH_REGEX}(?P<file_name>{FILE_NAME_CHARS}+)/$'

urlpatterns = [
    url(fr'{prefix}$', base_view.IndexView.as_view(), name='index'),
    url(fr'^{prefix}hb/$', base_view.IndexView.as_view()),
    url(fr'{prefix}addFolder/$', admin_views.AddFolderView.as_view(), {'title': 'Add Folder'}, name='addFolder'),
    url(fr'{prefix}addGroup/$', admin_views.AddGroupView.as_view(), name='addGroup'),
    url(fr'{prefix}addUser/$', user_views.AddUserView.as_view(), {'title': 'Add User'}, name='addUser'),
    url(fr'{prefix}content/{FOLDER_AND_PATH_REGEX}$', content_view.ContentView.as_view(), name='content'),
    url(fr'{prefix}deleteFolder/(?P<folder_name>.*?)$', admin_views.DeleteFolderView.as_view(), name='deleteFolder'),
    url(fr'{prefix}deleteGroup/$', admin_views.DeleteGroupView.as_view(), name='deleteGroup'),
    url(fr'{prefix}deleteImage/{FOLDER_AND_PATH_REGEX}$', base_view.DeleteImageView.as_view(), name='deleteImage'),
    url(fr'{prefix}deleteUser/$', user_views.DeleteUserView.as_view(), name='deleteUser'),
    url(_getUrlWithPath('download'), base_view.DownloadView.as_view(), name='download'),
    url(fr'{prefix}download_zip/{FOLDER_AND_PATH_REGEX}$', base_view.DownloadZipView.as_view(), name='downloadZip'),
    url(fr'{prefix}editGroup/(?P<group_name>\w+)$', admin_views.EditGroupView.as_view(), name='editGroup'),
    url(fr'{prefix}editFolder/(?P<folder_name>.*?)/$', admin_views.EditFolderView.as_view(), {'title': 'Edit Folder'}, name='editFolder'),
    url(fr'{prefix}editUser/(?P<username>.*?)/$', user_views.EditUserView.as_view(), {'title': 'Edit User'}, name='editUser'),
    url(fr'{prefix}folderAdmin/$', admin_views.FolderAdminView.as_view(), name='folderAdmin'),
    url(_getUrlWithPath('getNextImage'), base_view.GetNextImageView.as_view(), name='getNextImage'),
    url(fr'{prefix}hbAdmin/.*', admin_views.AdminView.as_view(), name='admin'),
    url(fr'{prefix}hbChangePassword/$', user_views.ChangePasswordView.as_view(), name='changePassword'),
    url(fr'{prefix}hbLogin/$', base_view.LoginView.as_view(), name='login'),
    url(fr'{prefix}hbLogout/$', base_view.LogoutView.as_view(), name='logout'),
    url(_getUrlWithPath('imageView'), base_view.ImageView.as_view(), name='imageView'),
    url(fr'{prefix}groupAdmin/$', admin_views.GroupAdminView.as_view(), name='groupAdmin'),
    url(fr'{prefix}upload/{FOLDER_AND_PATH_REGEX}$', base_view.UploadView.as_view(), name='upload'),
    url(fr'{prefix}userAdmin/$', user_views.UserAdminView.as_view(), name='userAdmin'),
    url(fr'{prefix}thumb/(?P<path>.*)', base_view.ThumbView.as_view(), name='thumb'),
    url(fr'{prefix}jsreverse/$', urls_js, name='js_reverse'),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'__debug__/', include(debug_toolbar.urls))
    ] + urlpatterns
