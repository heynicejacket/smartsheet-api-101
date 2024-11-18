import requests

from smartsheet.core.constants import (
    API_HEADER_SS,
    SS_BASE_URL,
    SS_FOLDER_URL,
    SS_RETURN_ALL_URL,
    SS_WORKSPACE_URL
)

from smartsheet.core.sql import (
    rate_limiter_passthru
)

from smartsheet.core.toolkit import (
    get_slim_metadata
)


def get_all_folders(slim_metadata=False, additional_keys=None, verbose=False):
    """
    Returns JSON dict containing metadata for all folders owner of API key has access to.

    :param slim_metadata        bool, optional          if True, returns a limited JSON dict
    :param additional_keys      list, optional          additional keys to preserve in metadata
    :param verbose:             bool, optional          If True, print status to terminal.
    :return:                    JSON                    API response in JSON format
    """

    url = SS_BASE_URL + SS_FOLDER_URL + SS_RETURN_ALL_URL
    print(url) if verbose else None

    all_folders_json = rate_limiter_passthru(url=url, request='get', verbose=verbose)[0]['data']

    if slim_metadata:
        all_folders_json = get_slim_metadata(
            data=all_folders_json,
            base_keys=None,
            additional_keys=additional_keys,
            verbose=verbose
        )

    return all_folders_json


def create_folder(folder_name, workspace_id=None, folder_id=None, home=False, verbose=False):
    """
    Creates new folder within workspace, folder, or personal home space in Smartsheet.

    If 'workspace_id' provided, creates folder in workspace; if 'folder_id', creates folder in folder; if 'home',
    folder created in personal home space.

    Given 'workspace_id', returns as follows:                           # todo: add example

    Given 'folder_id', returns as follows:                              # todo: add example

    Given 'home', returns as follows:

        {
            'message': 'SUCCESS',
            'resultCode': 0,
            'result': {
                'id': 2109142850895624,
                'name': 'New Folder',
                'permalink': 'https://app.smartsheet.com/folders/khXfXF5SEjmdFT2mh1P17HW'
            }
        }

    :param folder_name:         str, optional           name of folder to create
    :param workspace_id:        str, required           workspace ID where folder would be created
    :param folder_id:           str, optional           folder ID where folder would be created
    :param home:                bool, optional          if True, creates folder in personal home space
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response in JSON format
    """

    if sum([bool(workspace_id), bool(folder_id), home]) != 1:
        raise ValueError('Specify only one of workspace_id, folder_id, or home.')

    if workspace_id:
        url = SS_BASE_URL + SS_WORKSPACE_URL + f'{workspace_id}/' + SS_FOLDER_URL
    elif folder_id:
        url = SS_BASE_URL + SS_FOLDER_URL + f'{folder_id}/' + SS_FOLDER_URL
    elif home:
        url = SS_BASE_URL + 'home/' + SS_FOLDER_URL
    print(url) if verbose else None

    location = 'home' if home else ('workspace' if workspace_id else 'folder')
    print(f'Creating folder: {folder_name} in {location}: {workspace_id or folder_id or "home"}')

    payload = {'name': folder_name}

    response = rate_limiter_passthru(url=url, request='post', post_data=payload, return_all=True, verbose=verbose)
    print(response) if verbose else None

    return response


def get_folders_in_folder(folder_id, include_all=True, verbose=False):
    """
    Returns complete list of folders in specified folder using Smartsheet API. If include_all is True, loops until
    returning all results as one JSON dict; if False, returns paginated results.

    Returns as follows:

        [
            {
                'id': 2109142850895624,
                'name': 'New Folder',
                'permalink': 'https://app.smartsheet.com/folders/khXfXF5SEjmdFT2mh1P17HW'
            },
            ...
        ]

    :param folder_id:           str, required           folder ID to retrieve folders from
    :param include_all:         bool, optional          if True, retrieves all results without pagination
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response in JSON format
    """

    url = SS_BASE_URL + SS_FOLDER_URL + f'{folder_id}/' + SS_FOLDER_URL
    print(url) if verbose else None

    params = {'includeAll': str(include_all).lower()}
    all_folders = []
    page = 1

    while True:
        params['page'] = page
        print(f'Fetching page {page} of folders in folder {folder_id}...') if verbose else None

        response = requests.get(url, headers=API_HEADER_SS, params=params)
        if response.ok:
            data = response.json()
            all_folders.extend(data.get('data', []))
            if not data.get('morePages'):
                break
            page += 1
        else:
            print(f'Failed to retrieve folders: {response.status_code} - {response.text}') if verbose else None
            return {'error': response.status_code, 'message': response.text}

    print('Retrieved all folders successfully.') if verbose else None
    return all_folders
