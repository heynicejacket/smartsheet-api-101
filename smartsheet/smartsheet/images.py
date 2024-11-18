import os
import requests

from smartsheet.core.api import (
    rate_limiter_passthru,
    ss_post_upload
)

from smartsheet.core.constants import (
    MIME_TYPES,
    SS_BASE_URL,
    SS_CELL_IMAGE,
    SS_COLUMN_URL,
    SS_IMAGE_URL,
    SS_ROW_URL,
    SS_SHEET_URL
)

from smartsheet.smartsheet.sheet import (
    get_sheet
)


def download_images(urls, filepath, verbose=False):
    """
    Downloads images from a list or dictionary of URLs and saves each to specified directory.

    urls can be passed as a list of URLs, as follows:

        ['url', 'url', ...]

    or a dictionary with destination file names as keys, and image URLs as values, as follows:

        {
            'filename.jpg': 'url',
            'filename.jpg': 'url',
            ...
        }

    :param urls:                list or dict, required  list of image URLs or dict with filename and url
    :param filepath:            str, required           path to save downloaded images to
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    None
    """

    os.makedirs(filepath, exist_ok=True)

    if isinstance(urls, dict):
        items = urls.items()                            # for dict, (key, url) pairs for filenames
    else:
        items = enumerate(urls, start=1)                # for list, (idx, url) with numeric filenames

    for key, url in items:
        try:
            if verbose:
                print(f'Downloading image {key} from: {url}')

            response = requests.get(url, stream=True)
            response.raise_for_status()

            # use key directly as filename if dict, or autogenerate 'image_{idx}.jpg' if list
            filename = f'{key}.jpg' if isinstance(urls, dict) else f'image_{key}.jpg'
            save_path = os.path.join(filename, filename)

            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)

            print(f'Image {key} saved to: {save_path}') if verbose else None

        except requests.exceptions.RequestException as e:
            print(f'Error downloading image {key}: {e}')


def format_image_url_dict(column_data, image_name):
    """
    Helper function to format image URL dictionary from extracted column data.

    Given a dict as follows:

        {
            'khXfXF5SEjmdFT2mh1': 'https://aws.smartsheet.com/storageProxy/...',
            'khXfXF5SEjmdFT2mh2': 'https://aws.smartsheet.com/storageProxy/...',
            ...
        }

    image name can be 'row_id', 'rowNumber', 'value', or 'image_id'

    :param column_data:         dict, required          dict of image ID and URL
    :param image_name:          str, required           'row_id', 'rowNumber', 'value', or 'image_id'
    :return:                    dict                    dict mapping 'row_id-image_id' to image URLs
    """

    if image_name not in ('row_id', 'rowNumber', 'value', 'image_id'):
        raise ValueError(f'{image_name} is not a valid image metadata type.')

    return {
        f'{row[image_name]}': row['image_url']
        for row in column_data.get('rows', [])
        if 'image_url' in row
    }


def extract_image_column_data(sheet_id, column_id, slim_metadata=False, slim_metadata_key='image_id', verbose=False):
    """
    Returns a dictionary with column details, including image URLs.

    Returns as follows:

        {
            'column_id': 2109142850895624,
            'title': 'Image Column',
            'rows': [
                {
                    'row_id': 2109142850895624,
                    'rowNumber': 1,
                    'value': 'review.png',
                    'image_id': 'khXfXF5SEjmdFT2mh1',
                    'image_url': https://aws.smartsheet.com/...?expirationDate=2019-11-28T...&hmac=khXfXF5jmdFT2mh1'
                },
                ...
            ]
        }

    slim_metadata_key 'row_id', 'rowNumber', 'value', or 'image_id' can be passed to key value in
    format_image_url_dict()

    :param sheet_id:            str, required           sheet ID to extract image(s) from
    :param column_id:           str, required           column ID to extract
    :param slim_metadata        bool, optional          if True, returns a limited JSON dict
    :param slim_metadata_key:   str, optional           field to ensure is returned if slim_metadata=True
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response containing columns, rows, and image metadata
    """

    if slim_metadata_key not in ('row_id', 'rowNumber', 'value', 'image_id'):
        raise ValueError(f'{slim_metadata_key} is not a valid image metadata type.')

    sheet_json = get_sheet(sheet_id=sheet_id, slim_metadata=False, verbose=verbose)[0]

    column_data = next((col for col in sheet_json.get('columns', []) if str(col['id']) == column_id), None)
    if not column_data:
        return {}

    result = {
        'column_id': column_data['id'],
        'title': column_data['title'],
        'rows': []
    }

    image_rows = [
        {
            'row_id': row['id'],
            'rowNumber': row['rowNumber'],
            'value': cell['value'],
            'image_id': cell['image']['id']
        }
        for row in sheet_json.get('rows', [])
        for cell in row.get('cells', [])
        if str(cell['columnId']) == column_id and 'value' in cell and 'image' in cell
    ]

    # retrieve URLs and map to rows
    image_ids = [row['image_id'] for row in image_rows]
    image_urls = get_cell_image_urls(image_ids=image_ids, url_only=True, verbose=verbose)

    # assign URLs to rows
    for row, url in zip(image_rows, image_urls or []):
        row['image_url'] = url

    result['rows'] = image_rows

    if slim_metadata:
        return format_image_url_dict(column_data=result, image_name=slim_metadata_key)

    return result


