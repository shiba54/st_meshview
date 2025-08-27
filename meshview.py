import pandas as pd
import streamlit as st

from pkg import model
from pkg import view


def callback_apply_edited_rows(
        key_data_editor: str,
        key_target: str
    ) -> None:
    """
    Apply edited rows to target dataframe

    Parameters
    --------
    key_data_editor : str
        specified key at st.data_editor
    key_target : str
        key in st.session_state
        st.session_state[key_target] must be dataframe
    """
    dict_edited_rows = st.session_state[key_data_editor]['edited_rows']
    for idx, dict_edited_row in dict_edited_rows.items():
            for col, val in dict_edited_row.items():
                st.session_state[key_target].loc[idx, col] = val


def callback_set_step_df(
        step: int,
        key: str | None = None
    ) -> None:
    """
    Switch step on this app and determine st.session_state['df_pt']

    Parameters
    --------
    step : int
        step number to set st.session_state['step']
    key : str | None
        key in st.ssesion_state
        st.session_state[key] will be assigned to st.session_state['df_pt']
    """
    st.session_state['step'] = step
    if key is not None:
        st.session_state['df_pt'] = st.session_state[key]
        del st.session_state[key]


def callback_set_epsg() -> None:
    """
    Set EPSG code to st.session_state
    """
    epsg = st.session_state['_epsg']
    if epsg is None:
        st.session_state['epsg'] = None
        return

    try:
        st.session_state['epsg'] = int(epsg)
    except ValueError:
        st.session_state['epsg'] = None


