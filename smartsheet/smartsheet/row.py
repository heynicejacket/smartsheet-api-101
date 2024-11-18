import pandas as pd

from smartsheet.core.api import (
    rate_limiter_passthru
)

from smartsheet.core.constants import (
    SS_BASE_URL,
    SS_EMAIL_URL,
    SS_ROW_URL,
    SS_SHEET_URL
)

from smartsheet.smartsheet.column import (
    format_cell
)

from smartsheet.smartsheet.sheet import (
    get_sheet
)


def add_row():
    # todo: receive row from JSON or DataFrame; latter accomplished with smartsheet.smartsheet.sheet.df_to_ss append
    pass


def copy_rows_to_sheet(src_sheet_id, dest_sheet_id, row_ids, include='all', verbose=False):
    """
    Copies rows from one Smartsheet sheet to another.

    Options for 'include' parameter should be formatted as a string (e.g. 'attachments,children') and are as follows:

        'all', 'attachments', 'children', 'discussions'

    :param src_sheet_id:        str, required           source sheet ID
    :param dest_sheet_id:       str, required           destination sheet ID
    :param row_ids:             list, required          list of row IDs to copy
    :param include:             str, optional           comma-separated list of elements to include in copy
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response in JSON format
    """

    url = SS_BASE_URL + SS_SHEET_URL + f'{src_sheet_id}/' + SS_ROW_URL + 'copy'

    payload = {
        'rowIds': row_ids,
        'to': {'sheetId': dest_sheet_id},
        'include': include
    }

    print(f'Copying rows: {row_ids} from sheet {src_sheet_id} to sheet {dest_sheet_id}...') if verbose else None
    response = rate_limiter_passthru(url=url, request='post', post_data=payload, return_all=True, verbose=verbose)

    print(response) if verbose else None
    return response


def delete_row(sheet_id, row_id, verbose=False):
    """
    Deletes specified row from a Smartsheet sheet.

    :param sheet_id:            str, required           sheet ID of sheet containing row
    :param row_id:              str, required           row ID to delete
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response with status of delete operation
    """

    url = SS_BASE_URL + SS_SHEET_URL + f'{sheet_id}/' + SS_ROW_URL + f'{row_id}'
    response = rate_limiter_passthru(url=url, request='delete', return_all=True, verbose=verbose)

    print(response) if verbose else None
    return response


def send_rows_via_email(sheet_id, row_ids, send_to, subject, message, include_attachments=False,
                        include_discussions=False, layout='VERTICAL', cc_me=False, verbose=False):
    """
    Sends one or more rows from a Smartsheet sheet to specified recipients via email. This function can optionally
    limit columns sent to email recipient, and can include row attachments and discussions.

    The parameter 'send_to' should be formatted as follows:

        [{'email': 'recipient@example.com'}, {'email': 'another@example.com'}]

    ----- UX Guidelines --------------------------------------------------------------------------------
    Dependent on size of sheet, columns, and values, it is likely best to select 'HORIZONTAL' for multiple rows. This
    returns as follows:

        In Smartsheet:          | Project Name | Project Start Date | Project Status |
                                | value 1a     | value 1b           | value 1c       |
                                | value 2a     | value 2b           | value 2c       |

        In email:               | Project Name | Project Start Date | Project Status |
                                | value 1a     | value 1b           | value 1c       |
                                | value 2a     | value 2b           | value 2c       |

    For one row, ideal readability - to prevent email recipient from having to scroll horizontally - is 'VERTICAL'.
    This is how default single-row email works in Smartsheet Automation, arranging columns as follows:

        In Smartsheet:          | Project Name | Project Start Date | Project Status |
                                | value 1a     | value 1b           | value 1c       |
                                | value 2a     | value 2b           | value 2c       |

        In email:               Project Name            value 1a
                                Project Start Date      value 1b
                                Project Status          value 1c

                                Project Name            value 2a
                                Project Start Date      value 2b
                                Project Status          value 2c

    Multiple rows sent with 'VERTICAL' will result in multiple "cards" of above, and can create a very long email.
    ----------------------------------------------------------------------------------------------------

    :param sheet_id:            str, required           sheet ID to retrieve rows from
    :param row_ids:             list of str, required   one or more row IDs
    :param send_to:             list of str, required   list of one or more email addresses
    :param subject:             str, required           subject line of email
    :param message:             str, required           body content of email
    :param include_attachments: bool, optional          if True, include attachment(s) in email
    :param include_discussions: bool, optional          if True, include discussion(s) in email
    :param layout:              str, optional           layout of row(s) in email
    :param cc_me:               bool, optional          if True, send copy of email to owner of API key
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response in JSON format
    """

    url = SS_BASE_URL + SS_SHEET_URL + f'{sheet_id}/' + SS_ROW_URL + SS_EMAIL_URL
    print(url) if verbose else None

    payload = {
        'rowIds': row_ids,
        'message': message,
        'subject': subject,
        'recipients': [{'email': recipient} for recipient in send_to],
        'layout': layout,
        'ccMe': cc_me,
        'includeAttachments': include_attachments,
        'includeDiscussions': include_discussions
    }

    response = rate_limiter_passthru(url=url, request='post', post_data=payload, return_all=True, verbose=verbose)

    print(response) if verbose else None
    return response


