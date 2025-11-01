import base64
import io
from typing import Any

import pandas as pd
import datetime as dt

from pandas.io.formats.style import Styler

import db_functions
import utils

output_file: str = "bereinigt.csv"


def read_file_turbo(filecontent: Any, woche: int, jahr: int) -> None | Exception:
    if not woche:
        return Exception('Keine gültige Woche angegeben')
    if not jahr:
        return Exception('Kein gültiges Jahr angegeben')
    input_df = read_file(filecontent)
    input_df = rename_input_df(input_df)

    input_df['hochgeladen_am'] = dt.datetime.now()
    input_df['kalenderwoche'] = woche
    input_df['jahr'] = jahr

    if not input_df.empty:
        db_functions.insert('in_prices', data=input_df)


def daten_fuer_kw_anzeigen(woche: int, jahr: int, from_in_table=True) -> pd.DataFrame:
    jahr_kw_df = utils.get_kalenderwochen_pro_jahr(5)
    current_jahr_df = jahr_kw_df.loc[jahr_kw_df['jahr'] == jahr]
    if woche > current_jahr_df['max_kw'].iloc[0]:
        woche = current_jahr_df['max_kw'].iloc[0]
    if woche < 1:
        woche = jahr_kw_df.loc[jahr_kw_df['jahr'] == jahr - 1]['max_kw'].iloc[0]
    data_from_db = db_functions.select_where(
        table='in_prices' if from_in_table else 'out_prices',
        col_value={"kalenderwoche": woche, "jahr": jahr})

    return data_from_db


def transform_data_to_output(woche: int, jahr: int) -> None:
    data = daten_fuer_kw_anzeigen(woche, jahr)

    data_letzte_woche = daten_fuer_kw_anzeigen(woche - 1, jahr, from_in_table=False)

    output_df = transform_input(data)
    output_df['vprs'] = output_df['tags'].apply(lambda x: utils.split_tags('VPRS', x))
    output_df['ykbn'] = output_df['tags'].apply(lambda x: utils.split_tags('YKBN', x))

    output_df = pd.merge(
        left=output_df,
        right=data_letzte_woche[['artikelnummer', 'bester_wettbewerber_vk']],
        suffixes=('', '_letzte_woche'),
        how='left',
        on='artikelnummer')

    output_df = output_df.rename(columns={'bester_wettbewerber_vk_letzte_woche': 'preis_vorherige_kw'})

    output_df['prozessiert_am'] = dt.datetime.now()
    output_df = output_df.drop(columns=['tags', 'hochgeladen_am'])

    if not output_df.empty:
        db_functions.insert('out_prices', output_df)


def prepare_date_for_excel(woche: int, jahr: int) -> io.BytesIO:
    excel_data = daten_fuer_kw_anzeigen(woche, jahr, from_in_table=False)

    price_cols = ['meesenburg_vk', 'ynek', 'vprs', 'ykbn', 'bester_wettbewerber_vk', 'preis_vorherige_kw']

    excel_data['preis_vorherige_kw'] = excel_data['preis_vorherige_kw'].fillna('')
    excel_data = utils.format_int_to_price_format(excel_data, price_cols)
    excel_data = utils.add_euro_char(excel_data, price_cols)

    max_kw_last_year = utils.get_max_kw(jahr - 1)

    col_kw = f'KW {woche - 1 if woche - 1 > 1 else max_kw_last_year}'

    cols_map_out_df = db_functions.select(table='cols_map_out')
    cols_map_out_df = cols_map_out_df.sort_values(['spalte_position'])
    cols_map_out = dict(zip(cols_map_out_df["spalte_db"], cols_map_out_df["spalte_output_datei"]))
    cols_map_out['preis_vorherige_kw'] = col_kw

    excel_data = excel_data.rename(columns=cols_map_out)
    excel_data = excel_data[cols_map_out_df['spalte_output_datei'].to_list() + [col_kw]]

    styled = excel_data.style.apply(lambda _: utils.style_werte(excel_data, [col_kw, 'Bester Wettbewerber VK']),
                                    subset=[col_kw])

    excel_buffer = write_to_excel(excel_data, styled)
    return excel_buffer


def process(filecontent: Any, woche: int, jahr: int) -> str:
    read_file_turbo(filecontent, woche, jahr)
    transform_data_to_output(woche, jahr)
    excel_buffer = prepare_date_for_excel(woche, jahr)
    java_script = download_excel(excel_buffer, 'ergebnisse')
    return java_script


def transform_gedore(filecontent: Any) -> str:
    input_df = read_file(filecontent)
    input_df = rename_input_df(input_df)
    output_df = transform_input(input_df)

    price_cols = ['meesenburg_vk', 'ynek', 'bester_wettbewerber_vk']
    excel_data = get_excel_data(output_df, price_cols, ['VPRS', 'YKBN'])
    excel_buffer = write_to_excel(excel_data)
    js = download_excel(excel_buffer, 'gedore_ergebnisse')
    return js


