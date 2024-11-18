# Smartsheet API 101

I haven't seen a lot of examples for interacting with the Smartsheet API. There are surely many people who need to pull data off Smartsheet, but are either not experienced programmers, or don't have the time to futz around with it.

This is intended as a one-stop shop, growing repository of simple examples of how to I/O your Smartsheet assets, manipulate the data therein, and push it to other services.

This repo initially used the Smartsheet SDK, but there's more flexibility accessing Smartsheet's back-end directly, with the Python `requests` library, the documentation on which can be <a href="https://requests.readthedocs.io/en/latest/">found here</a>, and installed with:

```
pip install requests
```

## Getting started with the Smartsheet API

These examples require a Smartsheet access token (you can find instructions for that <a href="http://smartsheet-platform.github.io/api-docs/#authentication-and-access-tokens">here</a> (alternatively, <a href="https://www.youtube.com/watch?v=FPXXY_G7eH8&t=646s">this video</a> from Smartsheet is queued to how to generate an access token), and for most of these functions, you need to know the ID of the object you're trying to interact with.

You can get a Smartsheet sheet ID via `File > Properties`, and a Smartsheet row ID by right clicking on the row's number.

For example, to get a dictionary of column names and ID from a given sheet:

```
get_column_dict(sheet_id='2109142850895624')

# returns:
{
    'Created Date': 2109142850895624,
    'Status': 2109142850895625,
    'Description': 2109142850895626,
    'Assigned To': 2109142850895627,
    ...
}
```

Or to return only the column ID in question:

```
get_col_id_from_col_name(
    sheet_id='2109142850895624',
    col_name='Project Status'
)

# returns column ID
```

If you're new to working with APIs, <a href="https://www.getpostman.com/">Postman</a> is a great tool. They have a <a href="https://www.youtube.com/watch?v=YKalL1rVDOE&list=PLM-7VG-sgbtBsenu0CM-UF3NZj3hQFs7E">series of getting started with APIs videos here</a>, if you are so inclined.
