import duckdb
import pandas as pd
from argon2 import PasswordHasher
import streamlit as st
from supabase import create_client

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

ph = PasswordHasher()

def create_user_table():
    with duckdb.connect("user.db") as con:
        con.sql("CREATE SEQUENCE IF NOT EXISTS user_seq")
        con.sql("""CREATE TABLE IF NOT EXISTS user (
                    user_index INTEGER PRIMARY KEY,
                    vorname VARCHAR NOT NULL,
                    nachname VARCHAR NOT NULL,
                    email VARCHAR UNIQUE NOT NULL,
                    password VARCHAR NOT NULL,
                    profil VARCHAR,
                    freigeschaltet BOOL NOT NULL)""")
        con.sql(f"""INSERT OR IGNORE INTO user (user_index, vorname, nachname, email, password, profil, freigeschaltet) VALUES
                (0, 'Charbel', 'Chougourou', 'admin', '{ph.hash('test')}', 'Super User', 'true')""")
        con.sql("""ALTER TABLE user ALTER COLUMN user_index SET DEFAULT nextval('user_seq')""")


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
                                       'Rival Best Price', 'Your Diff.'],
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

def insert_on_app_start():
    if len(select("user")) == 0:
        d = {'user_id': [0],
             'vorname': ['Charbel'],
             'nachname': ['Chougourou'],
             'email': ['admin'],
             'password': [ph.hash('test')],
             'profil': ['Super User'],
             'freigeschaltet': ['true']}
        data = pd.DataFrame(data=d)
        insert("user", data)

def select(table: str, cols=None) -> pd.DataFrame:
    if cols is None:
        cols = []
    res = (
        supabase.table(table)
        .select(','.join(cols) if cols else '*')
        .execute()
    )
    res_df = pd.DataFrame(res.data)
    if res_df.empty:
        res_df = pd.DataFrame(columns=cols if cols else get_tab_cols(table))
    return res_df


def select_count(table: str) -> int:
    res = supabase.table(table).select("*", count="exact").execute()
    return res.count


def select_distinct(table: str, cols: list) -> pd.DataFrame:
    response = (
        supabase.table(table)
        .select(','.join(cols))
        .execute()
    )
    db_df = pd.DataFrame(response.data)
    db_df = db_df.drop_duplicates()
    if db_df.empty:
        db_df = pd.DataFrame(columns=cols)
    return db_df


def select_where(table: str, col_value: dict, cols=None) -> pd.DataFrame:
    query = supabase.table(table).select(','.join(cols) if cols else '*')
    for k, v in col_value.items():
        query = query.eq(k, v)
    res = query.execute()
    res_df = pd.DataFrame(res.data)
    if res_df.empty:
        res_df = pd.DataFrame(columns=cols if cols else get_tab_cols(table))
    return res_df


def get_tab_cols(table: str) -> list:
    res = supabase.rpc("get_columns", {"tablename": table}).execute()
    return [r["column_name"] for r in res.data]


def insert(table: str, data: pd.DataFrame) -> bool:
    data = data.copy()
    for col in data.select_dtypes(include=["datetime64[ns]", "datetime64[ns, UTC]"]).columns:
        data[col] = data[col].astype(str)
    data = data.to_dict(orient="records")
    res = supabase.table(table).insert(data).execute()
    if res.data:
        return True
    return False


def update(table: str, key_col: str, values_to_update: dict) -> bool:
    successful = []
    for row_id, updates in values_to_update.items():
        res = (
            supabase.table(table)
            .update(updates)
            .eq(key_col, row_id)
            .execute()
        )
        if res.data:
            successful.append(True)
    if False not in successful:
        return True
    return False


def update_where(table: str, cols_update, col_search_value: dict) -> bool:
    query = supabase.table(table).update(cols_update)
    for k, v in col_search_value.items():
        query = query.eq(k, v)
    res = query.execute()
    if res:
        return True
    return False


def delete(table: str) -> bool:
    res = supabase.table(table).delete().execute()
    if res:
        return True
    return False


def delete_where(table: str, col_value: dict) -> bool:
    query = supabase.table(table).delete()
    for k, v in col_value.items():
        query = query.eq(k, v)
    res = query.execute()
    if res:
        return True
    return False


def delete_where_in(table: str, col: str, values: list) -> bool:
    query = supabase.table(table).delete()
    for v in values:
        query = query.eq(col, v)
    res = query.execute()
    if res:
        return True
    return False


def delete_where_data_df(table: str, df_col_value: pd.DataFrame) -> bool:
    if not df_col_value.empty:
        data = df_col_value.to_dict(orient="records")
        condition = ",".join([
            f"and({df_col_value.columns[0]}.eq.{jahr_kw['jahr']},{df_col_value.columns[1]}.eq.{jahr_kw['kalenderwoche']})"
            for jahr_kw in data
        ])
        res = (
            supabase.table(table)
            .delete()
            .or_(condition)
            .execute()
        )
        if res:
            return True
        return False


def delete_greater(table: str, col_value: dict) -> bool:
    query = supabase.table(table).delete()
    for k, v in col_value.items():
        query = query.gt(k, v)
    res = query.execute()
    if res:
        return True
    return False


def speichern_in_db(data: pd.DataFrame, table: str) -> (bool, str):
    if not data.empty:
        if data[data.columns].isna().any().any():
            return False, 'Mindestens ein Wert ist None. Bitte überprüfen'
        if data.shape[0] > 1:
            for col in data.columns:
                if not data.loc[data.duplicated(subset=[col])].empty:
                    return False, f'Doppelter Wert in Spalte: {col}. Bitte überprüfen'

    else:
        return False, 'Keine Daten eingefügt'

