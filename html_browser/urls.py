from django.conf.urls import patterns, url

urlpatterns = patterns('html_browser.views',
    url(r'^$', 'index'),
    url(r'content/.*', 'content'),
    url(r'download/.*', 'download'),
    url(r'hbLogin/.*', 'hbLogin'),
    url(r'hbLogout/.*', 'hbLogout'),
    url(r'hbChangePassword/.*', 'hbChangePassword'),
    url(r'hbChangePasswordResult/.*', 'hbChangePasswordResult'),
    url(r'admin/user/add/action/.*', 'addUserAction'),
    url(r'admin/user/add/result/.*', 'addUserResult'),    
    url(r'admin/user/add/$', 'addUser'),
    url(r'admin/user/$', 'userAdmin'),
    url(r'admin/$', 'admin'),
    )
