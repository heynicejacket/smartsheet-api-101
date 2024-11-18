from smartsheet.core.constants import (
    SS_BASE_URL,
    SS_FOLDER_URL
)

from smartsheet.core.sql import (
    rate_limiter_passthru
)

from smartsheet.core.toolkit import (
    get_slim_metadata
)


def get_home_contents(slim_metadata=False, base_keys=None, additional_keys=None, verbose=False):
    """
    Returns JSON dictionary containing metadata of all items in user's home folder.

    Returns as follows:

        [
            {
                'id': 2109142850895624,
                'name': 'Sheets',
                'permalink': 'https://app.smartsheet.com/folders/personal',
                'sheets': [
                    {
                        'id': 2109142850895624,
                        'name': 'Test Sheet',
                        'accessLevel': 'OWNER',
                        'permalink': 'https://app.smartsheet.com/folders/khXfXF5SEjmdFT2mh1P17HW',
                        'createdAt': '2019-06-13T20:44:29Z',
                        'modifiedAt': '2019-06-14T19:30:22Z'
                    },
                    ...
                ]
            }
        ]

    If slim_metadata:

        [
            {
                'id': 2109142850895624,
                'name': 'Test Sheet',
                'permalink': 'https://app.smartsheet.com/folders/khXfXF5SEjmdFT2mh1P17HW',
            },
            ...
        ]

    :param slim_metadata        bool, optional          if True, returns a limited JSON dict
    :param base_keys:           list, optional          if not None, list of alternate base_keys to retrieve
    :param additional_keys      list, optional          additional keys to preserve in metadata
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response in JSON format
    """

    url = SS_BASE_URL + SS_FOLDER_URL + 'personal'
    print(url) if verbose else None

    response = rate_limiter_passthru(url=url, request='get', verbose=verbose)

    if slim_metadata:
        response = get_slim_metadata(
            data=response[0]['sheets'],
            base_keys=base_keys,
            additional_keys=additional_keys,
            verbose=verbose
        )

    return response


def get_home_folders(slim_metadata=False, base_keys=None, additional_keys=None, verbose=False):
    """
    Returns JSON dictionary containing metadata of all folders in user's home folder.

    Returns as follows:

        [
            {
                'pageNumber': 1,
                'pageSize': 100,
                'totalPages': 1,
                'totalCount': 4,
                'data': [
                    {
                        'id': 2109142850895624,
                        'name': 'Home Folder Name',
                        'permalink': 'https://app.smartsheet.com/folders/khXfXF5SEjmdFT2mh1P17HW',
                    },
                    ...
                ]
            }
        ]

    slim_metadata returns:

        [
            {
                'id': 2109142850895624,
                'name': 'Home Folder Name',
                'permalink': 'https://app.smartsheet.com/folders/khXfXF5SEjmdFT2mh1P17HW',
            },
            ...
        ]

    :param slim_metadata        bool, optional          if True, returns a limited JSON dict
    :param base_keys:           list, optional          if not None, list of alternate base_keys to retrieve
    :param additional_keys      list, optional          additional keys to preserve in metadata
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response in JSON format
    """

    url = SS_BASE_URL + 'home/' + SS_FOLDER_URL
    print(url) if verbose else None

    response = rate_limiter_passthru(url=url, request='get', verbose=verbose)

    if slim_metadata:
        response = get_slim_metadata(
            data=response[0]['data'],
            base_keys=base_keys,
            additional_keys=additional_keys,
            verbose=verbose
        )

    return response
