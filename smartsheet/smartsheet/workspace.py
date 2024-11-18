from urllib.parse import urlencode

from smartsheet.core.api import (
    rate_limiter_passthru
)

from smartsheet.core.constants import (
    SS_BASE_URL,
    SS_FOLDER_URL,
    SS_RETURN_ALL_URL,
    SS_SHARES_URL,
    SS_WORKSPACE_URL
)

from smartsheet.core.toolkit import (
    get_slim_metadata
)


def create_workspace(workspace_name, verbose=False):
    """
    Create a new workspace in Smartsheet.

    :param workspace_name:      str, required           name of workspace to create
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response in JSON format
    """

    url = SS_BASE_URL + SS_WORKSPACE_URL

    payload = {'name': workspace_name}

    print(f'Creating workspace: {workspace_name}') if verbose else None
    response = rate_limiter_passthru(url=url, request='post', post_data=payload, return_all=True, verbose=verbose)
    print(response) if verbose else None

    return response


def copy_workspace(workspace_id, new_workspace_name, include='all', skip_remap=None, verbose=False):
    """
    Copy an existing workspace in Smartsheet.

    Options for 'include' parameter should be formatted as a string (e.g. 'attachments,data') and are as follows:

        all, attachments, brand, cellLinks, data, discussions, filters, forms, ruleRecipients, rules, shares

    Options for 'skip_remap' parameter should be formatted as a string (e.g. 'cellLinks,reports') and are as follows:

        cellLinks, reports, sheetHyperlinks, sights

    :param workspace_id:        str, required           ID of workspace to copy
    :param new_workspace_name:  str, required           name of new workspace
    :param include:             str, optional           comma-separated list of elements to include in copy
    :param skip_remap:          str, optional           comma-separated list of references to exclude from copy
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response in JSON format
    """

    url = SS_BASE_URL + SS_WORKSPACE_URL + f'{workspace_id}/copy'

    params = {'include': include}

    if skip_remap:
        params['skipRemap'] = skip_remap

    url_with_params = f"{url}?{urlencode(params)}"

    payload = {'newName': new_workspace_name}

    print(f'Copying workspace: {workspace_id} to new workspace: {new_workspace_name}') if verbose else None
    response = rate_limiter_passthru(url=url_with_params, request='post', post_data=payload, return_all=True, verbose=verbose)
    print(response) if verbose else None

    return response


def delete_workspace(workspace_id, verbose=False):
    """
    Delete an existing workspace in Smartsheet.

    Returns a JSON response as follows:

        {'message': 'SUCCESS', 'resultCode': 0}

    :param workspace_id:        str, required           ID of workspace to delete
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    bool                    if True, deletion was successful; else False
    """

    url = SS_BASE_URL + SS_WORKSPACE_URL + f'{workspace_id}'

    print(f'Deleting workspace: {workspace_id}') if verbose else None
    response = rate_limiter_passthru(url=url, request='delete', return_all=True, verbose=verbose)
    print(response) if verbose else None

    return response


def get_all_workspaces(slim_metadata=None, additional_keys=None, verbose=False):
    """
    Returns a list containing metadata for all workspaces user has access to.

    :param slim_metadata        bool, optional          if True, returns a limited JSON dict
    :param additional_keys      list, optional          additional keys to preserve in metadata
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response in JSON format
    """

    url = SS_BASE_URL + SS_WORKSPACE_URL + SS_RETURN_ALL_URL
    workspace_json = rate_limiter_passthru(url=url, request='get', verbose=verbose)[0]['data']

    if slim_metadata:
        workspace_json = get_slim_metadata(
            data=workspace_json,
            base_keys=None,
            additional_keys=additional_keys,
            verbose=verbose
        )

    return workspace_json


def get_workspace(workspace_id, verbose=False):
    """
    Returns a dictionary containing metadata for workspace.

    :param workspace_id:        str, required           workspace ID to retrieve metadata from
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response in JSON format
    """

    url = SS_BASE_URL + SS_WORKSPACE_URL + f'{workspace_id}'
    response = rate_limiter_passthru(url=url, request='get', verbose=verbose)

    return response


