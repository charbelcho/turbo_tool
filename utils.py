import datetime as dt
import re

import duckdb
import pandas as pd


def get_jahre(shift=1) -> tuple | None:
    this_year = dt.date.today().year
    if shift != 0:
        return tuple([this_year - 1] + [this_year - 1 + y for y in range(1, shift)])


def get_current_jahr() -> int:
    return dt.date.today().isocalendar().year


def get_max_kw(jahr: int) -> int:
    return dt.date(jahr, 12, 28).isocalendar()[1]


def get_kalenderwochen_pro_jahr(anzahl_jahre: int) -> pd.DataFrame:
    jahre = []
    for jahr in range(anzahl_jahre):
        jahre.append(dt.date.today().isocalendar().year - 1 + jahr)

    jahr_kw_df = pd.DataFrame({"jahr": jahre})
    jahr_kw_df["max_kw"] = jahr_kw_df["jahr"].apply(get_max_kw)
    return jahr_kw_df


def get_kalenderwochen(max_kw: int) -> tuple:
    return tuple([a for a in range(1, max_kw + 1)])


def get_current_kalenderwoche() -> int:
    return dt.date.today().isocalendar().week


def get_kalenderwoche_db():
    jahr = dt.date.today().year
    with duckdb.connect("file.db") as con:
        max_kw_per_jahr_df = con.sql("SELECT max(kalenderwoche) as max_kw, jahr FROM out_prices group by jahr").df()
        if not max_kw_per_jahr_df.empty:
            kw_df = max_kw_per_jahr_df.loc[max_kw_per_jahr_df['jahr'] == jahr]
            if not kw_df.empty:
                return kw_df.iloc[0]['max_kw']
        return get_current_kalenderwoche()


def split_tags(look_for_string: str, string: str) -> str:
    result = ''
    match = re.match(f'({look_for_string}:\d*,?\d*)', string)
    if match:
        result = match.group(0).split(':')[1]
    return result


def format_int_to_price_format(data: pd.DataFrame, cols: list) -> pd.DataFrame:
    for col in cols:
        if data.dtypes[col] in ('int64', 'float64'):
            data[col] = data[col].apply(lambda x: "{:.2f}".format(x))
        data.loc[:, col] = data.loc[:, col].astype(str).str.replace(".", ",")
    return data


def add_euro_char(data: pd.DataFrame, cols: list) -> pd.DataFrame:
    for col in cols:
        data.loc[~((data[col].isna()) | (data[col] == '')), col] = data[col] + ' €'
    return data


# Styling-Funktion
def einfaerben(val, ref) -> str:
    try:
        if ref != 0:
            diff = abs((val - ref) / ref)
            if diff > 0.03:
                return "background-color: #FF9999"  # rot
    except Exception as ex:
        pass
    return ""


# Wrapper für Styler
def style_werte(df: pd.DataFrame, compare_cols: list) -> list:
    styles = []
    for v, r in zip(df[compare_cols[0]], df[compare_cols[1]]):
        match_v = re.match(f'(\d*,?\d*)', v)
        match_r = re.match(f'(\d*,?\d*)', r)
        if match_v:
            v = pd.to_numeric(match_v.group(0).replace(',', '.'))
        if match_r:
            r = pd.to_numeric(match_r.group(0).replace(',', '.'))
        styles.append(einfaerben(v, r))
    return styles
