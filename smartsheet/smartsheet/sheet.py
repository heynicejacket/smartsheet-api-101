from datetime import datetime
import pandas as pd
from pandas.api.types import is_datetime64_any_dtype

from smartsheet.core.constants import (
    SS_BASE_URL,
    SS_COLUMN_URL,
    SS_EMAIL_URL,
    SS_FOLDER_URL,
    SS_RETURN_ALL_URL,
    SS_ROW_URL,
    SS_SHEET_URL,
    SS_USER_URL,
    SS_WORKSPACE_URL
)

from smartsheet.core.sql import (
    format_column_headers,
    rate_limiter_passthru,
    ss_post
)

from smartsheet.core.toolkit import (
    get_slim_metadata
)

from smartsheet.smartsheet.column import (
    get_valid_columns,
    primary_column_exists
)

from smartsheet.smartsheet.row import (
    get_valid_rows
)


def append_sheet_from_df(df, sheet_id, auto_cols=None, replace_nan=False, to_top=True, parent_id=None, verbose=False):
    """
    Appends rows from a DataFrame to an existing Smartsheet sheet, with optional parameters to manage placement,
    structure, and data formatting.

    Returns as follows:

        {
            'message': 'SUCCESS',
            'resultCode': 0,
            'version': 2, 'result': [
                {
                    'id': 2109142850895624,
                    'sheetId': 2109142850895624,
                    'rowNumber': 1,
                    'expanded': True,
                    'locked': False,
                    'lockedForUser': False,
                    'createdAt': '2019-08-09T21:19:56Z',
                    'modifiedAt': '2022-11-13T22:14:00Z'
                    'cells': [
                        {
                            'columnId': 2109142850895624,
                            'displayValue': 'foo',
                            'value': 'foo'
                        },
                        ...
                    ]
                }
            ]
        }

    :param df:                  df, required            DataFrame to append to Smartsheet
    :param sheet_id:            str, required           target sheet ID
    :param auto_cols:           list, optional          column list to drop from DataFrame
    :param replace_nan:         bool, optional          if True, replace NaN values with empty strings
    :param to_top:              bool, optional          if True, add rows to top of sheet; else, bottom
    :param parent_id:           str, optional           if provided, sets parentId for hierarchical rows in Smartsheet
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response confirming row append
    """

    get_cols_url = SS_BASE_URL + SS_SHEET_URL + f'{sheet_id}/' + SS_COLUMN_URL + '?level=2'
    post_rows_url = SS_BASE_URL + SS_SHEET_URL + f'{sheet_id}/' + SS_ROW_URL

    if auto_cols:
        df = df.drop(columns=auto_cols, errors='ignore')

    df.reset_index(drop=True, inplace=True)

    ss_column_json = rate_limiter_passthru(url=get_cols_url, request='get', verbose=verbose)[0]['data']

    valid_columns = get_valid_columns(column_json=ss_column_json)

    if len(df.columns) > len(valid_columns):
        raise ValueError(f'Columns in DataFrame ({len(df.columns)}) exceed columns in Smartsheet ({len(valid_columns)}).')

    df.loc[:, df.dtypes.apply(pd.api.types.is_datetime64_ns_dtype)] = df.loc[:, df.dtypes.apply(pd.api.types.is_datetime64_ns_dtype)].apply(
        lambda x: x.dt.strftime('%Y-%m-%d')
    )

    list_of_rows = get_valid_rows(
        df=df, replace_nan=replace_nan, valid_columns=valid_columns,
        to_top=to_top, parent_id=parent_id, verbose=verbose
    )

    response = rate_limiter_passthru(
        url=post_rows_url, request='post', post_data=list_of_rows,
        return_all=True, verbose=verbose
    )

    return response


def clear_sheet(sheet_id, max_url_len=4000, verbose=False):
    """
    Clears a Smartsheet sheet of its rows while preserving sheet's column structure.

    :param sheet_id:            str, required           ID of sheet to clear
    :param max_url_len:         int, optional           maximum char length of request URL per loop
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response in JSON format
    """

    del_sheet = get_sheet(sheet_id=sheet_id, verbose=verbose)
    del_row_ids = [str(row['id']) for row in del_sheet[0]['rows']]

    while del_row_ids:
        url = SS_BASE_URL + SS_SHEET_URL + f'{sheet_id}/rows?ids='

        while del_row_ids and len(url) + len(del_row_ids[-1]) + 1 < max_url_len:
            url += del_row_ids.pop() + ','

        url = url.rstrip(',') + '&ignoreRowsNotFound=true'
        return rate_limiter_passthru(url=url, request='delete', verbose=verbose)


