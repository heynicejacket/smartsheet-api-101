import requests

from smartsheet.core.api import (
    rate_limiter_passthru
)

from smartsheet.core.constants import (
    API_HEADER_SS,
    SS_BASE_URL,
    SS_SHEET_URL,
    SS_SHARES_URL,
    SS_WORKSPACE_URL
)


def get_share():
    # todo: generic function to get share from any object
    pass


def update_share():
    # todo: generic function to update share from any object
    pass


def delete_share():
    # todo: generic function to delete share from any object
    pass


def delete_sheet_share(sheet_id, share_id, verbose=False):
    """
    Removes a shared user or group from specified Smartsheet.

    Returns as follows:

        {'message': 'SUCCESS', 'resultCode': 0}

    :param sheet_id:            str, required           sheet ID to remove shared user or group
    :param share_id:            str, required           share ID to remove from sheet
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response in JSON format
    """

    url = SS_BASE_URL + SS_SHEET_URL + f'{sheet_id}/' + SS_SHARES_URL + f'{share_id}/'
    print(url) if verbose else None

    return rate_limiter_passthru(url=url, request='delete', verbose=verbose)


def delete_workspace_share(workspace_id, share_id, verbose=False):
    """
    Remove a share from a Smartsheet workspace.

    :param workspace_id:        str, required           workspace ID from which share will be removed
    :param share_id:            str, required           share ID to remove
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response in JSON format
    """

    url = SS_BASE_URL + SS_WORKSPACE_URL + f'{workspace_id}/' + SS_SHARES_URL + f'{share_id}'

    user_data = get_workspace_shares(workspace_id=workspace_id, verbose=verbose)
    user_name = get_share_name_by_share_id(user_data, share_id)

    print(f'Removing {user_name} (share_id: {share_id}) from workspace {workspace_id}') if verbose else None
    response = rate_limiter_passthru(url=url, request='delete', return_all=True, verbose=verbose)

    return response


def get_share_id_by_share_name(share_data, share_name, verbose=False):
    """
    Given a list of dictionaries containing share data, returns user or group ID.

    Parameter share_date should be provided as follows:

        [
            {
                'id': 'ASbLKvfLDKJ',
                'type': 'USER',
                'userId': 2109142850895624,
                'email': 'matthew@nicejacket.cc',
                'name': 'Matthew Runde',
                'accessLevel': 'OWNER',
                'scope': 'ITEM',
                'createdAt': '2019-08-09T21:19:56Z',
                'modifiedAt': '2022-11-13T22:14:00Z'
            },
            ...
        ]

    :param share_data:          list of dict, required  list of user dicts to search
    :param share_name:          str, required           name of user or group share to return ID from
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    str or None             user or group share ID
    """

    share_name = next((user.get('id') for user in share_data if user.get('name') == share_name), None)
    print(share_name) if verbose else None

    return share_name


def get_share_name_by_share_id(share_data, share_id, verbose=False):
    """
    Given a list of dictionaries containing share data, returns user or group name.

    Parameter share_data should be provided as follows:

        [
            {
                'id': 'ASbLKvfLDKJ',
                'type': 'USER',
                'userId': 2109142850895624,
                'email': 'matthew@nicejacket.cc',
                'name': 'Matthew Runde',
                'accessLevel': 'OWNER',
                'scope': 'ITEM',
                'createdAt': '2019-08-09T21:19:56Z',
                'modifiedAt': '2022-11-13T22:14:00Z'
            },
            ...
        ]

    :param share_data:          list of dict, required  list of user dicts to search
    :param share_id:            str, required           user or user group share ID to return name from
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    str or None             user or group share name
    """

    share_name = next((user.get('name') for user in share_data if user.get('id') == share_id), None)
    print(share_name) if verbose else None

    return share_name


def get_sheet_shares(sheet_id, access_api_level=0, sharing_include=None, include_all=False, page=1, page_size=100, verbose=False):
    """
    Gets a list of all users and groups to whom specified Sheet is shared, and their access level.

    Returns as follows:

        {
            'pageNumber': 1,
            'totalPages': 1,
            'totalCount': 3,
            'data': [
                {
                    'id': 'ASbLKvfLDKJ',
                    'type': 'USER',
                    'userId': 2109142850895624,
                    'email': 'matthew@nicejacket.cc',
                    'name': 'Matthew Runde',
                    'accessLevel': 'OWNER',
                    'scope': 'ITEM',
                    'createdAt': '2019-08-09T21:19:56Z',
                    'modifiedAt': '2022-11-13T22:14:00Z'
                },
                ...
            ]
        }

    :param sheet_id:            str, required           sheet ID to retrieve share information for
    :param access_api_level:    int, optional           access API level; default 0 is 'VIEWER'
    :param sharing_include:     str, optional           defines scope of share ('ITEM', 'WORKSPACE')
    :param include_all:         bool, optional          if True, retrieves all results without permission
    :param page:                int, optional           page number to return
    :param page_size:           int, optional           number of items per page
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response with details of sheet shares
    """

    url = SS_BASE_URL + SS_SHEET_URL + f'{sheet_id}/' + SS_SHARES_URL
    print(url) if verbose else None

    params = {
        'accessApiLevel': access_api_level,
        'includeAll': str(include_all).lower(),
        'page': page,
        'pageSize': page_size
    }

    if sharing_include:
        params['sharingInclude'] = sharing_include

    print(f'Listing shares for sheet {sheet_id}...') if verbose else None

    return rate_limiter_passthru(url=url, request='get', return_all=False, verbose=verbose, params=params)


