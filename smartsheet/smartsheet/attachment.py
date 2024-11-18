import requests
import pandas as pd
from io import BytesIO

from smartsheet.core.constants import (
    SS_ATTACHMENT_URL,
    SS_BASE_URL,
    SS_ROW_URL,
    SS_SHEET_URL,
    SS_VERSION_URL
)

from smartsheet.core.sql import (
    rate_limiter_passthru,
    ss_post_upload
)

from smartsheet.core.toolkit import (
    get_file_info,
    get_slim_metadata
)


def attachment_to_df(attachment_json, verbose=False):
    """
    Given a CSV or Excel attachment, covert to DataFrame.

    :param attachment_json:     JSON, required          attachment data JSON
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    df                      DataFrame of attachment
    """

    file_url, file_name, _ = get_file_info(attachment_json=attachment_json, file_path=None)

    print(f'Downloading file: {file_name} from {file_url}') if verbose else None

    try:
        response = requests.get(file_url, allow_redirects=True)                 # make direct request to file URL
        response.raise_for_status()
        file_data = BytesIO(response.content)                                   # load file content into BytesIO stream

        if file_name.endswith('.csv'):
            df = pd.read_csv(file_data)
            print(f'Loaded {file_name} as a CSV into a DataFrame') if verbose else None
        elif file_name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_data)
            print(f'Loaded {file_name} as an Excel file into a DataFrame') if verbose else None
        else:
            raise ValueError('Unsupported file format. Only CSV and Excel files are supported.')

        return df

    except requests.exceptions.HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}') if verbose else None
    except Exception as e:
        print(f'Error loading file: {e}') if verbose else None

    return None


def delete_attachment(sheet_id, attachment_id, delete_all_versions=False, verbose=False):
    """
    Given sheet and attachment IDs, delete an attachment from a Smartsheet.

    :param sheet_id:            str, required           sheet ID
    :param attachment_id:       str, required           attachment ID
    :param delete_all_versions: bool, optional          if True, delete all versions of attachment
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response of deletion status
    """

    if delete_all_versions:
        url = SS_BASE_URL + SS_SHEET_URL + f'{sheet_id}/' + SS_ATTACHMENT_URL + f'{attachment_id}/' + SS_VERSION_URL
    else:
        url = SS_BASE_URL + SS_SHEET_URL + f'{sheet_id}/' + SS_ATTACHMENT_URL + f'{attachment_id}/'
    print(url) if verbose else None

    return rate_limiter_passthru(url=url, request='delete', verbose=verbose)


def download_attachment(attachment_json, file_path, verbose=False):
    """-
    Given a JSON from get_attachment_json() and a file path, download attachment from a Smartsheet.

    :param attachment_json:     JSON, required          attachment JSON
    :param file_path:           str, required           path to download file to
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    None
    """

    file_url, file_name, full_save_path = get_file_info(attachment_json, file_path)

    print(f'Downloading file: {file_name} from {file_url}') if verbose else None
    response = rate_limiter_passthru(url=file_url, request='get', verbose=verbose)

    if response.status_code == 200:
        with open(full_save_path, 'wb') as file:
            file.write(response.content)
        print(f'File downloaded successfully and saved as {full_save_path}') if verbose else None
    else:
        print(f'Failed to download file. Status code: {response.status_code}') if verbose else None
        response.raise_for_status()


def get_attachment_json(sheet_id, attachment_id, return_url=False, verbose=False):
    """
    Given a sheet_id and attachment_id, returns complete JSON of attachment data, or attachment URL.

    If return_url is False, complete attachment JSON is as follows:

        [
            {
                'id': 2109142850895624,
                'name': 'project_summary.xlsx',
                'url': 'https://s3.amazonaws.com/.../project_summary.xlsx...',
                'attachmentType': 'FILE',
                'mimeType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'urlExpiresInMillis': 120000,
                'sizeInKb': 20,
                'parentType': 'ROW',
                'parentId': 2109142850895624,
                'createdAt': '2018-05-01T11:37:15Z',
                'createdBy': {
                    'name': 'Matthew Runde',
                    'email': 'matthew@nicejacket.cc'
                }
            }
        ]

    If return_url is True, returns only URL, as 'https://s3.amazonaws.com/.../project_summary.xlsx...'

    :param sheet_id:            str, required           sheet ID to return attachment URLs
    :param attachment_id:       str, required           attachment ID to return file URL
    :param return_url:          bool, optional          if True, return only attachment URL
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON or URL             API response of attachment details or attachment URL
    """

    url = SS_BASE_URL + SS_SHEET_URL + f'{sheet_id}/' + SS_ATTACHMENT_URL + f'{attachment_id}/'
    attachment_json = rate_limiter_passthru(url=url, request='get', verbose=verbose)

    if return_url:
        attachment_json = attachment_json[0]['url']

    return attachment_json