def convert_value(value, column_type):
    """
    Converts a value based on Smartsheet column type.

    Returns converted value. For 'DATETIME', value is returned as datetime object. For 'TEXT_NUMBER', value is returned
    as int, float, or original value if conversion fails. For other types, value is returned as-is or appropriately
    converted (e.g., 'CHECKBOX' to boolean).

    # todo: merge with smartsheet.smartsheet.cell.format_cell() and move to .cell

    :param value:               any, required           value to be converted; string, numeric type, or None
    :param column_type:         str, required           column type from metadata (e.g., 'DATETIME', 'TEXT_NUMBER')
    :return:                                            converted value
    """

    if column_type == 'DATETIME' and isinstance(value, str):
        return datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')

    elif column_type == 'TEXT_NUMBER' and value is not None:
        if isinstance(value, (int, float)):
            return value                                                    # return number if already numeric type
        try:
            return float(value) if '.' in str(value) else int(value)
        except ValueError:
            return value                                                    # return original if cannot be converted

    elif column_type == 'CHECKBOX':
        return bool(value)

    elif column_type == 'PICKLIST':
        return value

    elif column_type == 'MULTI_PICKLIST':
        return value if isinstance(value, list) else [value]                # ensure a list

    elif column_type == 'DURATION':
        return value

    elif column_type == 'CONTACT_LIST':
        return value

    elif column_type == 'AUTO_NUMBER':
        return value

    elif column_type == 'PREDECESSOR':
        return value

    return value


def create_sheet_from_df(df, sheet_name, primary_col=None, replace_nan=False, verbose=False):
    """

    Returns:

        {
            'id': 2109142850895624,
            'name': 'New Sheet',
            'permalink': 'https://app.smartsheet.com/sheets/khXfXF5SEjmdFT2mh1'
        }

    :param df:                  df, required            DataFrame to create sheet
    :param sheet_name:          str, required           sheet name to be created
    :param primary_col:         str, optional           if not None, column to make primary; else 0th column
    :param replace_nan:         bool, optional          if True, replaces NaN / NaT with empty string
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    dict                    dict containing sheet ID, name, and permalink
    """

    url = SS_BASE_URL + SS_SHEET_URL
    print(url) if verbose else False

    primary_col = primary_col or df.columns[0]                      # if no primary column declared, assume 0th column
    columns = [df_to_smartsheet_col_type_dict(df, col, col == primary_col) for col in df.columns]
    payload = {
        'name': sheet_name,
        'columns': columns
    }

    response = rate_limiter_passthru(url=url, request='post', post_data=payload, return_all=True, verbose=verbose)

    result_dict = {key: response['result'][key] for key in ['id', 'name', 'permalink']}
    append_sheet_from_df(df=df, sheet_id=result_dict['id'], replace_nan=replace_nan, verbose=verbose)

    return result_dict


def df_to_smartsheet(df, sheet_id=None, sheet_name='', import_type='create', auto_cols=None, primary_col=None,
                     replace_nan=False, verbose=False):
    """
    Takes a DataFrame and appends to or replaces an existing Smartsheet, or creates a new sheet if import_type='Create'
    or if sheet ID is invalid.

    :param df:                  df, required            DataFrame to append to or replace data in an existing Smartsheet
    :param sheet_id:            int, optional           sheet ID to append or replace with DataFrame
    :param sheet_name:          str, optional           sheet name if creating new ID; defaults to new_sheet_[datetime] if ''
    :param import_type:         str, optional           default is 'create', other options are 'append', 'replace'
    :param auto_cols:           list, optional          all DataFrame columns that are "autogenerated" on Smartsheet
    :param primary_col:         str, optional           if not None, column to make primary; else 0th column
    :param replace_nan:         bool, optional          if True, replaces NaN / NaT with empty string
    :param verbose:             bool, optional          if True, prints statuses to terminal
    :return:                    None
    """

    if import_type not in ('append', 'create', 'replace'):
        raise ValueError(f'{import_type} is not a valid import_type')

    if sheet_id and import_type == 'append':
        print(f'Appending to sheet {sheet_id}...')
        response = append_sheet_from_df(df, sheet_id, auto_cols, replace_nan, verbose)
    elif sheet_id and import_type == 'replace':
        print(f'Replacing data in sheet {sheet_id}...')
        response = replace_sheet_from_df(df, sheet_id, auto_cols, replace_nan, verbose)
    else:
        print(f'Creating sheet {sheet_name}')
        response = create_sheet_from_df(df=df, sheet_name=sheet_name, primary_col=primary_col, replace_nan=replace_nan, verbose=verbose)

    return response


