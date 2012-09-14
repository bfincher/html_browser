from django.conf.urls import patterns, url

urlpatterns = patterns('html_browser.views',
    url(r'^$', 'index'),
    url(r'content/.*', 'content'),
    url(r'hbLogin/.*', 'hbLogin'),
    url(r'hbLogout/.*', 'hbLogout'),
    url(r'hbChangePassword/.*', 'hbChangePassword'),
    url(r'hbChangePasswordResult/.*', 'hbChangePasswordResult'),
    )
