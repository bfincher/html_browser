from django.conf.urls import url
from html_browser import views as hb_views
from html_browser import adminViews as admin_views

urlpatterns = [
    url(r'^$', hb_views.index),
    url(r'^hb/$', hb_views.index),
    url(r'content/.*', hb_views.content),
    url(r'download_zip/.*', hb_views.downloadZip),
    url(r'download/.*', hb_views.download),
    url(r'hbLogin/.*', hb_views.hbLogin),
    url(r'hbLogout/.*', hb_views.hbLogout),
    url(r'upload/.*', hb_views.upload),
    url(r'image_view/.*', hb_views.imageView),
    url(r'thumb/', hb_views.thumb),
    url(r'deleteImage', hb_views.deleteImage),
    url(r'getNextImage', hb_views.getNextImage),
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