def get_workspace_folders(workspace_id, slim_metadata=False, additional_keys=None, verbose=False):
    """
    Returns a list of dictionaries containing metadata for all folders in a given workspace.

    Returns as follows:

        [
            {
                'pageNumber': 1,
                'pageSize': 100,
                'totalPages': 1,
                'totalCount': 3,
                'data': [
                    {
                        'id': 2109142850895624,
                        'name': 'Project Folder',
                        'permalink': 'https://app.smartsheet.com/folders/khXfXF5SEjmdFT2mh1'
                    },
                    ...
                ]
            }
        ]

    :param workspace_id:        str, required           workspace ID to retrieve folder metadata from
    :param slim_metadata        bool, optional          if True, returns a limited JSON dict
    :param additional_keys      list, optional          additional keys to preserve in metadata
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response in JSON format
    """

    url = SS_BASE_URL + SS_WORKSPACE_URL + f'{workspace_id}/' + SS_FOLDER_URL
    print(url) if verbose else None

    workspace_folder_json = rate_limiter_passthru(url=url, request='get', verbose=verbose)

    if slim_metadata:
        workspace_folder_json = get_slim_metadata(
            data=workspace_folder_json,
            base_keys=None,
            additional_keys=additional_keys,
            verbose=verbose
        )

    print(workspace_folder_json) if verbose else None

    return workspace_folder_json


def update_workspace(workspace_id, workspace_name=None, verbose=False):
    """
    Update an existing workspace in Smartsheet.

    Returns as follows:

        {
            'message': 'SUCCESS',
            'resultCode': 0,
            'result': {
                'id': 2109142850895624,
                'name': 'Project Workspace',
                'accessLevel': 'OWNER',
                'permalink': 'https://app.smartsheet.com/folders/khXfXF5SEjmdFT2mh1'
            }
        }

    :param workspace_id:        str, required           ID of workspace to update
    :param workspace_name:      str, optional           new name of workspace
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response in JSON format
    """

    url = SS_BASE_URL + SS_WORKSPACE_URL + f'{workspace_id}'

    payload = {}
    if workspace_name:
        payload['name'] = workspace_name

    if not payload:
        print('No updates provided.') if verbose else None
        return None

    print(f'Updating workspace to \'{workspace_id}\'') if verbose else None
    response = rate_limiter_passthru(url=url, request='put', post_data=payload, return_all=True, verbose=verbose)
    print(response) if verbose else None

    return response


def update_workspace_share(workspace_id, share_id, access_level, access_api_level=0, verbose=False):
    """
    Update access level of a user or group for a specified workspace in Smartsheet.

    This function allows you to update access level for an existing user or group share within a workspace.

    Only system administrators can perform this operation.

    The parameter access_level has the following access options:

        - 'ADMIN'           full administrative rights to manage workspace
        - 'COMMENTER'       can view and leave comments but cannot edit
        - 'EDITOR'          can edit workspace content but cannot manage shares
        - 'EDITOR_SHARE'    can edit workspace and manage shares
        - 'OWNER'           full ownership rights
        - 'VIEWER'          can view workspace but cannot make edits

    Response as follows:

        {
            'version': 2,
            'resultCode': 0,
            'message': 'SUCCESS'
        }

    :param workspace_id:        str, required           ID of workspace to update
    :param share_id:            str, required           ID of user or group share to update
    :param access_level:        str, required           access level to grand user or group share
    :param access_api_level:    int, optional           0 enables default VIEWER access, 1 enables COMMENTER access
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    dict                    API response
    """

    url = SS_BASE_URL + SS_WORKSPACE_URL + f'{workspace_id}/' + SS_SHARES_URL + f'{share_id}'

    params = {'accessApiLevel': access_api_level}
    payload = {'accessLevel': access_level}

    print(f'Updating share: {share_id} in workspace: {workspace_id} to access level: {access_level}') if verbose else None
    response = rate_limiter_passthru(url=url, request='put', post_data=payload, return_all=True, verbose=verbose, params=params)

    return response
