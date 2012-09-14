from django.shortcuts import render_to_response
from django.template import RequestContext
from html_browser.models import Folder
from django.contrib.auth.views import login, logout

def index(request):
    allFolders = Folder.objects.all()
    folders = []
    for folder in allFolders:
        if folder.userCanRead(request.user):
            folders.append(folder)
    print folders
    
    #debug code
    user = request.user
    print folders[0].userCanRead(user)
    
    return render_to_response('index.html',
        {'folders' : folders,
         'user' : request.user}
    )
    
def content(request):
    pass

def hbLogin(request):
    return login(request)

def hbLogout(request):
    return logout(request, '/hb/')

def hbChangePassword(request):
    c = RequestContext(request)
    return render_to_response('registration/change_password.html', c)

def hbChangePasswordResult(request):
    user = request.user
    errorMessage = None
    if user.check_password(request.POST['password']):
        newPw = request.POST['newPassword']
        confirmPw = request.POST['newPassword2']
        
        if newPw == confirmPw:
            user.set_password(newPw)
            user.save()
        else:
            errorMessage = "Passwords don't match"
    else:
        errorMessage = "Incorrect current password"
        
    if errorMessage == None:
        c = RequestContext(request)
        return render_to_response('registration/change_password_success.html', c)
    else:
        c = RequestContext(request, {'errorMessage' : errorMessage})
        return render_to_response('registration/change_password_fail.html', c)