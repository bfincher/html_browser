from django.conf.urls import include, url
from django_js_reverse.views import urls_js

from html_browser import settings
from html_browser.views import adminViews as admin_views
from html_browser.views import base_view, content_view
from html_browser.views import userViews as user_views

file_name_chars = r'[\w \-~!@#$%^&*\(\)\+,\.\'’‘\[\]]'
folder_and_path_regex = r'(?P<folder_and_path_url>\w+(/%s+?)*)/' % file_name_chars
prefix = settings.URL_PREFIX

urlpatterns = [
    url(r'^%s$' % prefix, base_view.IndexView.as_view(), name='index'),
    url(r'^%shb/$' % prefix, base_view.IndexView.as_view()),
    url(r'%saddFolder/$' % prefix, admin_views.AddFolderView.as_view(), {'title': 'Add Folder'}, name='addFolder'),
    url(r'%saddGroup/$' % prefix, admin_views.AddGroupView.as_view(), name='addGroup'),
    url(r'%saddUser/$' % prefix, user_views.AddUserView.as_view(), {'title': 'Add User'}, name='addUser'),
    url(r'%scontent/%s$' % (prefix, folder_and_path_regex), content_view.ContentView.as_view(), name='content'),
    url(r'%sdeleteFolder/(?P<folder_name>.*?)$' % prefix, admin_views.DeleteFolderView.as_view(), name='deleteFolder'),
    url(r'%sdeleteGroup/$' % prefix, admin_views.DeleteGroupView.as_view(), name='deleteGroup'),
    url(r'%sdeleteImage/%s$' % (prefix, folder_and_path_regex), base_view.DeleteImageView.as_view(), name='deleteImage'),
    url(r'%sdeleteUser/$' % prefix, user_views.DeleteUserView.as_view(), name='deleteUser'),
    url(r'%sdownload/%s(?P<file_name>%s+)/$' % (prefix, folder_and_path_regex, file_name_chars), base_view.DownloadView.as_view(), name='download'),
    url(r'%sdownload_zip/%s$' % (prefix, folder_and_path_regex), base_view.DownloadZipView.as_view(), name='downloadZip'),
    url(r'%seditGroup/(?P<group_name>\w+)$' % prefix, admin_views.EditGroupView.as_view(), name='editGroup'),
    url(r'%seditFolder/(?P<folder_name>.*?)/$' % prefix, admin_views.EditFolderView.as_view(), {'title': 'Edit Folder'}, name='editFolder'),
    url(r'%seditUser/(?P<username>.*?)/$' % prefix, user_views.EditUserView.as_view(), {'title': 'Edit User'}, name='editUser'),
    url(r'%sfolderAdmin/$' % prefix, admin_views.FolderAdminView.as_view(), name='folderAdmin'),
    url(r'%sgetNextImage/%s(?P<file_name>%s+)/$' % (prefix, folder_and_path_regex, file_name_chars),
        base_view.GetNextImageView.as_view(), name='getNextImage'),
    url(r'%shbAdmin/.*' % prefix, admin_views.AdminView.as_view(), name='admin'),
    url(r'%shbChangePassword/$' % prefix, user_views.ChangePasswordView.as_view(), name='changePassword'),
    url(r'%shbLogin/$' % prefix, base_view.LoginView.as_view(), name='login'),
    url(r'%shbLogout/$' % prefix, base_view.LogoutView.as_view(), name='logout'),
    url(r'%simageView/%s(?P<file_name>%s+)/$' % (prefix, folder_and_path_regex, file_name_chars), base_view.ImageView.as_view(), name='imageView'),
    url(r'%sgroupAdmin/$' % prefix, admin_views.GroupAdminView.as_view(), name='groupAdmin'),
    url(r'%supload/%s$' % (prefix, folder_and_path_regex), base_view.UploadView.as_view(), name='upload'),
    url(r'%suserAdmin/$' % prefix, user_views.UserAdminView.as_view(), name='userAdmin'),
    url(r'%sthumb/(?P<path>.*)' % prefix, base_view.ThumbView.as_view(), name='thumb'),
    url(r'%sjsreverse/$' % prefix, urls_js, name='js_reverse'),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'__debug__/', include(debug_toolbar.urls))
    ] + urlpatterns