def df_to_smartsheet_col_type_dict(df, col, is_primary):
    """
    Given a DataFrame and a column name, returns a dict containing column name, Smartsheet data type retrieved using
    data type of DataFrame column, and whether column is primary.

    Returns as follows:

        {'title': 'Project Name', 'type': 'TEXT_NUMBER', 'primary': True}

    Used in a loop, can be used to product a list of dictionaries for an entire DataFrame, as follows:

        [
            {'title': 'Project Name', 'type': 'TEXT_NUMBER', 'primary': True},
            {'title': 'Project Start Date', 'type': 'DATE'},
            {'title': 'Project Status', 'type': 'PICKLIST', 'options': ['Not Started', 'In Progress', 'Complete']}
        ]

    :param df:                  df, required            DataFrame containing data to be used with Smartsheet
    :param col:                 str, required           column name to assess
    :param is_primary:          bool, required          if True, column is primary; else False
    :return:                    dict                    dict containing col name, Smartsheet data type, and primary status
    """

    col_type = 'CHECKBOX' if df[col].dtypes == bool else 'DATE' if is_datetime64_any_dtype(df[col]) else 'TEXT_NUMBER'
    if col_type == 'DATE':
        df[col] = df[col].dt.strftime('%Y-%m-%d')
    return {'title': col, 'type': col_type, 'primary': is_primary}


def get_all_sheets(slim_metadata=False, additional_keys=None, verbose=False):
    """
    Returns a JSON dictionary containing details of all sheets user can access.

    Returns as follows:

        [
            {
                'id': 2109142850895624,
                'name': 'Project Summary',
                'accessLevel': 'ADMIN',
                'permalink': 'https://app.smartsheet.com/sheets/khXfXF5SEjmdFT2mh1',
                'createdAt': '2019-08-09T21:19:56Z',
                'modifiedAt': '2022-11-13T22:14:00Z'
            },
            ...
        ]

    If slim_metadata is True, by default as follows:

        [
            {
                'id': 2109142850895624,
                'name': 'Project Summary'
            },
            ...
        ]

    :param slim_metadata        bool, optional          if True, returns a limited JSON dict
    :param additional_keys      list, optional          additional keys to preserve in metadata
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response in JSON format
    """

    url = SS_BASE_URL + SS_SHEET_URL + SS_RETURN_ALL_URL
    print(url) if verbose else None

    response = rate_limiter_passthru(url=url, request='get', verbose=verbose)[0]['data']

    if slim_metadata:
        response = get_slim_metadata(
            data=response,
            base_keys=None,
            additional_keys=additional_keys,
            verbose=verbose
        )

    return response


def get_sheet(sheet_id, slim_metadata=False, additional_keys=None, verbose=False):
    """
    Returns JSON of top-level sheet detail. By default, sheet ID, name, user access level, URL, and created and
    modified dates.

    Returns as follows:

        [
            {
                'id': 2109142850895624,
                'name': 'Project Summary',
                'accessLevel': 'ADMIN',
                'permalink': 'https://app.smartsheet.com/sheets/khXfXF5SEjmdFT2mh1',
                'createdAt': '2019-08-09T21:19:56Z',
                'modifiedAt': '2022-11-13T22:14:00Z'
                'columns': [
                    {
                        'id': 2109142850895624,
                        'index': 0,
                        'title': 'Project Name',
                        'type': 'TEXT_NUMBER'
                    },
                    ...
                ],
                'rows': [
                    {
                        'id': 2109142850895624,
                        'rowNumber': 1,
                        'cells': [
                            {'columnId': 2109142850895624, 'value': 'Project A'},
                            ...
                        ]
                    },
                    ...
                ]
            }
        ]

    If slim_metadata is True, by default, returns as follows, but can return additional key-value pairs contained in
    optional list additional_keys:

        [
            {
                'id': 2109142850895624,
                'name': 'Project Summary'
            }
        ]

    :param sheet_id:            str, required           ID of sheet to retrieve
    :param slim_metadata        bool, optional          if True, returns a limited JSON dict
    :param additional_keys      list, optional          additional keys to preserve in metadata
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response in JSON format
    """

    url = SS_BASE_URL + SS_SHEET_URL + f'{sheet_id}' + SS_RETURN_ALL_URL
    print(url) if verbose else None

    sheet_json = rate_limiter_passthru(url=url, request='get', verbose=verbose)

    if slim_metadata:
        sheet_json = get_slim_metadata(
            data=sheet_json,
            base_keys=None,
            additional_keys=additional_keys,
            verbose=verbose
        )

    return sheet_json