def get_mime_type(mime_types, filepath):
    """
    Determines MIME type based on a given file's extension.

    mime_type dictionary should be structured as follows:

        {
            'images': {
                'jpeg': 'image/jpeg',
                ...
            },
            'documents': {
                'pdf': 'application/pdf',
                ...
            },
            ...
        }

    This function uses a dictionary of MIME types to map file extension of provided 'filepath' to its corresponding
    MIME type. If extension is not found, it defaults to 'application/octet-stream'.

    :param mime_type:           dict, required          dict containing MIME types (e.g., 'application/pdf')
    :param filepath:            str, required           path to file
    :return:                    str                     file's MIME type; 'application/octet-stream' if not found
    """

    flattened_mime_types = {ext: mime for types in mime_types.values() for ext, mime in types.items()}

    extension = os.path.splitext(filepath)[-1][1:].lower()                      # extract file ext, convert to lowercase
    return flattened_mime_types.get(extension, 'application/octet-stream')


def get_cell_image_urls(image_ids, url_only=True, verbose=False):
    """
    Retrieves an array of image URLs for specified cell images from Smartsheet.

    By default, returns as follows:

        [
            https://aws.smartsheet.com/...?expirationDate=2021-08-28T...&hmac=khXfXF5SEjmdFT2mh1,
            ...
        ]

    If url_only is set to False, returns as follows:

        {
            'urlExpiresInMillis': 1800000,
            'imageUrls': [
                {
                    'imageId': 'khXfXF5SEjmdFT2mh1',
                    'url': 'https://aws.smartsheet.com/...?expirationDate=2021-08-28T...&hmac=khXfXF5SEjmdFT2mh1'
                },
                ...
            ]
        }

    :param image_ids:           list, required          list of image IDs to retrieve URLs for
    :param url_only:            bool, optional          if False, returns cell image metadata
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    list or dict            list of cell image URLs, or dict containing cell image metadata
    """

    url = SS_BASE_URL + SS_IMAGE_URL
    print(url) if verbose else None

    payload = [{'imageId': image_id} for image_id in image_ids]

    response = rate_limiter_passthru(url=url, request='post', post_data=payload, return_all=True, verbose=verbose)
    print(response) if verbose else None

    if url_only:
        return [item['url'] for item in response['imageUrls']] if response['imageUrls'] else None

    return response


def add_image_to_cell(sheet_id, row_id, column_id, filepath, alt_text=None, override_validation=False, verbose=False):
    """
    Uploads an image to specified cell within a sheet.

    On success, returns JSON as follows:

        {
            'message': 'SUCCESS',
            'resultCode': 0,
            'result': [{
                'id': 2109142850895624,
                'rowNumber': 1,
                'expanded': True,
                'createdAt': '2019-08-09T21:19:56Z',
                'modifiedAt': '2022-11-13T22:14:00Z'
                'cells': [
                    {
                        'columnId': 2109142850895624,
                        'value': 'preview.png',
                        'displayValue': 'preview.png',
                        'formula': '=SYS_CELLIMAGE("preview.png","khXfXF5SEjmdFT2mh1",60,145,"preview.png")',
                        'image': {
                            'id': 'khXfXF5SEjmdFT2mh1',
                            'height': 60,
                            'width': 145,
                            'altText': 'preview.png'
                        }
                    },
                    {
                        'columnId': 2109142850895624,
                        'value': 'Cancelled',
                        'displayValue': 'Cancelled'
                    },
                    ...
                ]
            }]
        ,
        'version': 20
    }

    :param sheet_id:            int, required           sheet ID to add image to
    :param row_id:              int, required           row ID to add image to
    :param column_id:           int, required           column ID to add image to
    :param filepath:            str, required           path to image file to upload
    :param alt_text:            str, optional           alt text for image
    :param override_validation: bool, optional          if True, bypasses validation limits
    :param verbose:             bool, optional          if True, prints status to terminal
    :return:                    JSON                    API response in JSON format
    """

    url = SS_BASE_URL + SS_SHEET_URL + f'{sheet_id}/' + SS_ROW_URL + f'{row_id}/' + SS_COLUMN_URL + f'{column_id}/' + SS_CELL_IMAGE
    print(url) if verbose else None

    params = {}

    if alt_text:
        params['altText'] = alt_text
    if override_validation:
        params['overrideValidation'] = 'true'

    mime_type = get_mime_type(mime_types=MIME_TYPES, filepath=filepath)

    response = ss_post_upload(url=url, mime_type=mime_type, params=params, filepath=filepath, verbose=verbose)  # todo: standardise
    print(response) if verbose else None

    return response
