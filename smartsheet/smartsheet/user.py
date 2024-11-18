from smartsheet.core.api import (
    rate_limiter_passthru
)

from smartsheet.core.constants import (
    SS_BASE_URL,
    SS_USER_URL
)


def add_user(first_name, last_name, email):
    """
    Given a first name, last name, and email, sends user request on behalf of owner of Smartsheet API token. User will
    receive an email asking to create a Smartsheet account.

    :param first_name:          str, required           user first name
    :param last_name:           str, required           user last name
    :param email:               str, required           complete email address
    :return:                    JSON                    API response in JSON format
    """

    user_json = f'{{"firstName": "{first_name}", "lastName": "{last_name}", "email": "{email}", "admin": false, "licensedSheetCreator": false}}'

    response = rate_limiter_passthru(
        url=SS_BASE_URL,
        request='post',
        post_data=user_json,
        verbose=True
    )

    return response


def convert_single_user(user_data, access_level, subject_line, message, cc=False, verbose=False):
    """
    Converts a single user's data into a Smartsheet API-compatible dictionary for user sharing.

    :param user_data:           dict or list, required  dict or list of dicts of user Smartsheet info
    :param access_level:        str, required           access level to assign (e.g., 'EDITOR', 'ADMIN')
    :param subject_line:        str, required           subject line of email notification
    :param message:             str, required           body of email notification
    :param cc:                  bool. optional          if True, cc email to owner of API key
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    dict                    dict containing user data
    """

    return {
        'type': user_data['type'],
        'userId': user_data['userId'],
        'accessLevel': access_level,
        'email': user_data['email'],
        'message': message,
        'ccMe': cc,
        'scope': user_data.get('scope', 'WORKSPACE'),
        'subject': subject_line
    }


def convert_user_dict_for_sharing(user_data, access_level, subject_line, message, cc=False, verbose=False):
    """
    Convert a user or list of users dictionary into format required for sharing a workspace.

    :param user_data:           dict or list, required  dict or list of dicts of user Smartsheet info
    :param access_level:        str, required           access level to assign (e.g., 'EDITOR', 'ADMIN')
    :param subject_line:        str, required           subject line of email notification
    :param message:             str, required           body of email notification
    :param cc:                  bool. optional          if True, cc email to owner of API key
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    dict or list            dict or list containing one or more user's data
    """

    if isinstance(user_data, list):
        return [convert_single_user(
            user_data=user,
            access_level=access_level,
            subject_line=subject_line,
            message=message,
            cc=cc,
            verbose=verbose
        ) for user in user_data]
    else:
        return convert_single_user(
            user_data=user_data,
            access_level=access_level,
            subject_line=subject_line,
            message=message,
            cc=cc,
            verbose=verbose
        )


def delete_user(user_id, remove_from_shares=False, transfer_ownership=None, verbose=False):
    """
    Deletes a user from Smartsheet account.

    :param user_id:             str, required           ID of user to delete
    :param remove_from_shares:  bool, optional          if True, removes user from shared items
    :param transfer_ownership:  str, optional           email address to transfer ownership of deleted user's sheets to
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response in JSON format
    """

    url = SS_BASE_URL + SS_USER_URL + f'{user_id}'

    params = {}
    if remove_from_shares:
        params['removeFromShares'] = 'true'
    if transfer_ownership:
        params['transferTo'] = transfer_ownership

    response = rate_limiter_passthru(url=url, request='delete', return_all=True, verbose=verbose)

    print(response) if verbose else None
    return response


def get_user(user_id=None, verbose=False):
    """
    Returns user metadata from Smartsheet.

    If user_id is not None, returns as follows:

        {
            'id': 2109142850895624,
            'email': 'matthew@nicejacket.cc',
            'name': 'Matthew Runde',
            'status': 'ACTIVE',
            'admin': false,
            'licensedSheetCreator': true,
            'groupAdmin': false,
            'resourceViewLicensed': false,
            'lastLogin': '2022-12-21T15:25:30Z',
            'account': {
                'id': 2109142850895624,
                'name': 'Account Name'
            }
        }

    If user_id is None, returns as follows:

        [
            {
                'id': 2109142850895624,
                ...
            },
            ...
        ]

    :param user_id:             str, optional           if None, return all users; else, ID of user to return
    :param verbose:
    :return:
    """

    if user_id is None:
        url = SS_BASE_URL + SS_USER_URL
    else:
        url = SS_BASE_URL + SS_USER_URL + f'{user_id}'
    response = rate_limiter_passthru(url=url, request='get', verbose=verbose)

    print(response) if verbose else None
    return response


def get_user_id_by_user_name(user_name, verbose=False):
    """
    Given a list of dictionaries containing user data, returns user name.

    Returns as follows:

        {
            'id': 2109142850895624,
            'email': 'matthew@nicejacket.cc',
            'name': 'Matthew Runde',
            'status': 'ACTIVE',
            'admin': false,
            'licensedSheetCreator': true,
            'groupAdmin': false,
            'resourceViewLicensed': false,
            'lastLogin': '2022-12-21T15:25:30Z',
            'account': {
                'id': 2109142850895624,
                'name': 'Account Name'
            }
        }

    :param user_name:           str, required           user or group share name to return ID from
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    str or None             user or group share name
    """

    user_data = get_user(user_id=None, verbose=verbose)                        # return all user metadata

    user_id = next((user.get('id') for user in user_data if user.get('name') == user_name), None)
    print(user_id) if verbose else None

    return user_id


def get_user_name_by_user_id(user_id, verbose=False):
    """
    Given a list of dictionaries containing user data, returns user name.

    Returns as follows:

        {
            'id': 2109142850895624,
            'email': 'matthew@nicejacket.cc',
            'name': 'Matthew Runde',
            'status': 'ACTIVE',
            'admin': false,
            'licensedSheetCreator': true,
            'groupAdmin': false,
            'resourceViewLicensed': false,
            'lastLogin': '2022-12-21T15:25:30Z',
            'account': {
                'id': 2109142850895624,
                'name': 'Account Name'
            }
        }

    :param user_id:             str, required           user or group share ID to return name from
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    str or None             user or group share name
    """

    user_data = get_user(user_id=None, verbose=verbose)                        # return all user metadata

    user_name = next((user.get('name') for user in user_data if user.get('id') == user_id), None)
    print(user_name) if verbose else None

    return user_name


def update_user(user_id, admin=False, licensed_sheet_creator=False, first_name=None, last_name=None,
                group_admin=False, resource_viewer=False, verbose=False):
    """
    Updates user details.

    :param user_id:                 int, required       ID of user to update
    :param admin:                   bool, optional      indicates if user is system admin
    :param licensed_sheet_creator:  bool, optional      indicates if user is licensed sheet creator
    :param first_name:              str, optional       user first name
    :param last_name:               str, optional       user last name
    :param group_admin:             bool, optional      indicates if user is group admin
    :param resource_viewer:         bool, optional      indicates if user is resource viewer
    :param verbose:                 bool, optional      if True, print status to terminal
    :return:                        JSON                API response in JSON format
    """

    url = SS_BASE_URL + SS_USER_URL + f'{user_id}'

    payload = {
        'admin': admin,
        'licensedSheetCreator': licensed_sheet_creator,
        'firstName': first_name,
        'lastName': last_name,
        'groupAdmin': group_admin,
        'resourceViewer': resource_viewer
    }
    payload = {key: value for key, value in payload.items() if value is not None}

    response = rate_limiter_passthru(url=url, request='put', post_data=payload, return_all=True, verbose=verbose)

    print(response) if verbose else None
    return response