def get_sheet_id(sheet_name, verbose=False):
    """
    Given a sheet name, returns sheet ID.

    :param sheet_name:          str, required           sheet name to return sheet ID from
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    str                     sheet ID
    """

    sheet_list = get_all_sheets(slim_metadata=False, verbose=verbose)
    for sheet in sheet_list:
        if sheet.get('name') == sheet_name:
            sheet_id = sheet.get('id')
            print(sheet_id) if verbose else None

            return sheet_id

    return None


def get_sheet_name(sheet_id, verbose=False):
    """
    Given a sheet ID, returns sheet name.

    :param sheet_id:            str, required           sheet ID to return sheet name from
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    str                     sheet name
    """

    sheet_name = get_sheet(sheet_id)[0]['name']
    print(sheet_name) if verbose else None

    return sheet_name


def get_sheet_url(sheet_id, verbose=False):
    """
    Given a sheet ID, returns sheet URL, as follows:

        'https://app.smartsheet.com/sheets/khXfXF5SEjmdFT2mh1'

    :param sheet_id:            str, required           sheet ID to return sheet URL from
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    str                     sheet URL
    """

    sheet_url = get_sheet(sheet_id)[0]['permalink']
    print(sheet_url) if verbose else None

    return sheet_url


def get_sheet_version(sheet_id, verbose=False):
    """
    Given a sheet ID, returns sheet version, as follows:

        {'version': 1}

    :param sheet_id:            str, required           sheet ID to return sheet version from
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    dict                    dict containing version number
    """

    url = SS_BASE_URL + SS_SHEET_URL + f'{sheet_id}/version'
    print(url) if verbose else None

    response = rate_limiter_passthru(url=url, request='get', verbose=verbose)

    return response[0] if response else None


def replace_sheet_from_df(df, sheet_id, auto_cols=None, replace_nan=False, verbose=False):
    """
    Given a sheet ID and DataFrame, replaces data in sheet with data from DataFrame.

    Contains an optional parameter to drop columns from DataFrame if those columns were auto-generated fields in a
    Smartsheet sheet. This can be helpful if DataFrame itself was derived from a sheet (e.g. smartsheet_to_df())
    and that sheet contained autogenerated columns.

    Returns as follows:

        {
            'message': 'SUCCESS',
            'resultCode': 0,
            'version': 6,
            'result': [
                {
                    'id': 2109142850895624,
                    'sheetId': 2109142850895624,
                    'rowNumber': 1,
                    'expanded': True,
                    'locked': False,
                    'lockedForUser': False,
                    'createdAt': '2019-08-09T21:19:56Z',
                    'modifiedAt': '2022-11-13T22:14:00Z'
                    'cells': [
                        {
                            'columnId': 2109142850895624,
                            'displayValue': 'New row',
                            'value': 'New row'
                        },
                        ...
                    ]
                }
            ]
        }

    :param df:                  df, required            DataFrame to replace data in Smartsheet
    :param sheet_id:            str, required           ID of sheet to replace data in
    :param auto_cols:           list, optional          list of sheet's auto-generated columns to drop
    :param replace_nan:         bool, optional          if True, replace NaN values with empty strings
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response in JSON format
    """

    url = SS_BASE_URL + SS_SHEET_URL + f'{sheet_id}/' + SS_COLUMN_URL

    if auto_cols:
        df = df.drop(columns=auto_cols, errors='ignore')

    df.reset_index(drop=True, inplace=True)

    ss_columns = rate_limiter_passthru(url=url, request='get', verbose=verbose)[0]['data']
    print(ss_columns) if verbose else None

    valid_columns = [col['id'] for col in ss_columns if 'formula' not in col and 'systemColumnType' not in col]

    if len(df.columns) > len(valid_columns):
        raise ValueError(
            f'Columns in DataFrame ({len(df.columns)}) exceed columns in Smartsheet ({len(valid_columns)}).')

    clear_sheet(sheet_id)
    return append_sheet_from_df(df=df, sheet_id=sheet_id, replace_nan=replace_nan, verbose=verbose)


