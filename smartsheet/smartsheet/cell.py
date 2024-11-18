import pandas as pd
import re

from smartsheet.core.api import (
    rate_limiter_passthru
)

from smartsheet.core.constants import (
    SS_BASE_URL,
    SS_CELL_HISTORY_URL,
    SS_COLUMN_URL,
    SS_ROW_URL,
    SS_SHEET_URL
)

from smartsheet.smartsheet.column import (
    format_contact_list,
    format_multi_contact_list,
    format_multi_picklist
)

from smartsheet.smartsheet.row import (
    get_row_id_list
)

from smartsheet.smartsheet.sheet import (
    get_sheet_name
)


def cell_history(sheet_id, row_id, col_id, verbose=False):
    """
    Retrieves cell history for a specific sheet, row, and column.

    :param sheet_id:            str, required           sheet ID to pull cell history from
    :param row_id:              str, required           row ID to pull cell history from
    :param col_id:              str, required           column ID to pull cell history from
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response of cell history data, or empty list if error
    """

    url = SS_BASE_URL + SS_SHEET_URL + f'{sheet_id}/' + SS_ROW_URL + f'{row_id}/' + SS_COLUMN_URL + f'{col_id}/' + SS_CELL_HISTORY_URL
    print(url) if verbose else None

    response = rate_limiter_passthru(url=url, request='get', verbose=verbose)

    if response is None:
        print(f"Failed to retrieve cell history for row_id: {row_id}, col_id: {col_id}") if verbose else None
        return []

    try:
        cell_history_json = response[0]['data']                 # ensure response[0]['data'] exists before returning it
        return cell_history_json
    except (IndexError, KeyError, TypeError) as e:
        print(f"Error processing response: {e}") if verbose else None
        return []


def format_cell(value, col_id, col_type, domain):
    """
    Formats a cell's value based on column type and returns corresponding Smartsheet API structure.

    # todo: merge with smartsheet.smartsheet.sheet.convert_value()

    :param value:               str, required           cell value to format
    :param col_id:              str, required           column ID
    :param col_type:            str, required           column type (e.g., 'MULTI_CONTACT_LIST', 'TEXT_NUMBER', etc.)
    :param domain:              str, required           domain to attempt to make valid email address from data provided
    :return:                    JSON                    API response containing cell's data structure
    """

    if col_type == 'MULTI_CONTACT_LIST':
        return format_multi_contact_list(value, col_id, domain)

    elif col_type == 'MULTI_PICKLIST':
        return format_multi_picklist(value, col_id)

    elif col_type == 'CONTACT_LIST':
        return format_contact_list(value, col_id)

    elif bool(re.match(pattern=r'\[(.*?)\]\((.*?)\)', string=value)):           # if URL
        display = re.findall(pattern=r'\[(.*?)\]', string=value)[0]
        url = re.findall(pattern=r'\((.*?)\)', string=value)[0]
        return {'columnId': col_id, 'value': display, 'displayValue': display, 'hyperlink': {'url': url}}

    elif len(value) > 0 and value[0] == '=':                                    # if formula
        return {'columnId': col_id, 'formula': value}

    elif len(value) > 0:                                                        # if plain value
        return {'columnId': col_id, 'value': value}

    return None


def cell_history_to_df(sheet_id, column_dict, verbose=False):
    """
    Retrieves cell history for all rows and specified columns in a Smartsheet and converts it to a DataFrame.

    :param sheet_id:            str, required           sheet ID to retrieve data from
    :param column_dict:         dict, required          dict of column names (keys) and column IDs (values)
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    df                      DataFrame of cell history for all specified columns and rows
    """

    sheet_name = get_sheet_name(sheet_id)                                       # get sheet name
    row_ids = get_row_id_list(sheet_id)                                         # get all row IDs for given sheet

    all_cell_history = []

    # loop through each column name and ID from dict
    for column_name, col_id in column_dict.items():

        # loop through each row ID in sheet
        for row_id in row_ids:

            # get cell history for given column and row
            cell_history_json = cell_history(sheet_id, row_id, col_id, verbose=verbose)

            for history in cell_history_json:                                   # prepare data for DataFrame
                all_cell_history.append({
                    'sheet_name': sheet_name,
                    'row_id': row_id,
                    'column_id': col_id,
                    'column_name': column_name,
                    'column_type': history.get('columnType'),
                    'value': history.get('value'),
                    'display_value': history.get('displayValue'),
                    'modified_at': history.get('modifiedAt'),
                    'modified_by': history['modifiedBy']['name'],
                    'modified_by_email': history['modifiedBy']['email']
                })

    return pd.DataFrame(all_cell_history)                                       # return as pandas DataFrame
