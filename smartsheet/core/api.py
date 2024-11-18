import requests
import time
from random import random

from smartsheet.core.constants import (
    ACCESS_TOKEN_SS,
    API_HEADER_SS
)

from smartsheet.core.toolkit import (
    ensure_list_of_dicts
)


def create_upload_header(mime_type, filepath, verbose=False):
    """
    Assembles and returns headers required for uploading a file to Smartsheet.

    :param mime_type:           str, required           MIME type of file being uploaded (e.g., 'application/pdf')
    :param filepath:            str, required           path to file being uploaded
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    dict                    headers for upload request
    """

    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN_SS}',
        'Content-Type': f'{mime_type}',
        'Content-Disposition': f'attachment; filename="{filepath.split("/")[-1]}"'
    }
    print(headers) if verbose else None

    return headers


def format_column_headers(df):
    """
    Replace all spaces in DataFrame column headers with underscores and convert them to lowercase. For example:

        Created Date
        Status
        Project ID

    ...is converted to:

        created_date
        status
        project_id

    :param df:                  df, required            DataFrame whose column headers to be modified
    :return:                    df                      DataFrame with modified columns
    """

    df.columns = df.columns.str.replace(' ', '_').str.lower()
    return df


def rate_limiter_passthru(url, request='get', post_data=None, return_all=False, verbose=False, **kwargs):
    """
    Rate limiter function that calls appropriate Smartsheet helper function based on request type.

    :param url:                 str, required           URL to send request to
    :param request:             str, required           HTTP request method ('get', 'post', 'put', 'delete')
    :param post_data:           dict, required          data to send with POST or PUT requests
    :param return_all:          bool, optional          if True, only return data dict; else, entire JSON dict
    :param verbose:             bool, optional          if True, print status to terminal
    :param kwargs:                                      additional parameters to be passed to helper functions
    :return:                    JSON                    API response from helper function, or None if failure
    """

    code = 429
    attempts = 0
    max_attempts = 5

    r = request.lower()

    if r not in ('get', 'delete', 'put', 'post'):
        raise ValueError(f'{r} is not a valid HTTP request type.')

    while code == 429 and attempts < max_attempts:
        if r == 'delete':
            response = ss_delete(url, verbose=verbose, **kwargs)
        elif r == 'get':
            response = ss_get(url, params=post_data, return_all=return_all, verbose=verbose)
        elif r == 'put':
            response = ss_put(url, payload=post_data, return_all=return_all, verbose=verbose, **kwargs)
        elif r == 'post':
            response = ss_post(url, payload=post_data, return_all=return_all, verbose=verbose, **kwargs)

        if response is None:
            print(f"Failed to get a valid response for {request} request") if verbose else None
            return None

        # ensure response has status code or use 200 as default
        code = response.status_code if hasattr(response, 'status_code') else 200

        if code == 429:
            print(f'{request} status returns {code}\n===== hit rate limit! =====') if verbose else None
        else:
            print(f'{request} status returns {code}') if verbose else None

        if code == 429:
            time.sleep((2 ** attempts) + random())                                      # exponential backoff
            attempts += 1
        elif code != 200:
            print(f'HTTP Error: {code} for URL: {url}') if verbose else None            # if not 200 or 429, return error
            return None
        else:
            return response

    if attempts == max_attempts:
        print(f'Max retry attempts reached for URL: {url}') if verbose else None
        return None

    return None


def ss_delete(url, return_all=False, verbose=False):
    """
    Sends a DELETE request to specified Smartsheet URL.

    :param url:                 str, required           URL to send request to
    :param return_all:          bool, optional          if True, only return data dict; else, entire json dict
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response in JSON format
    """

    try:
        response = requests.delete(url, headers=API_HEADER_SS)
        response.raise_for_status()
        return response.json() if return_all else response.json()
    except requests.exceptions.HTTPError as err:
        print(f'HTTP Error: {err}') if verbose else None
        return None