def smartsheet_to_df(sheet_id, convert_headers=True, verbose=False):
    """
    Constructs a pandas DataFrame from a Smartsheet-like dictionary, converting types based on column metadata.

    If convert_headers is True, standardize column names into a form generally easier to work with, converting to
    lowercase and replacing all spaces in column headers with underscores.

    :param sheet_id:            str, required           sheet ID to produce DataFrame from
    :param convert_headers:     bool, optional          if True, convert column names
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    df                      DataFrame produced from Smartsheet sheet
    """

    sheet_json = get_sheet(sheet_id=sheet_id, slim_metadata=False, verbose=verbose)

    column_map = {col['id']: col['title'] for col in sheet_json[0]['columns']}
    column_types = {col['title']: col['type'] for col in sheet_json[0]['columns']}

    data = []
    for row in sheet_json[0]['rows']:
        row_data = {
            column_map[cell['columnId']]: convert_value(cell.get('value'), column_types[column_map[cell['columnId']]])
            for cell in row['cells']
        }
        data.append(row_data)

    df = pd.DataFrame(data)

    if convert_headers:
        df = format_column_headers(df)

    return df


def create_sheet_in_folder(folder_id, sheet_name, include=None, columns=None, verbose=False):
    """
    Creates a new sheet in a specified Smartsheet folder.

    The parameter 'columns' should be formatted as a list of dictionaries, as follows:

        test_columns = [
            {'title': 'Project Name', 'type': 'TEXT_NUMBER', 'primary': True},
            {'title': 'Project Start Date', 'type': 'DATE'},
            {'title': 'Project Status', 'type': 'PICKLIST', 'options': ['Not Started', 'In Progress', 'Complete']}
        ]

    This structure can be generated from a DataFrame using df_to_smartsheet_col_type_dict(). Primary column must be
    identified and be of type TEXT_NUMBER.

    Options for 'include' parameter should be formatted as a string (e.g. 'attachments,data') and are as follows:

        attachments, cellLinks, data, discussions, filters, forms, ruleRecipients, rules

    Returns as follows:

        {
            'message': 'SUCCESS',
            'resultCode': 0,
            'result': {
                'id': 2109142850895624,
                'name': 'test',
                'accessLevel': 'OWNER',
                'permalink': 'https://app.smartsheet.com/sheets/khXfXF5SEjmdFT2mh1',
                'columns': [
                    {
                        'id': 2109142850895624,
                        'version': 0,
                        'index': 0,
                        'title': 'Project Name',
                        'type': 'TEXT_NUMBER',
                        'primary': True,
                        'validation': False,
                        'width': 150
                    },
                    ...
                ]
            }
        }

    :param folder_id:           str, required           folder ID where sheet will be created
    :param sheet_name:          str, required           name of new sheet
    :param include:             str, required           comma-separated list to copy from template (e.g. 'attachments,data')
    :param columns:             list, required          list of dicts of columns in sheet; must include 'title' and 'type'
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response with details of created sheet
    """

    if not primary_column_exists(columns=columns, verbose=verbose):
        return {'error': 'InvalidColumnConfiguration', 'message': 'There must be exactly one primary TEXT_NUMBER column.'}

    url = SS_BASE_URL + SS_FOLDER_URL + f'{folder_id}/' + SS_SHEET_URL
    print(url) if verbose else None

    params = {}
    if include:
        params['include'] = include

    data = {
        'name': sheet_name,
        'columns': columns
    }

    print(f'Creating sheet \'{sheet_name}\' in folder {folder_id} with columns: {columns}...') if verbose else None

    return ss_post(url, payload=data, return_all=True, verbose=verbose)         # todo: standardise


