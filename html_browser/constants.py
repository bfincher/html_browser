class _constants():
    BASE_URL = '/hb/'
    CONTENT_URL = BASE_URL + 'content/'
    CONTENT_ACTION_URL = CONTENT_URL
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
    MEDIA_URL = "/hbmedia/"
    IMAGE_URL = MEDIA_URL + 'images/'
    IMAGE_VIEW_URL = BASE_URL + "image_view/"
    THUMBNAIL_URL = MEDIA_URL + "/thumbs/"
    
    detailsViewType = 'details'
    listViewType = 'list'
    thumbnailsViewType = 'thumbnails'
    
    viewTypes = [detailsViewType, listViewType, thumbnailsViewType]
