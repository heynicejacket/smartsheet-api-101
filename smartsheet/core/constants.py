ACCESS_TOKEN_SS = 'your access token'                               # Smartsheet API key

API_HEADER_SS = {                                                   # header for requests
    'Authorization': 'Bearer ' + ACCESS_TOKEN_SS,
    'Content-Type': 'application/json',
    'cache-control': 'no-cache',
    'Smartsheet-Change-Agent': 'splice-agent'
}

MIME_TYPES = {
    'images': {
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'bmp': 'image/bmp',
        'webp': 'image/webp',
        'svg': 'image/svg+xml',
        'tiff': 'image/tiff',
        'ico': 'image/x-icon'
    },
    'documents': {
        'pdf': 'application/pdf',
        'msword': 'application/msword',
        'word_docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'excel_xls': 'application/vnd.ms-excel',
        'excel_xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'powerpoint_ppt': 'application/vnd.ms-powerpoint',
        'powerpoint_pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'rtf': 'application/rtf',
        'odt': 'application/vnd.oasis.opendocument.text',
        'ods': 'application/vnd.oasis.opendocument.spreadsheet'
    },
    'text_and_code_files': {
        'plain_text': 'text/plain',
        'html': 'text/html',
        'css': 'text/css',
        'javascript': 'application/javascript',
        'json': 'application/json',
        'csv': 'text/csv'
    },
    'archives_and_compressed_files': {
        'zip': 'application/zip',
        '7z': 'application/x-7z-compressed',
        'rar': 'application/x-rar-compressed',
        'gzip': 'application/gzip',
        'tar': 'application/x-tar'
    },
    'audio': {
        'mp3': 'audio/mpeg',
        'ogg': 'audio/ogg',
        'wav': 'audio/wav',
        'aac': 'audio/aac',
        'flac': 'audio/flac'
    },
    'video': {
        'mp4': 'video/mp4',
        'avi': 'video/x-msvideo',
        'mov': 'video/quicktime',
        'wmv': 'video/x-ms-wmv',
        'webm': 'video/webm',
        'mpeg': 'video/mpeg'
    },
    'other': {
        'binary': 'application/octet-stream',
        'google_docs': 'application/vnd.google-apps.document',
        'google_sheets': 'application/vnd.google-apps.spreadsheet',
        'google_slides': 'application/vnd.google-apps.presentation'
    }
}

SS_ATTACHMENT_URL = 'attachments/'
SS_AUTOMATION_URL = 'automationrules/'
SS_BASE_URL = 'https://api.smartsheet.com/2.0/'
SS_CELL_IMAGE = 'cellimages/'
SS_CELL_HISTORY_URL = 'history?include=columnType'                  # sheets/{sheetId}/rows/{rowId}/columns/{columnId}/history?include=columnType'
SS_COLUMN_URL = 'columns/'
SS_COMMENT_URL = 'comments/'                                        # sheets/{sheetId}/comments/{commentId}
SS_CROSSSHEET_REFS_URL = 'crosssheetreferences/'                    # sheets/{sheetId}/crosssheetreferences/
SS_EMAIL_URL = 'emails/'
SS_EVENTS_URL = 'events/'
SS_FOLDER_URL = 'folders/'
SS_GROUPS_URL = 'groups/'
SS_IMAGE_URL = 'imageurls/'
SS_MEMBER_URL = 'members/'
SS_RETURN_ALL_URL = '?includeAll=True'
SS_ROW_URL = 'rows/'
SS_SEARCH_URL = 'search'
SS_SHARES_URL = 'shares/'
SS_SHEET_URL = 'sheets/'
SS_USER_URL = 'users/'
SS_VERSION_URL = 'versions/'
SS_WORKSPACE_URL = 'workspaces/'
