import re
import requests

from smartsheet.core.constants import (
    API_HEADER_SS,
    SS_SHEET_URL,
    SS_COLUMN_URL,
    SS_BASE_URL
)

from smartsheet.core.sql import (
    rate_limiter_passthru
)

from smartsheet.core.toolkit import (
    check_email,
    get_slim_metadata
)

from smartsheet.smartsheet.sheet import (
    get_sheet
)


def format_cell(value, col_id, col_type):
    """
    Formats a cell's value based on column type and returns corresponding Smartsheet API structure.

    The parameter col_type is the Smartsheet column type to format, as follows:

        'TEXT_NUMBER'
        'PICKLIST'
        'MULTI_PICKLIST'
        'CONTACT_LIST'
        'MULTI_CONTACT_LIST'
        'CHECKBOX'
        'DATE' 'DATETIME'       # todo: only one of these actually exists as a selectable type on the front-end

    As of 9/1/2023, these types are in API, but are not selectable column types on Smartsheet front-end:

        'ABSTRACT_DATETIME',
        'DURATION',
        'PREDECESSOR'

    Returns as follows:

    :param value:               str, required           cell value to format
    :param col_id:              str, required           column ID
    :param col_type:            str, required           column type
    :return:
    """

    if col_type == 'MULTI_CONTACT_LIST':
        return format_multi_contact_list(value, col_id)

    elif col_type == 'MULTI_PICKLIST':
        return format_multi_picklist(value, col_id)

    elif col_type == 'CONTACT_LIST':
        return format_contact_list(value, col_id)

    elif bool(re.match(pattern=r"\[(.*?)\]\((.*?)\)", string=value)):   # hyperlink check
        display = re.findall(pattern=r"\[(.*?)\]", string=value)[0]
        url = re.findall(pattern=r"\((.*?)\)", string=value)[0]
        return {'columnId': col_id, 'value': display, 'displayValue': display, 'hyperlink': {'url': url}}

    elif len(value) > 0 and value[0] == '=':                            # formula
        return {'columnId': col_id, 'formula': value}

    elif len(value) > 0:                                                # plain value
        return {'columnId': col_id, 'value': value}

    return None


def format_contact_list(value, col_id, domain=None):
    """
    Formats a cell for a CONTACT_LIST Smartsheet column type, converting an alias or email into a dictionary structure
    suitable for use with the Smartsheet API.

    If input is a valid email, it is returned as-is; otherwise, input is treated as an alias and a placeholder email is
    generated using value and a provided domain (e.g. 'smartsheet.com').

    In some cases, columns containing aliases may also contain names, and as Smartsheet text field input cannot be
    tightly controlled, to limit errors caused by names (e.g. 'Matthew Runde' instead of 'mrunde'), spaces are replaced
    by underscores. Generally, this will simply cause a join error or erroneous data which can be handled downstream,
    but is required to make this work in Smartsheet, given its limitations.

    For this reason, even though domain is an optional parameter, it should be considered required wherever possible.

    If value is email address, returns as follows:

        {'columnId': 2109142850895624, 'value': 'matthew@nicejacket.cc'}

    If value is not email address and domain (e.g. 'smartsheet.com') provided, returns as follows:

        {'columnId': 2109142850895624, 'value': 'runde@smartsheet.com', 'displayValue': 'runde'}

    If value is not email address and not a domain, it may cause issues downstream, but returns as follows:

        {'columnId': 2109142850895624, 'value': 'Matthew_Runde@smartsheet.com', 'displayValue': 'Matthew Runde'}

    :param value:               str, required           cell value which should contain a single email or name
    :param col_id:              str, required           column ID to retrieve contact list from
    :param domain:              str, optional           if not None, attempts to make valid email address from data provided
    :return:                    dict                    dict of column ID and value, if not email, also display value
    """

    if not value:
        return None

    # if valid email address
    if check_email(value):
        return {'columnId': col_id, 'value': value}

    # if not valid email address and domain provided
    if domain is not None:
        email_placeholder = f'{value.replace(' ', '_')}@{domain}'       # todo: test; may fail in some circumstances
        return {'columnId': col_id, 'value': email_placeholder, 'displayValue': value}

    return None