def get_row(sheet_id, row_id, verbose=False):
    """
    Retrieves a row from a Smartsheet sheet by its row ID.

    :param sheet_id:            str, required           sheet ID containing row to get
    :param row_id:              str, required           row ID to return
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response with row details
    """

    url = SS_BASE_URL + SS_SHEET_URL + f'{sheet_id}/' + SS_ROW_URL + f'{row_id}'
    response = rate_limiter_passthru(url=url, request='get', verbose=verbose)

    print(response) if verbose else None
    return response


def get_row_id_list(sheet_id, verbose=False):
    """
    Extracts a list of all row IDs from a Smartsheet-like dictionary.

        [2109142850895624, 2109142850895625, ... ]

    :param sheet_id:            str, required           sheet ID to return rows from
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    list                    list of row IDs
    """

    response = get_sheet(sheet_id=sheet_id, slim_metadata=False, verbose=verbose)
    return [row['id'] for row in response[0]['rows']]


def get_valid_rows(df, replace_nan, valid_columns, to_top, parent_id, verbose=False):
    """
    Generates a list of rows formatted for Smartsheet API by converting DataFrame rows into required structure.

    Example return format:

        [
            {
                'cells': [
                    {'columnId': '2109142850895624', 'value': 'foo'},
                    {'columnId': '2109142850895625', 'value': 'bar'}
                ],
                'toTop': True,                                          # or 'toBottom' depending on `to_top` parameter
                'parentId': '2109142850895626'                          # optional, if parentId is provided
            },
            ...
        ]

    :param df:                  df, required            DataFrame of data to convert to Smartsheet rows
    :param replace_nan:         bool, required          if True, replaces NaN with empty strings in DataFrame
    :param valid_columns:       list, required          list of valid Smartsheet column IDs and types
    :param to_top:              bool, required          if True, marks rows to be added at top of sheet; else, bottom
    :param parent_id:           str, optional           if provided, sets parentId for hierarchical rows in Smartsheet
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response in JSON format
    """

    list_of_rows = []
    for _, row in df.iterrows():
        temp_row = []
        for j, col_name in enumerate(df.columns):
            value = '' if replace_nan and pd.isnull(row[col_name]) else str(row[col_name])
            formatted_cell = format_cell(value, valid_columns[j][0], valid_columns[j][1])
            if formatted_cell:
                temp_row.append(formatted_cell)

        fmt_row = {'cells': temp_row, 'toTop': to_top} if to_top else {'cells': temp_row, 'toBottom': True}
        if parent_id:
            fmt_row['parentId'] = parent_id
        list_of_rows.append(fmt_row)

    return list_of_rows


def move_rows_to_sheet(src_sheet_id, dest_sheet_id, row_ids, verbose=False):
    """
    Move rows from one Smartsheet sheet to another.

    :param src_sheet_id:        str, required           source sheet ID
    :param row_ids:             list of str, required   list of row IDs to move
    :param dest_sheet_id:       str, required           destination sheet ID
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response in JSON format
    """

    url = SS_BASE_URL + SS_SHEET_URL + f'{src_sheet_id}/' + SS_ROW_URL + 'move'

    payload = {
        'rowIds': row_ids,
        'to': {'sheetId': dest_sheet_id}
    }

    print(f'Moving rows: {row_ids} from sheet {src_sheet_id} to sheet {dest_sheet_id}...') if verbose else None
    response = rate_limiter_passthru(url=url, request='post', post_data=payload, return_all=True, verbose=verbose)

    print(response) if verbose else None
    return response


def sort_rows(sheet_id, row_ids, verbose=False):
    """
    Sorts rows in a Smartsheet sheet based on list of row IDs.

    :param sheet_id:            str, required           sheet ID to sort
    :param row_ids:             list, required          list of row IDs in desired order
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response in JSON format
    """

    url = SS_BASE_URL + SS_SHEET_URL + f'{sheet_id}/' + SS_ROW_URL

    payload = [{'id': row_id} for row_id in row_ids]

    response = rate_limiter_passthru(url=url, request='post', post_data=payload, return_all=True, verbose=verbose)

    print(response) if verbose else None
    return response


def sort_rows_by_column(sheet_id, column_title, ascending=True, verbose=False):
    """
    Sort rows in a Smartsheet sheet based on values in a specified column.

    :param sheet_id:            str, required           sheet ID to sort
    :param column_title:        str, required           column title to sort by
    :param ascending:           bool, optional          sort order; if True, ascending; if False, descending
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response for sorting operation
    """

    sheet_data = get_sheet(sheet_id=sheet_id, verbose=verbose)
    columns = sheet_data[0]['columns']
    column_id = next((col['id'] for col in columns if col['title'] == column_title), None)

    if not column_id:
        raise ValueError(f'Column \'{column_title}\' not found in sheet \'{sheet_id}\'.')

    sort_criteria = [
        {
            'columnId': column_id,
            'ascending': ascending
        }
    ]
    payload = {'sortCriteria': sort_criteria}

    url = SS_BASE_URL + SS_SHEET_URL + f'{sheet_id}/sort'
    response = rate_limiter_passthru(url=url, request='post', post_data=payload, return_all=True, verbose=verbose)

    print(response) if verbose else None
    return response


def update_row():
    # todo: options to receive row from JSON or DataFrame
    pass
