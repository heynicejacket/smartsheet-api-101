from smartsheet.core.api import (
    rate_limiter_passthru
)

from smartsheet.core.constants import (
    SS_BASE_URL,
    SS_SEARCH_URL
)


def search_sheet(sheet_id, search_value, verbose=False):
    """
    Search for a specific value in a Smartsheet sheet.

    Successful search returns as follows:

        {
            'totalCount': 1,
            'results': [
                {
                    'objectType': 'ROW',
                    'objectId': 2109142850895624,
                    'parentObjectId': 2109142850895624,
                    'text': '2415-B',
                    'context': 'Project ID: 2415-B'
                },
                {
                    ...
                }
            ]
        }

    :param sheet_id:            str, required           sheet ID to search
    :param search_value:        str, required           value to search for, enclosed in double quotes for exact match
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response with search results
    """

    url = SS_BASE_URL + SS_SEARCH_URL + f'?query={search_value}&scope=sheetId:{sheet_id}'

    print(f'Searching for \'{search_value}\' in sheet ID {sheet_id}...') if verbose else None
    response = rate_limiter_passthru(url=url, request='get', verbose=verbose)

    print(response) if verbose else None
    return response


def search_all_sheets(search_value, scopes=None, verbose=False):
    """
    Searches for a specified query text across all sheets that owner of Smartsheet API token can access.

    Options for 'scopes' parameter expand search beyond sheets, and should be formatted as a string (e.g.
    'attachments,cellData') and are as follows:

        attachments, cellData, comments, folderNames, reportNames, sheetNames,
        sightNames, summaryFields, templateNames, workspaceNames

    :param search_value:        str, required           value to search for, enclosed in double quotes for exact match
    :param scopes:              list, optional          list of search filters
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response with search results
    """

    url = SS_BASE_URL + SS_SEARCH_URL

    params = {
        'query': search_value,
        'scopes': scopes
    }

    print(f'Searching for \'{search_value}\' in all sheets...') if verbose else None
    response = rate_limiter_passthru(url=url, request='get', post_data=params, verbose=verbose)

    print(response) if verbose else None
    return response