def ss_get(url, params=None, return_all=False, verbose=False):
    """
    Sends a GET request to specified Smartsheet URL.

    If returning multiple, [ { ... }, { ... }, { ... }, ... ]

    If returning a single sheet, { ... } hence needing to _ensure_list_of_dicts()

    :param url:                 str, required           URL to send request to
    :param params:              dict, optional          additional query parameters to include in GET request
    :param return_all:          bool, optional          if True, only return data dict; else, entire json dict
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response in JSON format
    """

    try:
        response = requests.get(url, headers=API_HEADER_SS, params=params)
        response.raise_for_status()

        if not return_all:
            return ensure_list_of_dicts(list_of_dicts=response.json())                 # convert dict to list of dicts

        return response

    except requests.exceptions.HTTPError as err:
        print(f'HTTP Error: {err}') if verbose else None
        return None


def ss_post(url, payload, return_all=False, verbose=False, **kwargs):
    """
    Sends a POST request to specified Smartsheet URL with provided payload.

    :param url:                 str, required           URL to send request to
    :param payload:             dict, required          JSON payload to include in POST request
    :param return_all:          bool, optional          if True, only return data dict; else, entire json dict
    :param verbose:             bool, optional          if True, print status to terminal
    :param kwargs:              dict, optional          additional keyword arguments to pass to POST call
    :return:                    JSON                    API response in JSON format
    """

    try:
        # response = requests.post(url=url, headers=API_HEADER_SS, data=json.dumps(payload))
        response = requests.post(url=url, headers=API_HEADER_SS, json=payload, **kwargs)
        response.raise_for_status()
        return response.json() if return_all else response.json().get('data')
    except requests.exceptions.HTTPError as err:
        print(f'HTTP Error: {err}') if verbose else None
        return None


def ss_post_upload(url, mime_type, filepath, params=None, verbose=False):
    """
    Uploads a file to specified Smartsheet URL using a POST request.

    :param url:                 str, required           URL to send upload request to
    :param mime_type:           str, required           MIME type of file being uploaded (e.g., 'application/pdf')
    :param filepath:            str, required           path to file to be uploaded
    :param params:              dict, optional          additional query parameters to include in POST request
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response confirming upload or error details
    """

    headers = create_upload_header(mime_type=mime_type, filepath=filepath, verbose=verbose)

    try:
        with open(filepath, 'rb') as file_data:
            if params is not None:
                response = requests.post(url=url, headers=headers, params=params, data=file_data)
            else:
                response = requests.post(url=url, headers=headers, files={'file': file_data})
            response.raise_for_status()
            return response.json()

    except FileNotFoundError:
        raise FileNotFoundError(f'File not found: {filepath}')

    except requests.exceptions.RequestException as err:
        print(f'Error uploading {filepath}: {err}') if verbose else None


def ss_put(url, payload, return_all=False, verbose=False, **kwargs):
    """
    Sends a PUT request to specified Smartsheet URL with given payload.

    :param url:                 str, required           URL to send request to
    :param payload:             dict, required          JSON payload to include in PUT request
    :param return_all:          bool, optional          if True, return entire JSON response; else, return 'data' field
    :param verbose:             bool, optional          if True, print status to terminal
    :param kwargs:              dict, optional          additional keyword arguments to pass to PUT call
    :return:                    JSON                    API response in JSON format
    """

    try:
        # response = requests.put(url, headers=API_HEADER_SS, data=json.dumps(payload))
        response = requests.put(url=url, headers=API_HEADER_SS, json=payload, **kwargs)
        response.raise_for_status()
        return response.json() if return_all else response.json().get('data')
    except requests.exceptions.HTTPError as err:
        print(f'HTTP Error: {err}') if verbose else None
        return None


def ss_put_upload(url, filepath, filename, verbose=False):
    """
    Uploads a file to specified Smartsheet URL using a PUT request.

    :param url:                 str, required           URL to send request to
    :param filepath:            str, required           path to file to be uploaded
    :param filename:            str, required           name of file as it should appear in Smartsheet
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response confirming upload or error details
    """

    try:
        with open(filepath, 'rb') as file:
            files = {'file': (filename, file, 'application/octet-stream')}
            response = requests.put(url=url, headers=API_HEADER_SS, files=files)
            response.raise_for_status()
            return response.json()

    except FileNotFoundError:
        raise FileNotFoundError(f'File not found: {filepath}')

    except requests.exceptions.RequestException as err:
        print(f'Error uploading {filename}: {err}') if verbose else None
