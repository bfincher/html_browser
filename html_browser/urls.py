from django.conf.urls import url
from html_browser.models import Folder
from html_browser.views import base_view, content_view
from html_browser.views import adminViews as admin_views

fileNameChars = r'[\w !@#$%^&*()_\+-,\.]'
folderAndPathRegex = r'(?P<folderAndPathUrl>\w+(/%s+?)*)/' % fileNameChars

urlpatterns = [
    url(r'^$', base_view.IndexView.as_view(), name='index'),
    url(r'^hb/$', base_view.IndexView.as_view()),
    url(r'addFolder/.*', admin_views.AddFolderView.as_view(), {'title': 'Add Folder'}, name='addFolder'),
    url(r'addGroup/.*', admin_views.AddGroupView.as_view(), name='addGroup'),
    url(r'addUser/.*', admin_views.AddUserView.as_view(), {'title': 'Add User'}, name='addUser'),
    url(r'content/%s$' % folderAndPathRegex, content_view.ContentView.as_view(), name='content'),
    url(r'deleteFolder/(?P<folderName>.*?)$', admin_views.DeleteFolderView.as_view(), name='deleteFolder'),
    url(r'deleteGroup/(?P<groupName>\w+)', admin_views.DeleteGroupView.as_view(), name='deleteGroup'),
    url(r'deleteImage/%s$' % folderAndPathRegex, base_view.DeleteImageView.as_view(), name='deleteImage'),
    url(r'deleteUser/.*', admin_views.DeleteUserView.as_view(), name='deleteUser'),
    url(r'download/%s(?P<fileName>%s+)/$' % (folderAndPathRegex, fileNameChars), base_view.DownloadView.as_view(), name='download'),
    url(r'download_zip/%s$' % folderAndPathRegex, base_view.DownloadZipView.as_view(), name='downloadZip'),
    url(r'editGroup/(?P<groupName>\w+)?', admin_views.EditGroupView.as_view(), name='editGroup'),
    url(r'editFolder/(?P<folderName>.*?)/$', admin_views.EditFolderView.as_view(), {'title': 'Edit Folder'}, name='editFolder'),
    url(r'editUser/.*', admin_views.EditUserView.as_view(), {'title': 'Edit User'}, name='editUser'),
    url(r'folderAdmin/.*', admin_views.FolderAdminView.as_view(), name='folderAdmin'),
    url(r'getNextImage/%s(?P<fileName>%s+)/$' % (folderAndPathRegex, fileNameChars), base_view.GetNextImageView.as_view(), name='getNextImage'),
    url(r'hbAdmin/.*', admin_views.AdminView.as_view(), name='admin'),
    url(r'hbChangePassword/.*', admin_views.ChangePasswordView.as_view(), name='changePassword'),
    url(r'hbChangePasswordResult/.*', admin_views.ChangePasswordResultView.as_view(), name='changePasswordResult'),
    url(r'hbLogin/.*', base_view.LoginView.as_view(), name='login'),
    url(r'hbLogout/.*', base_view.LogoutView.as_view(), name='logout'),
    url(r'image_view/%s(?P<fileName>%s+)/$' % (folderAndPathRegex, fileNameChars), base_view.ImageView.as_view(), name='imageView'),
    url(r'groupAdmin/.*', admin_views.GroupAdminView.as_view(), name='groupAdmin'),
    url(r'upload/%s/$' % folderAndPathRegex, base_view.UploadView.as_view(), name='upload'),
    url(r'userAdmin/.*', admin_views.UserAdminView.as_view(), name='userAdmin'),
    url(r'thumb/', base_view.ThumbView.as_view(), name='thumb'),
    ]

for folder in Folder.objects.all():
    urlpatterns.append(url(r'__%s__/%s(?P<fileName>%s+)$' % (folder.name, folderAndPathRegex, fileNameChars),
                           base_view.DownloadImageView.as_view(),
                           name='download%sImage' % folder.name))
