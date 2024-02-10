import streamlit as st
import json
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import folium
from streamlit_folium import folium_static


SP_CREDENTIAL_FILE = 'gspread-test-step3-267b4903a38a.json'
SP_COPE = [
    'https://www.googleapis.com/auth/drive',
    'https://spreadsheets.google.com/feeds'
]
SP_SHEET_KEY = '1wGA5uWtGNVHVvYn1mRG5GKzyrR-tVEiJ1sf57XDm8SU'
SP_SHEET = 'Sheet1'

credentials = ServiceAccountCredentials.from_json_keyfile_name(SP_CREDENTIAL_FILE, SP_COPE)
gc = gspread.authorize(credentials)
sh = gc.open_by_key(SP_SHEET_KEY)
worksheet = sh.worksheet(SP_SHEET)
data = worksheet.get_all_values()
df = pd.DataFrame(data[1:], columns=data[0])

# '家賃[万円]'列のデータ型をfloat, int64に変換
df['家賃[万円]'] = df['家賃[万円]'].astype('float64')
df['管理費[万円]'] = df['管理費[万円]'].astype('float64')
df['敷金[万円]'] = df['敷金[万円]'].astype('float64')
df['礼金[万円]'] = df['礼金[万円]'].astype('float64')
df['専有面積[m2]'] = df['専有面積[m2]'].astype('float64')
df['徒歩1[分]'] = df['徒歩1[分]'].astype('int64')
df['徒歩2[分]'] = df['徒歩2[分]'].astype('int64')
df['徒歩3[分]'] = df['徒歩3[分]'].astype('int64')
df['緯度'] = df['緯度'].astype('float64')
df['経度'] = df['経度'].astype('float64')

st.title('都心のお部屋探しサイトRocky’s')


# 検索条件の入力
selected_wards = st.multiselect('検索する地域を選んでください', ['中央区', '千代田区', '港区', '渋谷区', '目黒区', '文京区', '新宿区'])
rent_range = st.slider('家賃の範囲を選択（万円）', min_value=0, max_value=25, value=(8, 15))

selected_lines = st.multiselect('使用したい路線を選んでください（optional）', ['ＪＲ中央線', 'ＪＲ山手線', 'ＪＲ総武線', 'ＪＲ京葉線', 'ＪＲ京浜東北線', 'ＪＲ総武線快速', '京急本線', '京王井の頭線', '京王新線京王新線', '京王線', '小田急線', '新交通ゆりかもめ', '東京メトロ丸ノ内線', '東京メトロ副都心線', '東京メトロ千代田線', '東京メトロ半蔵門線', '東京メトロ南北線', '東京メトロ日比谷線', '東京メトロ南北線', '東京メトロ有楽町線', '東京メトロ東西線', '東京メトロ銀座線', '東急大井町線', '東急東横線', '東急田園都市線', '東急目黒線', '西武新宿線', '都営三田線', '都営大江戸線', '都営新宿線', '都営浅草線', '都電荒川線'])

selected_madori = st.multiselect('間取りを選んでください（optional）', ['2K', '2DK', '2LDK', '2SK', '2SLDK', '3K', '3LDK'])
foot_upper_limit = st.slider('最寄駅まで徒歩⚪︎分以内', min_value=1, max_value=10)

# 検索ボタン
if st.button('上記条件で検索する'):
    # 選択した区の条件に合致する行を抽出
    selected_rows = df[df['区'].isin(selected_wards) & 
                   (df['間取り'].isin(selected_madori) if selected_madori else True) &
                   ((df[['路線1', '路線2', '路線3']].isin(selected_lines).any(axis=1)) if selected_lines else True) &
                   (df['家賃[万円]'] >= rent_range[0]) & 
                   (df['家賃[万円]'] <= rent_range[1]) &
                   ((df['徒歩1[分]'] > 0) & (df['徒歩1[分]'] <= foot_upper_limit) |
                    (df['徒歩2[分]'] > 0) & (df['徒歩2[分]'] <= foot_upper_limit) |
                    (df['徒歩3[分]'] > 0) & (df['徒歩3[分]'] <= foot_upper_limit))]

    # selected_rowsが空でないか確認
    if not selected_rows.empty:
        # 件数を表示
        st.write(f'{len(selected_rows)} 件該当しました！')
        
        # 初期位置を指定
        initial_location = [selected_rows.iloc[0]['緯度'], selected_rows.iloc[0]['経度']]
        
        # マップの初期化
        folium_map = folium.Map(location=initial_location, zoom_start=12)

        # selected_rowsの各行に対してマーカーをプロット
        for i, r in selected_rows.iterrows():
            location = [r['緯度'], r['経度']]
            popup_html = f"<b>{r['物件名']}</b><br><a href='{r['リンク']}' target='_blank'>詳細を見る</a>"
            popup = folium.Popup(popup_html, min_width=100, max_width=300)
            folium.Marker(location=location, popup=popup).add_to(folium_map)

        # マップを表示
        folium_static(folium_map)

        # 表示する列を指定
        visible_columns = ['物件名', '住所', '築年数', '階', '家賃[万円]', '間取り', '専有面積[m2]', 'アクセス', 'リンク']

        # 表示するデータフレーム
        df_to_show = selected_rows[visible_columns]

        # 表示前にPandasの表示オプションを設定
        pd.set_option('display.max_colwidth', 50)  # カラム内の文字列の最大幅

        # 結果を表示
        st.write(df_to_show)
    else:
        st.write("選択された範囲に該当するデータがありません。")