def get_workspace_shares(workspace_id, verbose=False):
    """
    Returns a list of dictionaries containing user or group share metadata for a given workspace.

    Returns as follows:

        [
            {
                'id': 'ASbLKvfLDKJ',
                'type': 'USER',
                'userId': 2109142850895624,
                'email': 'matthew@nicejacket.cc',
                'name': 'Matthew Runde',
                'accessLevel': 'OWNER',
                'scope': 'WORKSPACE',
                'createdAt': '2019-08-09T21:19:56Z',
                'modifiedAt': '2022-11-13T22:14:00Z'
            },
            ..
        ]

    :param workspace_id:        str, required           workspace ID to return share metadata from
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response in JSON format
    """

    url = SS_BASE_URL + SS_WORKSPACE_URL + f'{workspace_id}/' + SS_SHARES_URL
    print(url) if verbose else None

    return rate_limiter_passthru(url=url, request='get', verbose=verbose)[0]['data']


def share_sheet(sheet_id, shares, access_api_level=0, send_email=False, verbose=False):
    """
    Shares a sheet with specified users and groups.

    Options for 'shares' parameter is a list of dictionaries specifying share details, each containing:

        - 'email'               str                     user's email to shares
        - 'accessLevel'         str                     access level (e.g., 'ADMIN', 'COMMENTER', 'EDITOR', etc.)
        - 'message'             str                     message to notify recipient
        - 'subject'             str                     subject of email notification.
        - 'ccMe'                bool                    if True, send a copy to sharer

    Default access_api_level is 0 (VIEWER)

    :param sheet_id:            str, required           sheet ID to share
    :param shares:              list, required          list of dicts containing share details
    :param access_api_level:    list, optional          API access level
    :param send_email:          bool, optional          if True, send an email notification to recipients
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response with details of share
    """

    url = SS_BASE_URL + SS_SHEET_URL + f'{sheet_id}/' + SS_SHARES_URL

    params = {
        'accessApiLevel': access_api_level,
        'sendEmail': str(send_email).lower()
    }

    data = []
    for share in shares:
        share_data = {
            'email': share.get('email'),
            'accessLevel': share.get('accessLevel')
        }

        if 'message' in share:
            share_data['message'] = share['message']
        if 'subject' in share:
            share_data['subject'] = share['subject']
        if 'ccMe' in share:
            share_data['ccMe'] = share['ccMe']

        data.append(share_data)

    print(f'Sharing sheet {sheet_id} with {len(shares)} recipients...') if verbose else None

    response = rate_limiter_passthru(url=url, request='post', post_data=data, return_all=True, verbose=verbose, params=params)
    print(response) if verbose else None

    return response


def share_workspace(workspace_id, users, access_level, send_email=False, verbose=False):
    """
    Share a Smartsheet workspace with a list of users.

    The parameter access_level has the following access options:

        - 'ADMIN'           full administrative rights to manage workspace
        - 'COMMENTER'       can view and leave comments but cannot edit
        - 'EDITOR'          can edit workspace content but cannot manage shares
        - 'EDITOR_SHARE'    can edit workspace and manage shares
        - 'OWNER'           full ownership rights
        - 'VIEWER'          can view workspace but cannot make edits

    :param workspace_id:        str, required           workspace ID to share
    :param users:               list, required          list of user dicts with keys 'email' and 'accessLevel'
    :param access_level:        str, required           default access level to apply to all users
    :param send_email:          bool, optional          if True, send email to confirm sharing
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response in JSON format
    """

    url = SS_BASE_URL + SS_WORKSPACE_URL + f'{workspace_id}/' + SS_SHARES_URL

    share_body = [
        {
            'email': user['email'],
            'accessLevel': user.get('accessLevel', access_level),
            'sendEmail': send_email
        } for user in users
    ]

    print(f'Sharing workspace {workspace_id} with the following users: {share_body}') if verbose else None

    response = requests.post(url, json={'shares': share_body}, headers=API_HEADER_SS).json()        # todo: standardise
    return response
