from pyproj import CRS
from pyproj import exceptions
import streamlit as st


def warning_mesh_count(cnt_i: int, cnt_j: int) -> None:
    """
    Warn user against large mesh

    Parameters
    --------
    cnt_i : int
        count of I based on point
    cnt_j : int
        count of J based on point
    """
    cnt_mesh_warning = 10_000
    if cnt_i * cnt_j > cnt_mesh_warning:
        st.warning('メッシュ数が多いため、処理に時間がかかる場合があります')


def link_wkid() -> None:
    st.markdown(
        '[:small[参考: 日本周辺座標系の WKID 一覧 ©<2025> WINGFIELD since1995]]' \
        '(https://www.wingfield.gr.jp/archives/5692)'
    )


def link_color_scales() -> None:
    st.markdown(
        '[:small[参考: Sequential Color scales]]' \
        '(https://plotly.com/python/builtin-colorscales/)'
    )


def link_colormaps() -> None:
    st.markdown(
        '[:small[参考: colormaps]]' \
        '(https://matplotlib.org/cheatsheets/_images/cheatsheets-2.png)'
    )


def caption_crs_name(epsg: int) -> bool:
    """
    Caption crs name

    Parameters
    --------
    epsg : int
        EPSG code
    
    Returns
    --------
    True if valid epsg else False
    """
    try:
        crs = CRS.from_epsg(epsg)
        st.caption(f"座標系の名称: :gray-background[{crs.name}]")
        return True
    except exceptions.CRSError:
        st.caption('座標系の名称: :gray-background[該当なし]')
        return False


def show_params(
    cnt_i: int,
    cnt_j: int,
    ij_start: int,
    col_v: str,
    epsg: int | None
) -> None:
    """
    Show mesh parameters

    Parameters
    --------
    cnt_i : int
        count of I based on point
    cnt_j : int
        count of J based on point
    ij_start : int
        start number of IJ
    col_v : str
        column name of mesh value
    epsg : int | None
        EPSG code
    """
    st.markdown(':material/Check: メッシュ条件')
    st.markdown(f""":small[
        I 方向の格子点数: :gray-background[{cnt_i}]  
        J 方向の格子点数: :gray-background[{cnt_j}]  
        IJ の開始番号: :gray-background[{ij_start}]  
        メッシュの属性名: :gray-background[{col_v}]  
        EPSG コード: :gray-background[{epsg}]]
    """)
    st.caption(f"""
        I 方向のメッシュ数: :gray-background[{cnt_i - 1}]  
        J 方向のメッシュ数: :gray-background[{cnt_j - 1}]
    """)
    if epsg is not None:
        caption_crs_name(epsg=epsg)
    else:
        st.caption('座標系: 指定なし')
