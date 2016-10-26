from django.conf.urls import url
from html_browser.views import base_view as hb_views
from html_browser.views import adminViews as admin_views

urlpatterns = [
    url(r'^$', hb_views.IndexView.as_view()),
    url(r'^hb/$', hb_views.IndexView.as_view()),
    url(r'content/.*', hb_views.ContentView.as_view()),
    url(r'download_zip/.*', hb_views.DownloadZipView.as_view()),
    url(r'download/.*', hb_views.DownloadView.as_view),
    url(r'hbLogin/.*', hb_views.LoginView.as_view()),
    url(r'hbLogout/.*', hb_views.LogoutView.as_view()),
    url(r'upload/.*', hb_views.UploadView.as_view()),
    url(r'uploadAction/.*', hb_views.UploadActionView.as_view()),
    url(r'image_view/.*', hb_views.ImageView.as_view()),
    url(r'thumb/', hb_views.ThumbView.as_view()),
    url(r'deleteImage', hb_views.DeleteImageView.as_view()),
    url(r'getNextImage', hb_views.GetNextImageView.as_view()),
    url(r'hbAdmin/.*', admin_views.hbAdmin),
    url(r'userAdmin/.*', admin_views.userAdmin),
    url(r'userAdminAction/.*', admin_views.userAdminAction),
    url(r'editUser/.*', admin_views.editUser),
    url(r'addUser/.*', admin_views.addUser),
    url(r'editGroup/.*', admin_views.editGroup),
    url(r'folderAdmin/.*', admin_views.folderAdmin),
    url(r'folderAdminAction/.*', admin_views.folderAdminAction),
    url(r'editFolder/.*', admin_views.editFolder),
    url(r'addFolder/.*', admin_views.addFolder),
    url(r'groupAdmin/.*', admin_views.groupAdmin),
    url(r'groupAdminAction/.*', admin_views.groupAdminAction),
    url(r'hbChangePassword/.*', admin_views.hbChangePassword),
    url(r'hbChangePasswordResult/.*', admin_views.hbChangePasswordResult),
    ]