def format_multi_contact_list(value, col_id, domain):
    """
    Formats a cell for a MULTI_CONTACT Smartsheet column type.

    Formats a cell for a CONTACT_LIST Smartsheet column type, converting aliases or emails into a dictionary structure
    suitable for use with the Smartsheet API.

    If inputs are valid emails, they are returned as-is; otherwise, input is treated as alias and a placeholder email is
    generated using value and a provided domain (e.g. 'smartsheet.com').

    In some cases, columns containing aliases may also contain names, and as Smartsheet text field input cannot be
    tightly controlled, to limit errors caused by names (e.g. 'Matthew Runde' instead of 'mrunde'), spaces are replaced
    by underscores. Generally, this will simply cause a join error or erroneous data which can be handled downstream,
    but is required to make this work in Smartsheet, given its limitations.

    NOTE: unlike format_contact_list(), this function requires the domain parameter.    # todo: make domain optional

    :param value:               str, required           cell value which should contain comma-separated emails or names
    :param col_id:              str, required           column ID to retrieve contact list from
    :param domain:              str, required           domain to attempt to make valid email address from data provided
    :return:                    dict                    dict of column ID and multi-contact values
    """

    if not value:
        return None

    values = [
        {'objectType': 'CONTACT', 'email': email.strip() if check_email(
            email.strip()) else f'{email.strip().replace(' ', '_')}@{domain}'}
        for email in value.split(',')
    ]
    return {'columnId': col_id, 'objectValue': {'objectType': 'MULTI_CONTACT', 'values': values}}


def format_multi_picklist(value, col_id):
    """
    Formats a cell for a MULTI_PICKLIST Smartsheet column type.

    :param value:               str, required           cell value which should contain comma-separated values
    :param col_id:              str, required           column ID to retrieve picklist from
    :return:                    dict                    dict of column ID and MULTI_PICKLIST values
    """

    if not value:
        return None

    formatted_multi_picklist = {
        'columnId': col_id,
        'objectValue': {
            'objectType': 'MULTI_PICKLIST',
            'values': [v.strip() for v in value.split(',')]
        }
    }
    return formatted_multi_picklist


def get_column_dict(sheet_id, verbose=False):
    """
    Extracts a dictionary of column names and their corresponding IDs from a Smartsheet-like dictionary.

    Returns as follows:

        {
            'Created Date': 2109142850895624,
            'Status': 2109142850895625,
            'Description': 2109142850895626,
            'Assigned To': 2109142850895627,
            ...
        }

    :param sheet_id:            str, required           sheet ID to retrieve column data from
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    dict                    dict of column names and column IDs
    """

    col_json = get_sheet(sheet_id=sheet_id, slim_metadata=False, verbose=verbose)
    return {col['title']: col['id'] for col in col_json[0]['columns']}


def get_sheet_column_metadata(sheet_id, base_keys=None, additional_keys=None, format_for_comparison=False, verbose=False):
    """
    Retrieves metadata for columns of a Smartsheet sheet, including column names and types. Optionally formats metadata
    for easier comparison with DataFrame columns.

    By default, returns as follows:

        [
            {
                'id': 2109142850895624,
                'title': 'Date Created',
                'type': 'DATETIME'
            },
            {
                'id': 2109142850895625,
                'title': 'Status',
                'type': 'PICKLIST'
            },
            {
                'id': 2109142850895626,
                'title': 'Notes',
                'type': 'TEXT_NUMBER'
            }
        ]

    If format_for_comparison is True:

        {
            'Date Created': 'datetime64[ns]',
            'Status': 'category',
            'Notes': 'object'
        }

    :param sheet_id:                str, required       sheet ID to retrieve column metadata from
    :param base_keys:               list, optional      list of base keys to extract from metadata
    :param additional_keys:         list, optional      additional keys to extract from metadata
    :param format_for_comparison:   bool, optional      if True, formats metadata for comparison with DataFrame columns
    :param verbose:                 bool, optional      if True, print status to terminal
    :return:                        dict or list        column names and dtype dicts; or, list of dicts of column metadata
    """

    data = get_sheet(sheet_id=sheet_id, verbose=verbose)
    data = get_slim_metadata(
        data=data[0]['columns'],
        base_keys=base_keys,
        additional_keys=additional_keys,
        verbose=verbose
    )

    if format_for_comparison:
        metadata_dict = {col['title']: col['type'] for col in data}     # dict with col name as key and type as values

        # mapping Smartsheet types to pandas dtypes for easier comparison
        # todo: complete list and move to constants
        smartsheet_to_pandas = {
            'DATETIME': 'datetime64[ns]',
            'TEXT_NUMBER': 'object',                                    # handle as object; later convert if needed
            'PICKLIST': 'category',
            'CHECKBOX': 'bool',
            'TEXT': 'object'
        }

        formatted_metadata = {                                          # format for comparison
            col_name: smartsheet_to_pandas.get(col_type, 'object')      # default to 'object' if not in mapping
            for col_name, col_type in metadata_dict.items()
        }

        return formatted_metadata

    return data