def main():
    st.set_page_config(
        page_title='MeshView',
        page_icon='☕',
        layout='wide'
    )
    st.title('MeshView')
    st.write('メッシュビュー')
    st.caption('格子点の座標を指定し、メッシュの属性値に応じて色付けします')

    if 'step' not in st.session_state:
        st.session_state['step'] = 1

    if 'cnt_i' in st.session_state and 'cnt_j' in st.session_state:
        view.warning_mesh_count(
            cnt_i=st.session_state['cnt_i'],
            cnt_j=st.session_state['cnt_j']
        )

    if st.session_state['step'] == 1:
        with st.container(border=True):
            st.write(':memo: メッシュの条件を入力してください')
            col1, col2, col3, col4 = st.columns([0.25, 0.2, 0.2, 0.35])
            with col1:
                st.write(':material/Check: I 方向の格子点数')
                st.session_state['cnt_i'] = st.number_input(
                    label='_',
                    min_value=2,
                    step=1,
                    key='_cnt_i',
                    label_visibility='collapsed'
                )
                st.write(':material/Check: J 方向の格子点数')
                st.session_state['cnt_j'] = st.number_input(
                    label='_',
                    min_value=2,
                    step=1,
                    key='_cnt_j',
                    label_visibility='collapsed'
                )
            with col2:
                st.write(':material/Check: IJ の開始番号')
                st.session_state['ij_start'] = st.radio(
                    label='_',
                    options=[0, 1],
                    format_func=lambda x: f'{x} 始まり',
                    key='_ij_start',
                    label_visibility='collapsed'
                )
            with col3:
                st.write(':material/Check: メッシュの属性名')
                st.session_state['col_v'] = st.text_input(
                    label='_',
                    value='Z',
                    key='_col_v',
                    label_visibility='collapsed'
                )
            with col4:
                st.write(':material/Check: 座標系の EPSG コード（=WKID）')
                st.caption(body='英数字で入力してください（マップを表示しない場合は不要）')
                if 'epsg' not in st.session_state:
                    st.session_state['epsg'] = None

                st.text_input(
                    label='_',
                    value=st.session_state['epsg'],
                    key='_epsg',
                    on_change=callback_set_epsg,
                    label_visibility='collapsed'
                )
                if st.session_state['epsg'] is not None:
                    is_valid_epsg = view.caption_crs_name(st.session_state['epsg'])
                    if not is_valid_epsg:
                        st.session_state['epsg'] = None

                view.link_wkid()

        if st.button(
            label='確定',
            key='confirm1',
            on_click=callback_set_step_df,
            args=(2,)
        ):
            st.rerun()

    if st.session_state['step'] == 2:
        cnt_i = st.session_state['cnt_i']
        cnt_j = st.session_state['cnt_j']
        ij_start = st.session_state['ij_start']
        col_v = st.session_state['col_v']
        epsg = st.session_state['epsg']

        max_i = cnt_i + ij_start - 1
        max_j = cnt_j + ij_start - 1

        col1, col2 = st.columns([0.25, 0.75], border=True)
        with col1:
            view.show_params(cnt_i, cnt_j, ij_start, col_v, epsg)
        with col2:
            st.write(':memo: 格子点の XY 座標とメッシュの属性値を指定してください')

            tab_manual, tab_upload = st.tabs(['値入力で指定', 'ファイルで指定'])

            with tab_manual:
                if 'df_manual' not in st.session_state:
                    num_rows = cnt_i * cnt_j
                    data = {
                        'I': sorted([i + ij_start for i in range(cnt_i)] * cnt_j),
                        'J': [j + ij_start for j in range(cnt_j)] * cnt_i,
                        'X': [0.0 for _ in range(num_rows)],
                        'Y': [0.0 for _ in range(num_rows)],
                        col_v: [0.0 for _ in range(num_rows)]
                    }
                    df = pd.DataFrame(data)
                    st.session_state['df_manual'] = df

                column_config = {
                    'I': st.column_config.NumberColumn(
                        label='I番号',
                        disabled=True
                    ),
                    'J': st.column_config.NumberColumn(
                        label='J番号',
                        disabled=True
                    ),
                    'X': st.column_config.NumberColumn(
                        label='X座標',
                        disabled=False,
                        default=0.0,
                        format='localized'
                    ),
                    'Y': st.column_config.NumberColumn(
                        label='Y座標',
                        disabled=False,
                        default=0.0,
                        format='localized'
                    ),
                    col_v: st.column_config.NumberColumn(
                        label=f'{col_v}',
                        disabled=False,
                        default=0.0,
                        format='localized'
                    )
                }

                st.write(f"""
                    :material/Check: X座標（格子点）、Y座標（格子点）、:gray-background[{col_v}]（メッシュ）を入力  
                    （コピペできます）
                """)
                st.data_editor(
                    data=st.session_state['df_manual'],
                    hide_index=True,
                    column_config=column_config,
                    num_rows='fixed',
                    key='edited_df_manual',
                    on_change=callback_apply_edited_rows,
                    args=('edited_df_manual', 'df_manual')
                )

                if st.button(
                    label='確定',
                    key='confirm2_manual',
                    on_click=callback_set_step_df,
                    args=(3, 'df_manual')
                ):
                    st.rerun()

            with tab_upload:
                col1, col2 = st.columns(2)
                with col1:
                    st.write(':material/Check: 区切り文字')
                    delimit = st.text_input(
                        label='_',
                        value=',',
                        max_chars=1,
                        label_visibility='collapsed'
                    )
                with col2:
                    st.write(':material/Check: ヘッダ行数')
                    num_header = st.number_input(
                        '_',
                        min_value=0,
                        value=1,
                        step=1,
                        label_visibility='collapsed'
                    )

                st.write(':material/Check: 列番号')
                col1, col2, col3, col4, col5 = st.columns(5, vertical_alignment='bottom')
                with col1:
                    ncol_i = st.number_input(
                        'I番号',
                        min_value=1,
                        value=1,
                        step=1
                    )
                with col2:
                    ncol_j = st.number_input(
                        'J番号',
                        min_value=1,
                        value=2,
                        step=1
                    )
                with col3:
                    ncol_x = st.number_input(
                        'X座標（格子点）',
                        min_value=1,
                        value=3,
                        step=1
                    )
                with col4:
                    ncol_y = st.number_input(
                        'Y座標（格子点）',
                        min_value=1,
                        value=4,
                        step=1
                    )
                with col5:
                    ncol_v = st.number_input(
                        f':gray-background[{col_v}]（メッシュ）',
                        min_value=1,
                        value=5,
                        step=1
                    )

                st.write(':material/Check: ファイル')
                uploaded_file = st.file_uploader(
                    '_',
                    accept_multiple_files=False,
                    label_visibility='collapsed'
                )
                is_correct_ij = False
                if uploaded_file is not None:
                    try:
                        df_upload = pd.read_csv(
                            uploaded_file,
                            sep=delimit,
                            header=num_header - 1 if num_header > 0 else None,
                            names=['I', 'J', 'X', 'Y', col_v],
                            usecols=[ncol_i-1, ncol_j-1, ncol_x-1, ncol_y-1, ncol_v-1],
                            dtype={
                                'I': int,
                                'J': int,
                                'X': float,
                                'Y': float,
                                col_v: float
                            },
                            skipinitialspace=True
                        )

                        st.write(':material/Check: 読込結果')
                        try:
                            is_correct_ij = all((
                                    st.session_state['df_manual'][['I', 'J']] \
                                        == df_upload[['I', 'J']].sort_values(['I', 'J'])
                                ).all())
                        except ValueError:
                            is_correct_ij = False

                        if is_correct_ij:
                            st.dataframe(
                                data=df_upload,
                                hide_index=True
                            )
                            st.session_state['df_upload'] = df_upload


                        else:
                            if not len(df_upload) == cnt_i * cnt_j:
                                st.error('行数が正しくありません')
                            else:
                                st.error('IJ が正しくありません')

                    except pd.errors.ParserError:
                        st.error('データを読み込めません')
                    except ValueError:
                        st.error('データを読み込めません')

                if st.button(
                    label='確定',
                    key='confirm2_upload',
                    on_click=callback_set_step_df,
                    args=(3, 'df_upload'),
                    disabled=False if is_correct_ij else True
                ):
                    st.rerun()

            st.caption(f'I = {max_i}, J = {max_j} のメッシュ属性値は無視されます')

    if st.session_state['step'] == 3:
        cnt_i = st.session_state['cnt_i']
        cnt_j = st.session_state['cnt_j']
        ij_start = st.session_state['ij_start']
        col_v = st.session_state['col_v']
        epsg = st.session_state['epsg']

        max_i = cnt_i + ij_start - 1
        max_j = cnt_j + ij_start - 1

        col1, col2 = st.columns([0.25, 0.75], border=True)
        with col1:
            view.show_params(cnt_i, cnt_j, ij_start, col_v, epsg)
        with col2:
            st.write(':memo: メッシュの表示設定')

            col21, col22, col23 = st.columns(3)
            with col22:
                st.write(f':material/Check: :gray-background[{col_v}] ダミー値')
                dummy_v = st.number_input(
                    '_',
                    value=None,
                    format='%0.3f',
                    placeholder='指定なし',
                    label_visibility='collapsed'
                )
                if epsg is not None:
                    st.write(':material/Check: 透過率')
                    mesh_opacity = 1.0 - st.slider(
                        '_',
                        min_value=0.0,
                        max_value=1.0,
                        value=0.3,
                        step=0.1,
                        format='%0.1f',
                        key='_mesh_opacity',
                        label_visibility='collapsed'
                    )
                else:
                    pass

            with col21:
                st.write(f':material/Check: :gray-background[{col_v}] 表示レンジ')
                range_auto = st.toggle(
                    '自動',
                    value=True
                )

                df_v = st.session_state['df_pt']
                df_v = df_v.loc[(df_v['I'] != max_i) & (df_v['J'] != max_j), [col_v]]
                df_v = df_v.loc[df_v[col_v] != dummy_v] if dummy_v else df_v

                if range_auto:
                    max_v = df_v[col_v].max()
                    min_v = df_v[col_v].min()
                else:
                    max_v = st.number_input(
                        '最大値',
                        value=df_v[col_v].max(),
                        format='%0.3f',
                        disabled=range_auto
                    )
                    min_v = st.number_input(
                        '最小値',
                        value=df_v[col_v].min(),
                        format='%0.3f',
                        disabled=range_auto
                    )

                if (min_v < max_v):
                    range_v = [min_v, max_v]
                else:
                    st.warning('レンジ設定が正しくありません')
                    range_v = None
                    range_auto = True

            with col23:
                st.write(':material/Check: カラースケール')
                if epsg is not None:
                    color = st.selectbox(
                        '_',
                        options=model.COLORS_PLOTLY,
                        index=model.COLORS_PLOTLY.index('Viridis'),
                        label_visibility='collapsed'
                    )
                    reverse = st.toggle('反転')
                    view.link_color_scales()
                else:
                    color = st.selectbox(
                        '_',
                        options=model.COLORS_MATPLOTLIB,
                        index=model.COLORS_MATPLOTLIB.index('viridis'),
                        label_visibility='collapsed'
                    )
                    reverse = st.toggle('反転')
                    view.link_colormaps()

                color = f'{color}_r' if reverse else color

        if epsg is not None:
            with st.container(border=True):
                st.write(':memo: ベースマップの表示設定')
                col21, col22, col23 = st.columns(3)
                with col21:
                    st.write(':material/Check: 種類')
                    tile = st.selectbox(
                        '_',
                        options=model.TILES,
                        format_func=lambda tile: tile.name,
                        label_visibility='collapsed'
                    )
                with col22:
                    st.write(':material/Check: 透過率')
                    tile_opacity = 1.0 - st.slider(
                        '_',
                        min_value=0.0,
                        max_value=1.0,
                        value=0.3,
                        step=0.1,
                        format='%0.1f',
                        key='_tile_opacity',
                        label_visibility='collapsed'
                    )
                with col23:
                    st.write(':material/Check: ズームレベル')
                    zoom_level = st.slider(
                        '_',
                        min_value=0,
                        max_value=20,
                        value=12,
                        step=1,
                        label_visibility='collapsed'
                    )

        meshs = model.Meshs(
            df=st.session_state['df_pt'],
            col_v=st.session_state['col_v'],
            epsg=st.session_state['epsg']
        )

        with st.container(border=True):
            st.write(':sparkles: メッシュ表示')
            if epsg is not None:
                # Plotly plot
                fig = meshs.choropleth_map(
                    dummy_v=dummy_v,
                    range_v=range_v,
                    colorscale=color,
                    mesh_opacity=mesh_opacity,
                    zoom_level=zoom_level,
                    tile=tile,
                    tile_opacity=tile_opacity
                )
                st.plotly_chart(
                    fig,
                    config={'scrollZoom': True}
                )

                @st.fragment
                def download_map():
                    st.write(':material/Check: HTML データ')
                    with st.spinner():
                        st.download_button(
                            label='Download',
                            data=meshs.zip_map(fig),
                            file_name='map.zip',
                            mime='application/zip'
                        )

            else:
                # Matplotlib plot
                fig = meshs.plot(
                    dummy_v=dummy_v,
                    range_v=range_v,
                    cmap=color
                )
                st.pyplot(fig)

                @st.fragment
                def download_plot():
                    st.write(':material/Check: 画像データ')
                    ext = st.selectbox(
                        '_',
                        options=model.EXT_PLOT,
                        label_visibility='collapsed',
                        width=200
                    )
                    with st.spinner():
                        st.download_button(
                            label='Download',
                            data=meshs.zip_plot(fig, ext),
                            file_name='plot.zip',
                            mime='application/zip'
                        )

        with st.container(border=True):
            st.write(':sparkles: ダウンロード')

            @st.fragment
            def download_gis():
                st.write(':material/Check: GIS データ')
                driver = st.selectbox(
                    '_',
                    options=model.DRIVER2EXT.keys(),
                    label_visibility='collapsed',
                    width=200
                )
                ext = model.DRIVER2EXT[driver]
                with st.spinner():
                    st.download_button(
                        label='Download',
                        data=meshs.zip_gis(driver, ext),
                        file_name='mesh.zip',
                        mime='application/zip'
                    )

            col1, col2 = st.columns(2)
            with col1:
                download_gis()
            with col2:
                if epsg is not None:
                    download_map()
                else:
                    download_plot()

    st.markdown("""
    * ブラウザ更新でリセットできます
    * BFC 構造の2次元のメッシュを対象としています
    """)


if __name__ == '__main__':
    main()
