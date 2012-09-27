class _constants():
#    class ConstError(TypeError): pass
    
    BASE_URL = '/hb/'
    CONTENT_URL = BASE_URL + 'content/'
    DOWNLOAD_URL = BASE_URL + "download/"
    ADMIN_URL = BASE_URL + "admin/"
    USER_ADMIN_URL = ADMIN_URL + "user/"
    ADD_USER_URL = USER_ADMIN_URL + "add/"
    ADD_USER_ACTION_URL = ADD_USER_URL + "action/"
    GROUP_ADMIN_URL = ADMIN_URL + "group/"
    ADD_GROUP_URL = GROUP_ADMIN_URL + "add/"
    ADD_GROUP_ACTION_URL = ADD_GROUP_URL + "action/"
    EDIT_GROUP_URL = GROUP_ADMIN_URL + "edit/"
    EDIT_GROUP_ACTION_URL = EDIT_GROUP_URL + "action/"
    MEDIA_URL = '/hbmedia/'
    IMAGE_URL = MEDIA_URL + 'images/'
    IMAGE_VIEW_URL = BASE_URL + "image_view/"
    THUMBNAIL_URL = BASE_URL + "__media__/"
    
    detailsViewType = 'details'
    listViewType = 'list'
    thumbnailsViewType = 'thumbnails'
    
    viewTypes = [detailsViewType, listViewType, thumbnailsViewType]
    
#    def __setattr__(self,name,value):
#        if self.__dict__.has_key(name):
#            raise self.ConstError, "Can't rebind const(%s)"%name
#        self.__dict__[name]=value
#        
#sys.modules[__name__]=_constants()
