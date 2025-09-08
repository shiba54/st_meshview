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
    st.markdown('メッシュビュー')
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
            st.markdown(':memo: メッシュの条件を入力してください')
            with st.container(border=True):
                st.session_state['cnt_i'] = st.number_input(
                    label='I 方向の格子点数',
                    min_value=2,
                    step=1,
                    key='_cnt_i'
                )
            with st.container(border=True):
                st.session_state['cnt_j'] = st.number_input(
                    label='J 方向の格子点数',
                    min_value=2,
                    step=1,
                    key='_cnt_j'
                )
            with st.container(border=True):
                st.session_state['ij_start'] = st.radio(
                    label='I J の開始番号',
                    options=[0, 1],
                    format_func=lambda x: f'{x} 始まり',
                    key='_ij_start'
                )
            with st.container(border=True):
                st.session_state['col_v'] = st.text_input(
                    label='メッシュの属性名',
                    value='Z',
                    key='_col_v'
                )
            with st.container(border=True):
                if 'epsg' not in st.session_state:
                    st.session_state['epsg'] = None

                st.text_input(
                    label='座標系の EPSG コード（=WKID）',
                    value=st.session_state['epsg'],
                    key='_epsg',
                    on_change=callback_set_epsg
                )

                if st.session_state['epsg'] is not None:
                    is_valid_epsg = view.caption_crs_name(
                        epsg=st.session_state['epsg']
                    )
                    if not is_valid_epsg:
                        st.session_state['epsg'] = None
                else:
                    st.caption('座標系の指定なし（マップは表示されません）')

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

        col1, col2 = st.columns(spec=[0.25, 0.75], border=True)
        with col1:
            view.show_params(
                cnt_i=cnt_i,
                cnt_j=cnt_j,
                ij_start=ij_start,
                col_v=col_v,
                epsg=epsg
            )
        with col2:
            st.markdown(':memo: 格子点の XY 座標とメッシュの属性値を指定してください')

            tab_manual, tab_upload = st.tabs(tabs=['値入力で指定', 'ファイルで指定'])

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

                st.markdown(f"""
                :small[
                    格子点の X座標 と Y座標、
                    メッシュの :gray-background[{col_v}] を入力 （コピペできます）
                ]
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
                with st.container(border=True):
                    delimit = st.text_input(
                        label='区切り文字',
                        value=',',
                        max_chars=1
                    )
                with st.container(border=True):
                    num_header = st.number_input(
                        label='ヘッダ行数',
                        min_value=0,
                        value=1,
                        step=1
                    )

                with st.container(border=True):
                    st.markdown(':small[列番号]')
                    col1, col2, col3, col4, col5 = st.columns(
                        spec=5,
                        vertical_alignment='bottom'
                    )
                    with col1:
                        ncol_i = st.number_input(
                            label='I番号',
                            min_value=1,
                            value=1,
                            step=1
                        )
                    with col2:
                        ncol_j = st.number_input(
                            label='J番号',
                            min_value=1,
                            value=2,
                            step=1
                        )
                    with col3:
                        ncol_x = st.number_input(
                            label='X座標（格子点）',
                            min_value=1,
                            value=3,
                            step=1
                        )
                    with col4:
                        ncol_y = st.number_input(
                            label='Y座標（格子点）',
                            min_value=1,
                            value=4,
                            step=1
                        )
                    with col5:
                        ncol_v = st.number_input(
                            label=f':gray-background[{col_v}]（メッシュ）',
                            min_value=1,
                            value=5,
                            step=1
                        )

                with st.container(border=True):
                    uploaded_file = st.file_uploader(
                        label='ファイル',
                        accept_multiple_files=False
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

                        st.markdown(':small[読込結果]')
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

        col1, col2 = st.columns(spec=[0.25, 0.75], border=True)
        with col1:
            view.show_params(
                cnt_i=cnt_i,
                cnt_j=cnt_j,
                ij_start=ij_start,
                col_v=col_v,
                epsg=epsg
            )
        with col2:
            st.markdown(':memo: メッシュの表示設定')

            with st.container(border=True):
                dummy_v = st.number_input(
                    label=f':gray-background[{col_v}] ダミー値',
                    value=None,
                    format='%0.3f'
                )
            with st.container(border=True):
                st.markdown(f':small[:gray-background[{col_v}] 表示レンジ]')
                range_auto = st.toggle(
                    label='自動',
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
                        label='最大値',
                        value=df_v[col_v].max(),
                        format='%0.3f',
                        disabled=range_auto
                    )
                    min_v = st.number_input(
                        label='最小値',
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

            with st.container(border=True):
                if epsg is not None:
                    mesh_opacity = 1.0 - st.slider(
                        label='透過率',
                        min_value=0.0,
                        max_value=1.0,
                        value=0.3,
                        step=0.1,
                        format='%0.1f',
                        key='_mesh_opacity'
                    )
                else:
                    pass

            with st.container(border=True):
                if epsg is not None:
                    col1, col2 = st.columns(spec=2, vertical_alignment='bottom')
                    with col1:
                        color = st.selectbox(
                            label='カラースケール',
                            options=model.COLORS_PLOTLY,
                            index=model.COLORS_PLOTLY.index('Viridis')
                        )
                    with col2:
                        reverse = st.toggle(label='反転')
                    view.link_color_scales()
                else:
                    col1, col2 = st.columns(spec=2, vertical_alignment='bottom')
                    with col1:
                        color = st.selectbox(
                            label='カラースケール',
                            options=model.COLORS_MATPLOTLIB,
                            index=model.COLORS_MATPLOTLIB.index('viridis')
                        )
                    with col2:
                        reverse = st.toggle(label='反転')
                    view.link_colormaps()

                color = f'{color}_r' if reverse else color

        if epsg is not None:
            with st.container(border=True):
                st.markdown(':memo: ベースマップの表示設定')

                with st.container(border=True):
                    tile = st.selectbox(
                        label='種類',
                        options=model.TILES,
                        format_func=lambda tile: tile.name
                    )

                with st.container(border=True):
                    tile_opacity = 1.0 - st.slider(
                        label='透過率',
                        min_value=0.0,
                        max_value=1.0,
                        value=0.3,
                        step=0.1,
                        format='%0.1f',
                        key='_tile_opacity'
                    )
                with st.container(border=True):
                    zoom_level = st.slider(
                        label='ズームレベル',
                        min_value=0,
                        max_value=20,
                        value=12,
                        step=1
                    )

        meshs = model.Meshs(
            df=st.session_state['df_pt'],
            col_v=st.session_state['col_v'],
            epsg=st.session_state['epsg']
        )

        with st.container(border=True):
            st.markdown(':sparkles: メッシュ表示')
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
                    st.markdown(':small[HTML データ]')
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
                    col1, col2 = st.columns(spec=2, vertical_alignment='bottom')
                    with col1:
                        ext = st.selectbox(
                            label='画像データ',
                            options=model.EXT_PLOT
                        )
                    with col2:
                        with st.spinner():
                            st.download_button(
                                label='Download',
                                data=meshs.zip_plot(fig, ext),
                                file_name='plot.zip',
                                mime='application/zip'
                            )

        with st.container(border=True):
            st.markdown(':sparkles: ダウンロード')

            @st.fragment
            def download_gis():
                col1, col2 = st.columns(spec=2, vertical_alignment='bottom')
                with col1:
                    driver = st.selectbox(
                        label='GIS データ',
                        options=model.DRIVER2EXT.keys()
                    )
                    ext = model.DRIVER2EXT[driver]
                with col2:
                    with st.spinner():
                        st.download_button(
                            label='Download',
                            data=meshs.zip_gis(driver, ext),
                            file_name='mesh.zip',
                            mime='application/zip'
                        )

            with st.container(border=True):
                download_gis()

            with st.container(border=True):
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