def get_valid_columns(column_json):
    """
    Extracts valid column IDs and types from Smartsheet columns metadata.

    Returns a list of tuples (column ID and column name) for valid columns, excluding system columns and formulas.

    :param column_json:         list, required          list of dicts of columns from Smartsheet
    :return:                    list                    list of tuples for valid columns
    """

    return [
        (col['id'], col['type'])
        for col in column_json
        if 'formula' not in col and 'systemColumnType' not in col
    ]


def primary_column_exists(columns, verbose=False):
    """
    Validates that there is exactly one column with 'type' as 'TEXT_NUMBER' and 'primary' set to True.

    :param columns:             list, required          list of dicts containing 'type' and 'primary' keys
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    bool                    if exactly one valid primary TEXT_NUMBER column True, else False
    """

    primary_text_number_count = sum(
        1 for column in columns if column.get('type') == 'TEXT_NUMBER' and column.get('primary') is True
    )

    print('Primary column exists.') if verbose else None

    return primary_text_number_count == 1


def add_column(sheet_id, column_name, column_type='TEXT_NUMBER', primary=False, index=0, symbol=None,
    options=None, auto_number_format=None, format_style=None, width=None, validation=None, verbose=False):
    """
    Adds a column to a Smartsheet sheet.

    Each row in columns_df must represent a column to add, with following attributes:
        - title:                str                     column title
        - type:                 str                     column type, one of following:          TODO: define valid types
        - index:                int                     zero-based index position for column

    Optional attributes for each column:
        - formula:              str                     formula for column (e.g., "=data@row")
        - autoNumberFormat:     dict                    format settings for an AUTO_NUMBER system column
        - description:          str                     column description
        - locked:               bool                    indicates if column is locked
        - options:              list of str             values for PICKLIST or MULTI_PICKLIST column types
        - symbol:               str                     symbol settings for CHECKBOX or PICKLIST types
        - systemColumnType:     str                     system column type (e.g., AUTO_NUMBER)
        - validation:           bool                    enables validation for PICKLIST and MULTI_PICKLIST types
        - width:                int                     column display width in pixels

    For symbol parameter, full list of options: https://smartsheet.redoc.ly/tag/columnsRelated#section/Column-Types/Symbol-Columns

    For format_style parameter, full list of options: https://smartsheet.redoc.ly/#section/API-Basics/Formatting

    :param sheet_id:            str, required           sheet ID to add column to
    :param column_name:         str, required           column name to add to sheet
    :param column_type:         str, optional           column type, e.g. TEXT_NUMBER
    :param primary:             bool, optional          if True, this column is primary column in sheet
    :param index:               int, optional           position index where column should be added
    :param symbol:              str, optional           value for symbol type
    :param options:             list, optional          list of options in dropdown; required if type is PICKLIST
    :param auto_number_format:  dict, optional          sets format for AUTO_NUMBER column type (prefix, suffix, fill)
    :param format_style:        str, optional           format style for column text
    :param width:               int, optional           sets column width in pixels
    :param validation:          bool, optional          enables strict picklist validation for PICKLIST column type
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response with details of added column
    """

    url = SS_BASE_URL + SS_SHEET_URL + f'{sheet_id}/' + SS_COLUMN_URL
    data = {
        'title': column_name,
        'type': column_type,
        'primary': primary,
        'index': index
    }

    if symbol:
        data['symbol'] = symbol
    if options:
        data['options'] = options
    if auto_number_format:
        data['autoNumberFormat'] = auto_number_format
    if format_style:
        data['format'] = format_style
    if width:
        data['width'] = width
    if validation is not None:
        data['validation'] = validation

    print(f'Adding column \'{column_name}\' with data: {data} to sheet {sheet_id}...') if verbose else None

    response = requests.post(url, headers=API_HEADER_SS, json=data)     # todo: standardise

    if response.status_code == 200:
        if verbose:
            print(f'Column \'{column_name}\' added successfully.')
        return response.json()
    else:
        if verbose:
            print(f'Failed to add column \'{column_name}\': {response.status_code} - {response.text}')
        return {'error': response.status_code, 'message': response.text}


