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
    #url(r'admin/user/add/result/.*', 'addUserResult'),    
    url(r'admin/user/add/$', 'addUser'),
    url(r'admin/user/$', 'userAdmin'),
    url(r'admin/group/$', 'groupAdmin'),
    url(r'admin/group/add/$', 'addGroup'),
    #url(r'admin/group/add/action/.*', 'addGroupAction'),
    #url(r'admin/group/add/result/.*', 'addGroupResult'),
    #url(r'admin/group/edit/.*', 'editGroup'),
    #url(r'admin/group/edit/action/.*', 'editGroupAction'),
    #url(r'admin/$', 'admin'),
    )
