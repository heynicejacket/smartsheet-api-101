import requests

from smartsheet.core.constants import (
    API_HEADER_SS,
    SS_BASE_URL,
    SS_GROUPS_URL,
    SS_MEMBER_URL
)

from smartsheet.core.sql import (
    rate_limiter_passthru
)

from smartsheet.core.toolkit import (
    get_slim_metadata
)


def delete_user_from_group(group_id, user_id, verbose=False):
    """
    Deletes a user from an existing user group in Smartsheet.

    Returns as follows:

        {'message': 'SUCCESS', 'resultCode': 0}

    :param group_id:            str, required           user group ID to modify
    :param user_id:             str, required           user ID to remove from user group
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response in JSON format
    """

    url = SS_BASE_URL + SS_GROUPS_URL + f'{group_id}' + SS_MEMBER_URL + f'{user_id}'
    print(url) if verbose else None

    return rate_limiter_passthru(url=url, request='delete', return_all=True, verbose=verbose)


def add_users_to_group(group_id, user_emails, verbose=False):
    """
    Adds multiple users to an existing group in Smartsheet.

    Returns as follows:

        {
            'message': 'SUCCESS',
            'resultCode': 0,
            'result': [
                {
                    'id': 2109142850895624,
                    'email': 'matthew@nicejacket.cc',
                    'firstName': 'Matthew',
                    'lastName': 'Runde',
                    'name': 'Matthew Runde'
                }
            ]
        }

    :param group_id:            str, required           user group ID to add users to
    :param user_emails:         list, required          list of user email addresses to add to group
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response in JSON format
    """

    url = SS_BASE_URL + SS_GROUPS_URL + f'{group_id}/' + SS_MEMBER_URL

    member_data = [{'email': email} for email in user_emails]

    print(f'Adding users with emails: {user_emails} to group with ID: {group_id}') if verbose else None

    response = requests.post(url, headers=API_HEADER_SS, json=member_data)      # todo: standardise
    return response


def delete_group(group_id, verbose=False):
    """
    Deletes a user group from Smartsheet.

    Returns as follows:

        {'message': 'SUCCESS', 'resultCode': 0}

    :param group_id:            str, required           user group ID to delete
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response in JSON format
    """

    url = SS_BASE_URL + SS_GROUPS_URL + f'{group_id}'
    print(url) if verbose else None

    return rate_limiter_passthru(url=url, request='delete', return_all=True, verbose=verbose)


def get_all_groups(slim_metadata=False, additional_keys=None, verbose=False):
    """
    Returns a JSON dictionary of details for all groups a user has access to.

    Returns as follows:

        [
            {
                'id': 2109142850895624,
                'name': 'User Group',
                'owner': 'matthew@nicejacket.cc',
                'ownerId': 2109142850895624,
                'createdAt': '2019-08-09T21:19:56Z',
                'modifiedAt': '2022-11-13T22:14:00Z'
            },
            ...
        ]

    :param slim_metadata        bool, optional          if True, returns a limited JSON dict
    :param additional_keys      list, optional          additional keys to preserve in metadata
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response in JSON format
    """

    url = SS_BASE_URL + SS_GROUPS_URL
    print(url) if verbose else None

    response = rate_limiter_passthru(url=url, request='get', verbose=verbose)

    if slim_metadata:
        response = get_slim_metadata(
            data=response[0]['data'],
            base_keys=None,
            additional_keys=additional_keys,
            verbose=verbose
        )

    return response


def get_group(group_id, slim_metadata=False, base_keys=None, additional_keys=None, verbose=False):
    """
    Returns a JSON dictionary of details for a user groups in Smartsheet.

    Returns as follows:

        [
            {
                'id': 2109142850895624,
                'name': 'User Group',
                'description': 'Description of group.',
                'owner': 'matthew@nicejacket.cc',
                'ownerId': 2109142850895624,
                'members': [
                    {
                        'id': 2109142850895624,
                        'email': 'matthew@nicejacket.cc',
                        'firstName': 'Matthew',
                        'lastName': 'Runde',
                        'name': 'Matthew Runde'
                    },
                    ...
                ],
                'createdAt': '2019-06-13T20:44:29Z',
                'modifiedAt': '2019-06-14T19:30:22Z'
            }
        ]

    :param group_id:            str, required           user group ID to retrieve metadata for
    :param slim_metadata        bool, optional          if True, returns a limited JSON dict
    :param base_keys:           list, optional          if not None, list of alternate base_keys to retrieve
    :param additional_keys      list, optional          additional keys to preserve in metadata
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response in JSON format
    """

    url = SS_BASE_URL + SS_GROUPS_URL + f'{group_id}'
    print(url) if verbose else None

    response = rate_limiter_passthru(url=url, request='get', verbose=verbose)

    if slim_metadata:
        response = get_slim_metadata(
            data=response,
            base_keys=base_keys,
            additional_keys=additional_keys,
            verbose=verbose
        )

    return response


def create_group(name, description=None, members=None, verbose=False):
    """
    Creates a new group in Smartsheet.

    Returns as follows:

        {
            'message': 'SUCCESS',
            'resultCode': 0,
            'result': {
                'id': 2109142850895624,
                'name': 'User Group',
                'description': 'Description of group.',
                'owner': 'matthew@nicejacket.cc',
                'ownerId': 2109142850895624,
                'members': [
                    {
                        'id': 2109142850895624,
                        'email': 'matthew@nicejacket.cc',
                        'firstName': 'Matthew',
                        'lastName': 'Runde',
                        'name': 'Matthew Runde'
                    },
                    ...
                ],
                'createdAt': '2019-06-13T20:44:29Z',
                'modifiedAt': '2019-06-14T19:30:22Z'
            }
        }

    :param name:                str, required           user group name (must be unique to organisation)
    :param description:         str, optional           group description
    :param members:             list, optional          list of dicts of member details to add to group, must contain 'email'
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response in JSON format
    """

    url = SS_BASE_URL + SS_GROUPS_URL

    group_data = {
        'name': name,
        'description': description,
        'members': [{'email': member['email']} for member in members] if members else []
    }

    response = requests.post(url, headers=API_HEADER_SS, json=group_data)
    return response


def update_group(group_id, name=None, description=None, owner_id=None, verbose=False):
    """
    Updates an existing group in Smartsheet.

    Returns as follows:

        {
            'message': 'SUCCESS',
            'resultCode': 0,
            'result': {
                'id': 2109142850895624,
                'name': 'Updated Group',
                'description': 'Updated group description.',
                'owner': 'matthew@nicejacket.cc',
                'ownerId': 2109142850895624,
                'createdAt': '2019-06-13T20:44:29Z',
                'modifiedAt': '2019-06-14T19:30:22Z'
            }
        }

    :param group_id:            str, required           user group ID to update
    :param name:                str, optional           new user group name (must be unique to organisation)
    :param description:         str, optional           new user group description
    :param owner_id:            str, optional           new user group owner (user) ID (must be admin)
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response in JSON format
    """

    url = SS_BASE_URL + SS_GROUPS_URL + f'{group_id}'

    group_data = {}
    if name:
        group_data['name'] = name
    if description:
        group_data['description'] = description
    if owner_id:
        group_data['ownerId'] = owner_id

    if verbose:
        print(f'Updating group with ID: {group_id}')
        if name:
            print(f'New Name: {name}')
        if description:
            print(f'New Description: {description}')
        if owner_id:
            print(f'New Owner ID: {owner_id}')

    response = requests.put(url, headers=API_HEADER_SS, json=group_data)        # todo: standardise
    return response