def create_sheet_in_workspace(workspace_id, sheet_name, include=None, columns=None, access_api_level=0, verbose=False):
    """
    Creates a new sheet in a specified Smartsheet workspace.

    The parameter 'columns' should be formatted as a list of dictionaries, as follows:

        test_columns = [
            {'title': 'Project Name', 'type': 'TEXT_NUMBER', 'primary': True},
            {'title': 'Project Start Date', 'type': 'DATE'},
            {'title': 'Project Status', 'type': 'PICKLIST', 'options': ['Not Started', 'In Progress', 'Complete']}
        ]

    This structure can be generated from a DataFrame using df_to_smartsheet_col_type_dict(). Primary column must be
    identified and be of type TEXT_NUMBER.

    Options for 'include' parameter should be formatted as a string (e.g. 'attachments,data') and are as follows:

        attachments, cellLinks, data, discussions, filters, forms, ruleRecipients, rules

    Returns as follows:

        {
            'message': 'SUCCESS',
            'resultCode': 0,
            'result': {
                'id': 2109142850895624,
                'name': 'test',
                'accessLevel': 'OWNER',
                'permalink': 'https://app.smartsheet.com/sheets/khXfXF5SEjmdFT2mh1',
                'columns': [
                    {
                        'id': 2109142850895624,
                        'version': 0,
                        'index': 0,
                        'title': 'Project Name',
                        'type': 'TEXT_NUMBER',
                        'primary': True,
                        'validation': False,
                        'width': 150
                    },
                    ...
                ]
            }
        }

    Access level: 0 is VIEWER and 1 is COMMENTER

    :param workspace_id:        str, required           workspace ID where sheet will be created
    :param sheet_name:          str, required           name of sheet to create in workspace
    :param include:             str, optional           comma-separated list of elements to copy from template
    :param columns:             list, optional          list of dicts containing (at least) 'title' and 'type' keys
    :param access_api_level:    int, optional           API access level
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response with details of created sheet
    """

    if not primary_column_exists(columns=columns, verbose=verbose):
        return {'error': 'InvalidColumnConfiguration', 'message': 'There must be exactly one primary TEXT_NUMBER column.'}

    url = SS_BASE_URL + SS_WORKSPACE_URL + f'{workspace_id}/' + SS_SHEET_URL

    params = {}
    if include:
        params['include'] = include
    params['accessApiLevel'] = access_api_level

    data = {
        'name': sheet_name,
        'columns': columns
    }

    print(f'Creating sheet \'{sheet_name}\' in workspace {workspace_id} with columns: {columns}...') if verbose else None

    return rate_limiter_passthru(url=url, request='post', post_data=data, return_all=True, verbose=verbose, params=params)


def list_org_sheets(return_all=False, verbose=False):
    """
    List all sheets in account. Only available to system admins.

    By default, returns as follows:

        {
            'pageNumber': 1,
            'pageSize': 50,
            'totalPages': -1,
            'totalCount': -1,
            'data': [
                {
                    'id': 0,
                    'name': 'string',
                    'owner': '',
                    'ownerId': 0
                },
                ...
            ]
        }

    If return_all is True, returns list of dictionaries containing only sheet information, as follows:

        [
            {
                'id': 0,
                'name': 'string',
                'owner': '',
                'ownerId': 0
            },
            ...
        ]

    :param return_all:          bool, optional          if True, only return data dict; else, entire json dict
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response in JSON format
    """

    url = SS_BASE_URL + SS_USER_URL + SS_SHEET_URL
    print(url) if verbose else None

    response = rate_limiter_passthru(url=url, request='get', return_all=return_all, verbose=verbose)

    return response


def move_sheet(sheet_id, destination_id, destination_type, verbose=False):
    """
    Moves specified sheet to a new location in Smartsheet. New location can be a Smartsheet folder, workspace, or
    Smartsheet home location.

    Returns as follows:

        {
            'message': 'SUCCESS',
            'resultCode': 0,
            'result': {
                'id': 2109142850895624,
                'name': 'Moved Project Sheet',
                'accessLevel': 'OWNER',
                'permalink': 'https://app.smartsheet.com/sheets/khXfXF5SEjmdFT2mh1',
            }
        }

    :param sheet_id:            str, required           ID of sheet to move
    :param destination_id:      str, required           destination ID folder or workspace
    :param destination_type:    str. required           destination type ('folder', 'home', or 'workspace')
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response with details of moved sheet, or error
    """

    url = SS_BASE_URL + SS_SHEET_URL + f'{sheet_id}/move'
    print(f'Request URL: {url}') if verbose else None

    data = {
        'destinationId': destination_id if destination_type != 'home' else None,
        'destinationType': destination_type
    }

    print(f'Moving sheet {sheet_id} to {destination_type} with ID {destination_id}...') if verbose else None

    response = rate_limiter_passthru(url=url, request='post', post_data=data, return_all=True, verbose=verbose)
    print(response) if verbose else None

    return response


