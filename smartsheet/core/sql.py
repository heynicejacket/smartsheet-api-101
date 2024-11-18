import pandas as pd
import sqlalchemy

from smartsheet.core.constants import (
    DTYPE_MAPPING
)


def create_engine(db, dialect, user, password, endpoint, mssql_driver=17, fast_executemany=False, verbose=False):
    """
    Creates a SQLAlchemy engine to connect to a specified database based on the provided dialect (Postgres, MySQL, or
    MSSQL).

    This function supports connection to PostgreSQL, MySQL, and Microsoft SQL Server. For MSSQL, mssql_driver parameter
    allows selecting ODBC driver version, and fast_executemany can be used for faster bulk inserts; for PostgreSQL and
    MySQL, use chunksize in db_to_df().

    For MySQL, the following library must be installed:

        pip install pymsql

    The function returns a SQLAlchemy engine object for database interactions.

    :param db:                  str, required           database name
    :param dialect:             str, required           'postgres', 'mysql', or 'mssql'; database type
    :param user:                str, required           database username
    :param password:            str, required           database password
    :param endpoint:            str, required           server hostname or IP address where database is hosted
    :param mssql_driver:        int, optional           driver version for connecting to Microsoft SQL Server
    :param fast_executemany:    bool, optional          if True, enables fast bulk inserts for MSSQL
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    object                  SQLAlchemy engine object for specified database
    """

    if dialect == 'postgres':
        engine = sqlalchemy.create_engine(
            url=f'postgresql://{user}:{password}@{endpoint}/{db}',
            echo=verbose
        )
    elif dialect == 'mysql':
        engine = sqlalchemy.create_engine(
            url=f'mysql+pymysql://{user}:{password}@{endpoint}/{db}',
            echo=verbose
        )
    elif dialect == 'mssql':
        engine = sqlalchemy.create_engine(
            url=f'mssql://{user}:{password}@{endpoint}/{db}'
            f'?driver=ODBC+Driver+{str(mssql_driver)}+for+SQL+Server',
            fast_executemany=fast_executemany,
            echo=verbose
        )
    else:
        print(f'dialect {dialect} invalid type; cannot create connection engine')
        return None

    print('Success: create_engine() successful to database {}.'.format(db)) if verbose else None

    return engine


def db_to_df(query, engine, verbose=False):
    """
    Executes a SQL query and returns result as a pandas DataFrame.

    :param query:               str, required       SQL query to execute and convert to pandas DataFrame
    :param engine:              object, required    SQLAlchemy engine object used to connect to database
    :param verbose:             bool, optional      if True, print status to terminal
    :return:                    df                  DataFrame from SQL query
    """

    try:
        return pd.read_sql(query, engine)

    except Exception as e:
        print(f'Error executing query: {e}') if verbose else None


def df_to_db(engine, df, tbl, if_tbl_exists, retrieve_dtype_from_db=False, dtype_override=None, chunksize=10000, verbose=False):
    """
    Connects to database and attempts to push a pandas DataFrame to a specified SQL table. Optionally checks or
    overrides column data types based on provided mappings or existing database table schema.

    If dtype_override provided, it will be used to cast DataFrame columns to specified SQL types before upload.
    Example as follows:

        {'col1': sqlalchemy.types.Integer(), 'col2': sqlalchemy.types.String()}

    If retrieve_dtype_from_db is True, function will fetch column types of existing SQL table and match DataFrame's
    dtypes to existing table schema.

    The function will check whether DataFrame's column types match SQL table's column types. If a mismatch occurs and
    can be cast, the function will attempt to convert columns. If conversion is not possible, it will fail.

    :param engine:                  object, required    SQLAlchemy engine object used to connect to database
    :param df:                      df, required        pandas DataFrame to upload to SQL
    :param tbl:                     str, required       name of table to push data to
    :param if_tbl_exists:           str, required       ‘fail’, ‘replace’, or ‘append’
    :param retrieve_dtype_from_db:  bool, optional      if True, retrieves column data types from existing SQL table
    :param dtype_override:          dict, optional      a dict to define column names and their SQL types
    :param chunksize:               int, optional       rows to be inserted at a time during bulk insert operations
    :param verbose:                 bool, optional      if True, print status to terminal
    :return:                        None
    """

    if df.empty:
        print('DataFrame is empty. Skipping SQL upload.') if verbose else None
        return

    # if needed, get column types from database
    db_col_types = get_sql_col_types(engine=engine, tbl=tbl) if retrieve_dtype_from_db else {}
    print(db_col_types) if verbose else None

    # if provided, apply dtype overrides
    if dtype_override:
        print(f'Using provided dtype_override: {dtype_override}') if verbose else None
        df = df.astype(dtype_override)

    # compare and cast DataFrame column types to match SQL table schema
    for col in df.columns:
        if col in db_col_types:
            expected_dtype = DTYPE_MAPPING.get(db_col_types[col].lower())
            if expected_dtype and str(df[col].dtype) != expected_dtype:
                try:
                    print(f'Casting column {col} from {df[col].dtype} to {expected_dtype}') if verbose else None
                    df[col] = df[col].astype(expected_dtype)
                except Exception as e:
                    raise TypeError(f'Cannot cast column \'{col}\' to {expected_dtype}: {e}')

    try:
        df.to_sql(name=tbl, con=engine, index=False, if_exists=if_tbl_exists, dtype=dtype_override, chunksize=chunksize)
        print(f'Successfully pushed data to {tbl}.') if verbose else None

    except Exception as e:
        print(f'Error during upload to SQL: {e}') if verbose else None
        raise


def get_sql_col_types(engine, tbl, verbose=False):
    """
    Given a table, retrieve column types from the database.

    Returned dict appears as follows:

        {
            'task_id': 'int',
            'task_name': 'nvarchar',
            'task_created': 'datetime',
            'task_completed': 'bit'
        }

    :param engine:              object, required        SQLAlchemy engine object used to connect to database
    :param tbl:                 str, required           name of table to push data to
    :param verbose:             bool, optional          if True, print status to terminal
    :return:                    dict                    dict of column names and dtypes
    """

    existing_table_query = f'SELECT column_name, data_type FROM information_schema.columns WHERE table_name = \'{tbl}\''
    print(existing_table_query) if verbose else None

    with engine.connect() as conn:
        existing_columns = pd.read_sql(existing_table_query, conn)
        db_col_types = dict(zip(existing_columns['column_name'], existing_columns['data_type']))

    print(f'Retrieved column types from {tbl}: {db_col_types}') if verbose else None

    return db_col_types
