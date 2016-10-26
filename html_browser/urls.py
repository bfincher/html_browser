from django.conf.urls import url
from html_browser.views import base_view, content_view
from html_browser.views import adminViews as admin_views

urlpatterns = [
    url(r'^$', base_view.IndexView.as_view()),
    url(r'^hb/$', base_view.IndexView.as_view()),
    url(r'content/.*', content_view.ContentView.as_view()),
    url(r'download_zip/.*', base_view.DownloadZipView.as_view()),
    url(r'download/.*', base_view.DownloadView.as_view),
    url(r'hbLogin/.*', base_view.LoginView.as_view()),
    url(r'hbLogout/.*', base_view.LogoutView.as_view()),
    url(r'upload/.*', base_view.UploadView.as_view()),
    url(r'uploadAction/.*', base_view.UploadActionView.as_view()),
    url(r'image_view/.*', base_view.ImageView.as_view()),
    url(r'thumb/', base_view.ThumbView.as_view()),
    url(r'deleteImage', base_view.DeleteImageView.as_view()),
    url(r'getNextImage', base_view.GetNextImageView.as_view()),
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