def send_sheet_via_email(sheet_id, send_to, subject, message, format_type='PDF', format_details='LETTER', cc_me=False, verbose=False):
    """
    Sends specified sheet as a PDF (or other specified format) attachment via email.

    The parameter 'send_to' should be formatted as follows:

        [{'email': 'recipient@example.com'}, {'email': 'another@example.com'}]

    Options for format_type and format_details are as follows:

        format_type:        'EXCEL', 'PDF', or 'PDF_GANTT'
        format_details:     'A0', 'A1', 'A2', 'A3', 'A4', 'ARCHID', 'LEGAL', 'LETTER', or 'WIDE'

    Returns as follows:

        {'message': 'SUCCESS', 'resultCode': 0}

    :param sheet_id:            str, required           ID of sheet to send
    :param send_to:             list, required          list of dicts containing emails to send sheet to
    :param subject:             str, required           subject line of email
    :param message:             str, required           body content of email
    :param format_type:         str, optional           format of export
    :param format_details:      str, optional           if PDF, paper size to save as
    :param cc_me:               bool, optional          if True, sends a copy of email to sender
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response with details of email sent, or error message
    """

    url = SS_BASE_URL + SS_SHEET_URL + f'{sheet_id}/' + SS_EMAIL_URL
    print(url) if verbose else None

    send_to_dict = [{'email': email} if isinstance(email, str) else email for email in send_to]
    format_details_dict = {'paperSize': format_details} if format_type in ['PDF', 'PDF_GANTT'] else {}
    data = {
        'sendTo': send_to_dict,
        'subject': subject,
        'message': message,
        'format': format_type,
        'ccMe': cc_me,
        'formatDetails': format_details_dict
    }

    response = rate_limiter_passthru(url=url, request='post', post_data=data, return_all=True, verbose=verbose)
    print(response) if verbose else None

    return response


def copy_sheet(sheet_id, new_name, destination_type, destination_id=None, include=None, exclude=None, verbose=False):
    """
    Copies an existing sheet to a specified destination - folder, workspace, or home - in Smartsheet. If sheet is copied
    to a folder or workspace, destination_id must be provided. If sheet is copied to home, destination_id must be None.
    Copied sheet can have same name as original sheet.

    Options for 'include' parameter should be formatted as a string (e.g. 'attachments,data') and are as follows:

        attachments, cellLinks, data, discussions, filters, forms, ruleRecipients, rules

    Option for 'exclude' parameter is None or 'sheetHyperlinks', to exclude hyperlinks from copied sheet.

    Returns as follows:

        {
            'message': 'SUCCESS',
            'resultCode': 0,
            'result': {
                'id': 2109142850895624,
                'name': 'Copied Project Sheet',
                'accessLevel': 'OWNER',
                'permalink': 'https://app.smartsheet.com/sheets/khXfXF5SEjmdFT2mh1'
            }
        }

    :param sheet_id:            str, required           ID of sheet to copy
    :param destination_id:      str, required           destination container ID ('folder' or 'workspace')
    :param destination_type:    str, required           destination type ('folder', 'workspace', or 'home')
    :param new_name:            str, required           new name for copied sheet
    :param include:             str, optional           comma-separated list of elements to include in copy
    :param exclude:             str, optional           None or sheetHyperlinks to exclude hyperlinks from copy
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response with details of copied sheet, or error message
    """

    url = SS_BASE_URL + SS_SHEET_URL + f'{sheet_id}/copy'

    params = {}
    if include:
        params['include'] = include
    if exclude:
        params['exclude'] = exclude

    data = {
        'destinationId': destination_id,
        'destinationType': destination_type,
        'newName': new_name
    }

    print(f'Copying sheet {sheet_id} to {destination_type} {destination_id} with new name \'{new_name}\'...') if verbose else None

    response = rate_limiter_passthru(url=url, request='post', post_data=data, return_all=True, verbose=verbose, params=params)
    print(response) if verbose else None

    return response


def delete_sheet(sheet_id, verbose=False):
    """
    Deletes sheet from Smartsheet.

    Returns as follows:

        {'message': 'SUCCESS', 'resultCode': 0}

    :param sheet_id:            str, required           sheet ID to delete
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response in JSON format
    """

    url = SS_BASE_URL + SS_SHEET_URL + f'{sheet_id}'
    print(url) if verbose else None

    return rate_limiter_passthru(url=url, request='delete', return_all=True, verbose=verbose)