def get_attachment_versions(sheet_id, attachment_id, verbose=False):
    """
    Given a sheet ID and attachment ID, returns a JSON dictionary listing details of all versions of attachment.

    Returns a JSON as follows:

        [
            {
                'id': 2109142850895624,
                'versionNumber': 3,
                'createdAt': '2018-01-15T19:30:00Z',
                'createdBy': {
                    'id': 2109142850895624,
                    'name': 'Matthew Runde',
                    'email': 'matthew@nicejacket.cc'
                },
                'name': 'project_summary.pdf',
                'url': 'https://api.smartsheet.com/2.0/attachments/2109142850895624/versions/3'
            },
            ...
        ]

    :param sheet_id:            str, required           sheet ID to retrieve attachments from
    :param attachment_id:       str, required           attachment ID to retrieve
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response containing attachment versions
    """

    url = SS_BASE_URL + SS_SHEET_URL + f'{sheet_id}/' + SS_ATTACHMENT_URL + f'{attachment_id}/' + SS_VERSION_URL
    print(url) if verbose else None

    return rate_limiter_passthru(url=url, request='get', verbose=verbose)[0]['data']


def get_sheet_attachments_json(sheet_id, row_id=None, slim_metadata=False, additional_keys=None, verbose=False):
    """
    Returns JSON containing detail of all attachments in a given Smartsheet.

    Returns a JSON as follows:

        [
            {
                'id': 2109142850895624,
                'name': 'project_summary.xlsx',
                'attachmentType': 'FILE',
                'mimeType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'sizeInKb': 20,
                'parentType': 'ROW',
                'parentId': 2109142850895624,
                'createdAt': '2018-05-01T11:37:15Z',
                'createdBy': {
                    'name': 'Matthew Runde',
                    'email': 'matthew@nicejacket.cc'
                }
            },
            ...
        ]

    With slim_metadata, default return as follows:

        [
            {
                'id': 2109142850895624,
                'name': 'project_summary.xlsx',
                'parentId': 2109142850895624,
            },
            ...
        ]

    :param sheet_id:            str, required           sheet ID to retrieve attachment from
    :param row_id:              str, required           row ID to retrieve attachment from
    :param slim_metadata        bool, optional          if True, returns a limited JSON dict
    :param additional_keys      list, optional          additional keys to preserve in metadata
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response in JSON format
    """

    if row_id:
        url = SS_BASE_URL + SS_SHEET_URL + f'{sheet_id}/' + SS_ROW_URL + f'{row_id}/' + SS_ATTACHMENT_URL
    else:
        url = SS_BASE_URL + SS_SHEET_URL + f'{sheet_id}/' + SS_ATTACHMENT_URL
    attachment_json = rate_limiter_passthru(url=url, request='get', verbose=verbose)[0]['data']

    if additional_keys is None:
        additional_keys = ['parentId']

    if slim_metadata:
        attachment_json = get_slim_metadata(
            data=attachment_json,
            base_keys=None,
            additional_keys=additional_keys,
            verbose=verbose
        )

    return attachment_json


def upload_new_file_to_smartsheet(sheet_id, mime_type, filepath, row_id=None, verbose=False):
    """
    Uploads a file to a specific row or sheet in a Smartsheet.

    :param sheet_id:            str, required           sheet ID to upload new file attachment
    :param row_id:              str, required           row ID where file will be attached
    :param mime_type:           str, required           MIME type of file being uploaded (e.g., 'application/pdf')
    :param filepath:            str, required           path to file to be uploaded
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response containing upload details
    """

    if row_id:
        url = SS_BASE_URL + SS_SHEET_URL + f'{sheet_id}/' + SS_ROW_URL + f'{row_id}/' + SS_ATTACHMENT_URL
    else:
        url = SS_BASE_URL + SS_SHEET_URL + f'{sheet_id}/' + SS_ATTACHMENT_URL
    print(url) if verbose else None

    return ss_post_upload(url=url, mime_type=mime_type, filepath=filepath, verbose=verbose)


def upload_new_file_version_to_smartsheet(sheet_id, attachment_id, mime_type, filepath, verbose=False):
    """
    Uploads a new version of an attachment to Smartsheet.

    :param sheet_id:            str, required           sheet ID to upload new file attachment
    :param attachment_id:       str, required           attachment ID to be updated with new version
    :param mime_type:           str, required           MIME type of file being uploaded (e.g., 'application/pdf')
    :param filepath:            str, required           path to file to be uploaded
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response confirming upload or error details
    """

    url = SS_BASE_URL + SS_SHEET_URL + f'{sheet_id}/' + SS_ATTACHMENT_URL + f'{attachment_id}/' + SS_VERSION_URL
    print(url) if verbose else None

    return ss_post_upload(url=url, mime_type=mime_type, filepath=filepath, verbose=verbose)
