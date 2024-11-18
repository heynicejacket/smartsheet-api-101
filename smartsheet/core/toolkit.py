import re


def check_email(email):
    """
    Validates an email address against a regular expression pattern.

    :param email:               str, required           email address to validate
    :return:                    bool                    True if valid email address, else False
    """

    regex = r'^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$'
    return bool(re.search(regex, email))


def ensure_list_of_dicts(list_of_dicts):
    """
    Check if input is a list and first element is a dictionary. If not a list or list is empty, check if a dict. If not
    a list of dicts, wrap dict in a list. If not a dict or list of dicts, raise error. Else, return list of dicts.

    :param list_of_dicts:       list or dict, required  input to validate or transform
    :return:                    list                    list of dictionaries
    """

    try:
        if isinstance(list_of_dicts, list) and isinstance(list_of_dicts[0], dict):
            return list_of_dicts                                                    # already a list of dicts
        else:
            raise TypeError                                                         # not a list of dicts

    except (IndexError, TypeError):
        if isinstance(list_of_dicts, dict):
            return [list_of_dicts]                                                  # wrap dict into a list
        else:
            raise ValueError('The variable is neither a dict nor a list containing dicts')


def get_slim_metadata(data, base_keys=None, additional_keys=None, verbose=False):
    """
    Extracts a slimmed-down version of metadata from a JSON dictionary by retaining only specified keys.

    :param data:                list, required          JSON data to extract metadata from
    :param base_keys:           list, optional          list of keys to preserve in metadata; if None, ['id', 'name']
    :param additional_keys:     list, optional          additional keys to preserve in metadata
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    JSON                    API response in JSON format
    """

    if base_keys is None:
        base_keys = ['id', 'name']

    # merge base keys with additional keys, if provided
    keys_to_extract = base_keys + (additional_keys if additional_keys else [])

    extracted_data = []
    for item in data:
        extracted_item = {key: item[key] for key in keys_to_extract if key in item}
        extracted_data.append(extracted_item)

    return extracted_data


def get_file_info(attachment_json, file_path):
    """
    Extracts file information from an attachment JSON object and constructs full save path.

    attachment_json must have keys 'url' and 'name' to function within this project.

    :param attachment_json:     list, required           JSON object containing attachment details
    :param file_path:           str, required            path where file will be saved
    :return:                    tuple                    tuple containing file URL, name, and file path
    """

    file_url = attachment_json[0]['url']
    file_name = attachment_json[0]['name']
    full_save_path = f'{file_path}/{file_name}'

    return file_url, file_name, full_save_path
