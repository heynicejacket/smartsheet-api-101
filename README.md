![smartsheet-api-101](https://github.com/heynicejacket/smartsheet-api-101/blob/master/smartsheet-api-101-banner-transparent.png)

## The 101

I haven't seen a lot of examples for interacting with the Smartsheet API. There are surely many people who need to pull data off Smartsheet, but are either not experienced programmers, or don't have the time to futz around with it.

This is intended as a one-stop shop, growing repository of simple examples of how to I/O your Smartsheet assets, manipulate the data therein, and push it to other services.

This repo initially utilized the Smartsheet SDK, but there's more flexibility accessing Smartsheet's back-end directly, with the Python `requests` library, the documentation on which can be <a href="https://requests.readthedocs.io/en/latest/">found here</a>.

For more information, see the <a href="https://smartsheet.redoc.ly/">Smartsheet API documentation</a>.

## Basic implementation

🚨 _See [smartsheet-api-101, Issue #1](https://github.com/heynicejacket/smartsheet-api-101/issues/2): Test sets TBD, in `smartsheet.test`_

These examples require a Smartsheet access token. You can find instructions for that <a href="http://smartsheet-platform.github.io/api-docs/#authentication-and-access-tokens">here</a>.

You can get a Smartsheet sheet ID via `File > Properties`, and a Smartsheet row ID by right clicking on the row's number. Given that, you can convert your sheet directly into a pandas DataFrame with:

```
smartsheet_to_df(sheet_id='2109142850895624')
```

For most of these functions, you need to know the ID of the object you're trying to interact with. These are often not immediately apparent or accessible, and the Smartsheet API documentation, while robust, can sometimes require you to jump from place to place to get what you need.

Hopefully, these functions streamline this.

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

## Additional helper functions

#### smartsheet.core.sql.create_engine()

A one-stop shop for creating a SQLAlchemy engine for MSSQL, postgreSQL, or MySQL.

Many users will have their own constructions of this, or will simply use the basic SQLAlchemy functions to do this, but this is a helpful tool for doing the connection formatting work for you.

```
# create SQLAlchemy connection engine
engine = create_engine(
    db=db,                          # name of database
    dialect=dialect,                # 'postgres', 'mysql', or 'mssql'
    user=user,
    password=password,
    endpoint=endpoint,
    verbose=True                    # if True, prints status to terminal; for dev and debug
)
```

#### smartsheet.core.sql.db_to_df()

While many users will have their own construction of this, this is a variant on `pd.read_sql()` with built-in error handling. Given a SQLAlchemy engine and a SQL query, returns the query as a DataFrame.

```
query = """
    SELECT * FROM project_audit_trail
"""

df = db_to_df(
    query=query,
    engine=engine,
    verbose=True
)
```

#### smartsheet.core.sql.df_to_db()

This function utilises `df.to_sql()` to push a DataFrame to SQL, with the optional functionality of handling dtypes between DataFrames and SQL to ensure successful upload.

```
df_to_db(
    engine=engine,
    df=df,
    tbl='event_log_with_time',      # name of SQL table to upload data to
    if_tbl_exists='replace',        # as with df.to_sql()
    retrieve_dtype_from_db=True,    # if True, recasts DataFrame with SQL field types
    dtype_override=None,            # dictionary of column names and dtypes
    chunksize=10000,
    verbose=True
)
```

#### smartsheet.core.sql.get_sql_col_types()

Helper function to retrieve column types from SQL tables.

🚨 _See [Chronumbo, Issue #5](https://github.com/heynicejacket/chronumbo/issues/5); This function currently only supports postgreSQL._

```
get_sql_col_types(
    engine=engine,
    tbl=tbl,
    verbose=True
)
```
