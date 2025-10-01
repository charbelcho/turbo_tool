import duckdb
import pandas as pd

def create_user_table():
    with duckdb.connect("user.db") as con:
        con.sql("CREATE SEQUENCE IF NOT EXISTS user_seq")
        con.sql("""CREATE TABLE IF NOT EXISTS user (
                    user_index INTEGER DEFAULT nextval('user_seq') PRIMARY KEY,
                    vorname VARCHAR,
                    nachname VARCHAR,
                    email VARCHAR UNIQUE,
                    password VARCHAR,
                    profil VARCHAR)""")

def create_in_table():
    with duckdb.connect("file.db") as con:
        con.sql("CREATE SEQUENCE IF NOT EXISTS in_prices_seq")
        con.sql("""CREATE TABLE IF NOT EXISTS in_prices (
                    in_prices_index INTEGER DEFAULT nextval('in_prices_seq') PRIMARY KEY,
                    hochgeladen_am TIMESTAMP_S,
                    brand VARCHAR, 
                    product VARCHAR, 
                    code DOUBLE, 
                    your_price DOUBLE, 
                    tags VARCHAR, 
                    cost_price DOUBLE, 
                    rival_best_price DOUBLE, 
                    your_difference VARCHAR,
                    kalenderwoche INTEGER, 
                    jahr INTEGER)""")
        con.sql("""CREATE UNIQUE INDEX IF NOT EXISTS 
                    u_idx_in_prices ON in_prices (code, kalenderwoche, jahr)""")

def create_out_table():
    with duckdb.connect("file.db") as con:
        con.sql("CREATE SEQUENCE IF NOT EXISTS out_prices_seq")
        con.sql("""CREATE TABLE IF NOT EXISTS out_prices (
                    out_prices_index INTEGER DEFAULT nextval('in_prices_seq') PRIMARY KEY,
                    prozessiert_am TIMESTAMP_S,
                    lieferant VARCHAR, 
                    artikel VARCHAR, 
                    artikelnummer DOUBLE, 
                    meesenburg_vk DOUBLE,
                    ynek DOUBLE, 
                    vprs VARCHAR,
                    ykbn VARCHAR,
                    bester_wettbewerber_vk DOUBLE,
                    vk_zum_besten_wettbewerber VARCHAR,
                    me_vk_bester_preis VARCHAR,
                    preis_vorherige_kw DOUBLE,
                    kalenderwoche INTEGER, 
                    jahr INTEGER)""")
        con.sql("""CREATE UNIQUE INDEX IF NOT EXISTS 
                    u_idx_out_prices ON out_prices (artikelnummer, kalenderwoche, jahr)""")


def create_cols_map_in_table():
    with duckdb.connect("file.db") as con:
        con.sql("""CREATE TABLE IF NOT EXISTS cols_map_in (
                    spalte_input_datei VARCHAR NOT NULL, 
                    spalte_db VARCHAR NOT NULL)""")

        data = {'spalte_input_datei': ['Brand', 'Product', 'Code', 'Your Price', 'Tags', 'Cost Price',
                                       'Rival Best Price', 'Your Diff.' ],
                'spalte_db': ['brand', 'product', 'code', 'your_price', 'tags', 'cost_price',
                                       'rival_best_price', 'your_difference']}

        df = pd.DataFrame(data=data)
        con.sql(f"CREATE OR REPLACE TABLE cols_map_in AS SELECT * FROM df")


def create_cols_map_out_table():
    with duckdb.connect("file.db") as con:
        con.sql("""CREATE TABLE IF NOT EXISTS cols_map_out (
                    spalte_db VARCHAR NOT NULL, 
                    spalte_output_datei VARCHAR NOT NULL,
                    spalte_position INTEGER UNIQUE)""")

        data = {'spalte_db': ['lieferant', 'artikel', 'artikelnummer', 'meesenburg_vk', 'ynek', 'vprs', 'ykbn',
                              'bester_wettbewerber_vk', 'vk_zum_besten_wettbewerber', 'me_vk_bester_preis'],
                'spalte_output_datei': ['Lieferant', 'Artikel', 'Artikelnummer', 'Meesenburg VK', 'YNEK', 'VPRS',
                                        'YKBN', 'Bester Wettbewerber VK', 'VK zum besten Wettbewerber',
                                        'ME VK bester Preis'],
                'spalte_position': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]}

        df = pd.DataFrame(data=data)
        con.sql(f"CREATE OR REPLACE TABLE cols_map_out AS SELECT * FROM df")


def select(table: str, connect_to='file', cols=None) -> pd.DataFrame:
    if cols is None:
        cols = []
    with duckdb.connect(f"{connect_to}.db") as con:
        return con.sql(f"""SELECT {','.join(cols) if cols else '*'} FROM {table}""").df()


def select_distinct(table: str, cols: list) -> pd.DataFrame:
    with duckdb.connect("file.db") as con:
        return con.sql(f"""SELECT distinct {','.join(cols)} FROM {table}""").df()


def select_where(table: str, col_value: dict, cols=None) -> pd.DataFrame:
    if cols is None:
        cols = []
    with duckdb.connect("file.db") as con:
        return con.sql(f"""
            SELECT {','.join(cols) if cols else '*'} 
            FROM {table} WHERE {" AND ".join([f"{k} = {v}" for k, v in col_value.items()])}""").df()


def insert(table: str, data: pd.DataFrame, connect_to='file') -> bool:
    with duckdb.connect(f"{connect_to}.db") as con:
        try:
            con.sql(f"INSERT INTO {table} BY NAME SELECT * FROM data")
            return True
        except Exception as ex:
            return False

def update(table: str, orig_data: pd.DataFrame, update_data: pd.DataFrame, connect_to='file') -> bool:
    with duckdb.connect(f"{connect_to}.db") as con:
        try:
            con.sql(f"UPDATE {table} SET BY NAME SELECT * FROM data")
            return True
        except Exception as ex:
            return False

def delete(table: str, col_value: dict) -> bool:
    with duckdb.connect("file.db") as con:
        try:
            con.sql(f"""DELETE FROM {table} WHERE {" AND ".join([f"{k} = {v}" for k, v in col_value.items()])}""")
            return True
        except Exception as ex:
            return False

def delete_where_data_df(table: str, df_col_value: pd.DataFrame) -> bool:
    with duckdb.connect("file.db") as con:
        try:
            for i in range(df_col_value.shape[0]):
                row = df_col_value.iloc[i]
                where_clause = " AND ".join(
                    f"{col} = '{row[col]}'" if isinstance(row[col], str) else f"{col} = {row[col]}"
                    for col in row.index
                )
                con.sql(f"""DELETE FROM {table} WHERE {where_clause}""")
                con.sql(f"""DELETE FROM {'out_prices'} WHERE {where_clause}""")
            return True
        except Exception as ex:
            print(ex)
            return False


def speichern_in_db(data: pd.DataFrame, table: str) -> (bool, str):
    if not data.empty:
        if data[data.columns].isna().any().any():
            return False, 'Mindestens ein Wert ist None. Bitte überprüfen'
        if data.shape[0] > 1:
            for col in data.columns:
                if not data.loc[data.duplicated(subset=[col])].empty:
                    return False, f'Doppelter Wert in Spalte: {col}. Bitte überprüfen'
            with duckdb.connect("file.db") as con:
                con.sql(f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM data")
                return True, 'Daten gespeichert'
    else:
        return False, 'Keine Daten eingefügt'

