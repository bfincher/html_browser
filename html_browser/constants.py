import sys
class _constants():
#    class ConstError(TypeError): pass
    
    BASE_URL = '/hb/'
    CONTENT_URL = BASE_URL + 'content/'
    DOWNLOAD_URL = BASE_URL + "download/"
    ADMIN_URL = BASE_URL + "admin/"
    USER_ADMIN_URL = ADMIN_URL + "user/"
    ADD_USER_URL = USER_ADMIN_URL + "add/"
    ADD_USER_ACTION_URL = ADD_USER_URL + "action/"
    IMAGE_URL = 'http://www.fincherhome.com/hbstuff/images/'
    
    viewTypes = ['details', 'list', 'thumbnails']
    
#    def __setattr__(self,name,value):
#        if self.__dict__.has_key(name):
#            raise self.ConstError, "Can't rebind const(%s)"%name
#        self.__dict__[name]=value
#        
#sys.modules[__name__]=_constants()