def transform_google_shopping(filecontent: Any) -> str:
    input_df = read_file(filecontent)
    input_df = rename_input_df(input_df)
    output_df = transform_input(input_df)
    output_df['vprs'] = output_df['tags'].apply(lambda x: utils.split_tags('VPRS', x))
    output_df['ykbn'] = output_df['tags'].apply(lambda x: utils.split_tags('YKBN', x))

    price_cols = ['meesenburg_vk', 'ynek', 'vprs', 'ykbn', 'bester_wettbewerber_vk']
    excel_data = get_excel_data(output_df, price_cols)
    excel_buffer = write_to_excel(excel_data)
    js = download_excel(excel_buffer, 'google_shopping_ergebnisse')
    return js


def read_file(filecontent: Any) -> pd.DataFrame | Exception:
    if filecontent is not None:
        raw_data = filecontent.getvalue()

        byte_string = raw_data.replace(b'\x00', b'')
        text = byte_string.decode("utf-8", errors="replace")  # ersetzt nicht-unicode-Zeichen durch �

        # Ersetze alle � (Replacement Character) mit leerem String
        clean_text = text.replace('�', '').replace('"', '')

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(clean_text)

        input_df = pd.read_csv(output_file, encoding='utf-8', engine="python", sep="\t", encoding_errors='ignore',
                               skip_blank_lines=True)
        return input_df
    return Exception('Empty File!')


def rename_input_df(input_df: pd.DataFrame) -> pd.DataFrame:
    input_df = input_df[
        ['Brand', 'Product', 'Code', 'Your Price', 'Tags', 'Cost Price', 'Rival Best Price', 'Your Diff.']]

    cols_map_in_df = db_functions.select(table='cols_map_in')
    cols_map_in = dict(zip(cols_map_in_df["spalte_input_datei"], cols_map_in_df["spalte_db"]))
    input_df = input_df.rename(columns=cols_map_in)
    return input_df


def transform_input(input_df) -> pd.DataFrame | Exception:
    if not input_df.empty:
        input_df.loc[:, 'me_vk_bester_preis'] = ''
        input_df.loc[input_df['your_price'] < input_df['rival_best_price'], 'me_vk_bester_preis'] = 'ja'
        input_df.loc[input_df['your_price'] == input_df['rival_best_price'], 'me_vk_bester_preis'] = 'gleich'
        input_df.loc[input_df['your_price'] > input_df['rival_best_price'], 'me_vk_bester_preis'] = 'nein'

        output_df = input_df.rename(columns={'brand': 'lieferant', 'product': 'artikel', 'code': 'artikelnummer',
                                             'your_price': 'meesenburg_vk', 'cost_price': 'ynek',
                                             'rival_best_price': 'bester_wettbewerber_vk',
                                             'your_difference': 'vk_zum_besten_wettbewerber'})
        return output_df
    return Exception('Empty Input Dataframe!')


def get_excel_data(output_df: pd.DataFrame, price_cols: list = None, filter_cols_out: list = None) -> pd.DataFrame:
    if filter_cols_out is None:
        filter_cols_out = []
    excel_data = utils.format_int_to_price_format(output_df, price_cols)
    excel_data = utils.add_euro_char(excel_data, price_cols)

    cols_map_out_df = db_functions.select(table='cols_map_out')
    cols_map_out_df = cols_map_out_df.sort_values(['spalte_position'])
    if filter_cols_out:
        cols_map_out_df = cols_map_out_df.loc[~cols_map_out_df['spalte_output_datei'].isin(filter_cols_out)]
    cols_map_out = dict(zip(cols_map_out_df["spalte_db"], cols_map_out_df["spalte_output_datei"]))

    excel_data = excel_data.rename(columns=cols_map_out)
    excel_data = excel_data[cols_map_out_df['spalte_output_datei'].to_list()]
    return excel_data


def write_to_excel(excel_data: pd.DataFrame, styled: Styler = None) -> io.BytesIO:
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
        if styled:
            styled.to_excel(writer, index=False, sheet_name="Ergebnisse")
        else:
            excel_data.to_excel(writer, index=False, sheet_name="Ergebnisse")
        workbook = writer.book
        worksheet = writer.sheets["Ergebnisse"]

        # Spaltenbreite automatisch anpassen
        for i, col in enumerate(excel_data.columns):
            max_len = max(
                excel_data[col].astype(str).map(len).max(),
                len(col)
            ) + 2
            worksheet.set_column(i, i, max_len)

    excel_buffer.seek(0)
    return excel_buffer


def download_excel(excel_buffer: io.BytesIO, excel_name: str) -> str:
    b64 = base64.b64encode(excel_buffer.read()).decode()
    href = f'data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}'

    js = f"""
        <html>
        <body>
            <a id="download" href="{href}" download="{excel_name}.xlsx"></a>
            <script>
                document.getElementById('download').click();
            </script>
        </body>
        </html>
        """
    return js