def update_column(sheet_id, column_id, column_name=None, column_type=None, primary=None, symbol=None, options=None,
                  auto_number_format=None, format_style=None, width=None, validation=None, verbose=False):
    """
    Updates a column in a Smartsheet sheet.

    For symbol parameter, full list of options: https://smartsheet.redoc.ly/tag/columnsRelated#section/Column-Types/Symbol-Columns

    For format_style parameter, full list of options: https://smartsheet.redoc.ly/#section/API-Basics/Formatting

    Returns as follows:

        {
            'message': 'SUCCESS',
            'resultCode': 0,
            'version': 21,
            'result': {
                'id': 2109142850895624,
                'index': 0,
                'title': 'Updated Column Name',
                'type': 'TEXT_NUMBER',
                'validation': False,
                'width': 200
            }
        }

    :param sheet_id:            str, required           sheet ID
    :param column_id:           str, required           column ID to update
    :param column_name:         str, optional           new column name
    :param column_type:         str, optional           new Smartsheet column type for column
    :param primary:             bool, optional          if True, this column is primary column in sheet
    :param symbol:              str, optional           value for symbol type
    :param options:             list, optional          list of options in dropdown; required if type is PICKLIST
    :param auto_number_format:  dict, optional          sets format for AUTO_NUMBER column types
    :param format_style:        str, optional           format style for column text
    :param width:               int, optional           column width in pixels
    :param validation:          bool, optional          enables strict validation for PICKLIST column type
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response confirming column update, or error if unsuccessful
    """

    url = SS_BASE_URL + SS_SHEET_URL + f'{sheet_id}/' + SS_COLUMN_URL + f'{column_id}'
    data = {}

    if column_name:
        data['title'] = column_name
    if column_type:
        data['type'] = column_type
    if primary is not None:
        data['primary'] = primary
    if symbol:
        data['symbol'] = symbol
    if options:
        data['options'] = options
    if auto_number_format:
        data['autoNumberFormat'] = auto_number_format
    if format_style:
        data['format'] = format_style
    if width:
        data['width'] = width
    if validation is not None:
        data['validation'] = validation

    print(f'Updating column \'{column_id}\' with data: {data} in sheet {sheet_id}...') if verbose else None

    response = requests.put(url, headers=API_HEADER_SS, json=data)      # todo: standardise
    return response


def delete_column(sheet_id, column_id, verbose=False):
    """
    Deletes a column from a Smartsheet sheet.

    :param sheet_id:            str, required           sheet ID
    :param column_id:           str, required           column ID
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response in JSON format
    """

    url = SS_BASE_URL + SS_SHEET_URL + f'{sheet_id}/' + SS_COLUMN_URL + f'{column_id}'

    print(f'Deleting column \'{column_id}\' from sheet {sheet_id}...') if verbose else None

    return requests.delete(url, headers=API_HEADER_SS)                  # todo: standardise


def get_column(sheet_id, column_id, slim_metadata=False, additional_keys=None, verbose=False):
    """
    Returns column metadata from a Smartsheet.

    :param sheet_id:            str, required           sheet ID to retrieve column data from
    :param column_id:           str, required           column ID to retrieve data from
    :param slim_metadata        bool, optional          if True, returns a limited JSON dict
    :param additional_keys:     list, optional          additional keys to preserve in metadata
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response in JSON format
    """

    url = SS_BASE_URL + SS_SHEET_URL + f'{sheet_id}/' + SS_COLUMN_URL + f'{column_id}/'
    print(url) if verbose else None

    response = rate_limiter_passthru(url=url, request='get', verbose=verbose)

    if slim_metadata:
        response = get_slim_metadata(
            data=response,
            base_keys=None,
            additional_keys=additional_keys,
            verbose=verbose
        )

    return response
