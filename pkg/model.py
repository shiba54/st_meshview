import dataclasses
import glob
from io import BytesIO
import os.path
import tempfile
import warnings
import zipfile

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib import colormaps
from mpl_toolkits.axes_grid1 import make_axes_locatable
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from _plotly_utils import colors
from shapely.geometry import Polygon


COLORS_PLOTLY = sorted(
    [s for s in dir(colors.sequential) if ('_' not in s) and (not s.startswith('swatches'))],
    key=str.lower
)
COLORS_MATPLOTLIB = sorted(
    [s for s in colormaps if not s.endswith('_r')],
    key=str.lower
)

DRIVER2EXT = {
    'ESRI Shapefile': 'shp',
    'GeoJSON': 'geojson',
    'GPKG': 'gpkg'
}
EXT_PLOT = ['png', 'pdf', 'svg']
EXT_MAP = ['png', 'svg', 'html']

plt.rcParams['font.size'] = 8
plt.rcParams['font.family'] = 'Meiryo'


@dataclasses.dataclass
class TILE:
    """
    Web tile service
    """
    name: str
    sourceattribution: str
    source: str


TILES = [
    TILE(
        name='オープンストリートマップ',
        sourceattribution='©OpenStreetMap contributors, CC BY-SA ',
        source='https://tile.openstreetmap.org/{z}/{x}/{y}.png',
    ),
    TILE(
        name='標準地図',
        sourceattribution='地理院タイル（標準地図）(https://maps.gsi.go.jp/development/ichiran.html)',
        source='https://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png',
    ),
    TILE(
        name='淡色地図',
        sourceattribution='地理院タイル（淡色地図） (https://maps.gsi.go.jp/development/ichiran.html)',
        source='https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png'
    ),
    TILE(
        name='写真',
        sourceattribution='地理院タイル（写真） (https://maps.gsi.go.jp/development/ichiran.html)',
        source='https://cyberjapandata.gsi.go.jp/xyz/seamlessphoto/{z}/{x}/{y}.jpg'
    )
]


class Meshs:
    """
    BFC Mesh class

    Parameters
    --------
    col_i : str
        column name of I number
    col_j : str
        column name of J number
    col_x : str
        column name of X coordinate
    col_y : str
        column name of Y coordinate
    col_v : str
        column name of mesh value
    epsg : int | None
        EPSG code
    gdf : gpd.GeoDataFrame
        mesh data without the end of I and J point
        columns are col_i, col_j, col_v, and 'geometry'
    """
    def __init__(
        self,
        df: pd.DataFrame,
        col_v: str,
        epsg: int | None,
        col_i = 'I',
        col_j = 'J',
        col_x = 'X',
        col_y = 'Y'
    ) -> None:
        self.col_i = col_i
        self.col_j = col_j
        self.col_x = col_x
        self.col_y = col_y
        self.col_v = col_v
        self.epsg = epsg
        self.gdf: gpd.GeoDataFrame
        self.set_gdf(df)

    def set_gdf(self, df: pd.DataFrame) -> None:
        """
        Set GeoDataFrame

        Parameters
        --------
        df : pd.DataFrame
            user input data including the end of I and J point
            columns are col_i, col_j, col_x, col_y, col_v
        """
        cnt_j = df[self.col_j].nunique()
        max_i = df[self.col_i].max()
        max_j = df[self.col_j].max()
        df = df.sort_values([self.col_i, self.col_j])
        df[['Xpt2', 'Ypt2']] = df.loc[:, [self.col_x, self.col_y]].shift(-1)
        df[['Xpt3', 'Ypt3']] = df.loc[:, [self.col_x, self.col_y]].shift(-cnt_j - 1)
        df[['Xpt4', 'Ypt4']] = df.loc[:, [self.col_x, self.col_y]].shift(-cnt_j)

        df = df.loc[(df[self.col_i] != max_i) & (df[self.col_j] != max_j), :]

        def getpolygon(row):
            x1, y1 = row[self.col_x], row[self.col_y]
            x2, y2 = row['Xpt2'], row['Ypt2']
            x3, y3 = row['Xpt3'], row['Ypt3']
            x4, y4 = row['Xpt4'], row['Ypt4']
            polygon = Polygon([(x1, y1), (x2, y2), (x3, y3), (x4, y4)])
            return polygon

        df['geometry'] = df.apply(getpolygon, axis=1)  # type: ignore

        df = df[[self.col_i, self.col_j, self.col_v, 'geometry']]
        gdf = gpd.GeoDataFrame(df, crs=self.epsg)
        self.gdf = gdf

    def choropleth_map(
        self,
        dummy_v: float | None,
        range_v: list[float] | None,
        colorscale: str,
        mesh_opacity: float,
        zoom_level: int,
        tile: TILE,
        tile_opacity: float
    ) -> go.Figure:
        """
        Choropleth map based on plotly
        Mesh must have epsg

        Parameters
        --------
        dummy_v : float | None
            if v is dummy_v, the mesh will be removed from fig
        range_v : list[float] | None
            range_color to be passed to px.choropleth_map
        colorscale : str
            color_continuous_scale to be passed to px.choropleth_map
        mesh_opacity : float
            opacity to be passed to px.choropleth_map
        zoom_level : int
            zoom to be passed to px.choropleth_map
        tile : TILE
            basemap
        tile_opacity : float
            tile opacity

        Returns
        --------
        go.Figure
        """
        col_ij = 'IJ'

        if dummy_v is not None:
            gdf = self.gdf.loc[self.gdf[self.col_v] != dummy_v].copy()
        else:
            gdf = self.gdf.copy()

        gdf[col_ij] = gdf.apply(
            lambda row: f"{row[self.col_i]}, {row[self.col_j]}",
            axis=1
        )
        gdf = gdf[[col_ij, self.col_v, 'geometry']].set_index(col_ij)

        gdf = gdf.to_crs(4326)  # WGS84
        minx, miny, maxx, maxy = gdf['geometry'].total_bounds

        fig = px.choropleth_map(
            data_frame=gdf,
            geojson=gdf.geometry,
            locations=gdf.index,
            color=self.col_v,
            color_continuous_scale=colorscale,
            range_color=range_v,
            hover_data=[self.col_v],
            opacity=mesh_opacity,
            zoom=zoom_level,
            center=dict(
                lat=(miny + maxy)/2,
                lon=(minx + maxx)/2
                ),
            height=720
        )

        map_layers = [
            {
                'below': 'traces',
                'sourcetype': 'raster',
                'sourceattribution': tile.sourceattribution,
                'source': [tile.source],
                'opacity': tile_opacity
            }
        ]

        fig.update_layout(
            map_style='white-bg',
            map_layers=map_layers
        )

        return fig

    def plot(
        self,
        dummy_v: float | None,
        range_v: list[float] | None,
        cmap: str
    ) -> Figure:
        """
        Choropleth map based on matplotlib
        EPSG is not necessary

        Parameters
        --------
        dummy_v : float | None
            if v is dummy_v, the mesh will be removed from fig
        range_v : list[float] | None
            [vmin, vmax] to be passed to plot
        cmap : str
            cmap to be passed to plot
        
        Returns
        --------
        Figure
        """
        if dummy_v is not None:
            gdf = self.gdf.loc[self.gdf[self.col_v] != dummy_v].copy()
        else:
            gdf = self.gdf.copy()

        fig, ax = plt.subplots(tight_layout=True)

        divider = make_axes_locatable(ax)
        cax = divider.append_axes(position='right', size='5%', pad='3%')

        ax.grid(linewidth=0.5)
        ax.set_axisbelow(True)

        gdf.plot(
            column=self.col_v,
            cmap=cmap,
            ax=ax,
            legend=True,
            legend_kwds={'label': self.col_v, 'cax': cax},
            vmin=range_v[0] if range_v is not None else None,
            vmax=range_v[1] if range_v is not None else None
        )

        return fig

    def zip_plot(
        self,
        fig: Figure,
        ext: str
    ) -> BytesIO:
        """
        Zip plot to image

        Parameters
        --------
        fig : Figure
            returned figure from plot()
        ext : str
            output file extension
        
        Returns
        --------
        BytesIO
        """
        in_memory = BytesIO()
        filename = 'plot'

        with tempfile.TemporaryDirectory() as tmpdir:
            with zipfile.ZipFile(
                file=in_memory,
                mode='w',
                compression=zipfile.ZIP_DEFLATED
            ) as zf:

                filepath = os.path.join(tmpdir, f'{filename}.{ext}')
                fig.savefig(fname=filepath)
                zf.write(
                    filename=filepath,
                    arcname=os.path.basename(filepath)
                )

        return in_memory

    def zip_map(
        self,
        fig: go.Figure
    ) -> BytesIO:
        """
        Zip choropleth map to html

        Parameters
        --------
        fig : go.Figure
            returned figure from choropleth_map()
        
        Returns
        --------
        BytesIO
        """
        in_memory = BytesIO()
        filename = 'map'

        with zipfile.ZipFile(
            file=in_memory,
            mode='w',
            compression=zipfile.ZIP_DEFLATED
        ) as zf:

            fig_bytes = fig.to_html()
            zf.writestr(
                zinfo_or_arcname=f'{filename}.html',
                data=fig_bytes
            )

        return in_memory

    def zip_gis(
        self,
        driver: str,
        ext: str
    ) -> BytesIO:
        """
        Zip GIS file

        Parameters
        --------
        driver : str
            driver to be passed to to_file
        ext : str
            output file extension
        
        Returns
        --------
        BytesIO
        """
        in_memory = BytesIO()
        filename = 'mesh'

        with tempfile.TemporaryDirectory() as tmpdir:
            with zipfile.ZipFile(
                file=in_memory,
                mode='w',
                compression=zipfile.ZIP_DEFLATED
            ) as zf:

                filepath = os.path.join(tmpdir, f'{filename}.{ext}')
                with warnings.catch_warnings(
                    action='ignore',
                    category=UserWarning
                ):
                    # hide UserWarning('crs' was not provided ...)
                    self.gdf.to_file(
                        filename=filepath,
                        driver=driver
                    )

                files = glob.glob(
                    pathname=os.path.join(tmpdir, f'{filename}.*')
                )

                for file in files:
                    zf.write(
                        filename=file,
                        arcname=os.path.basename(file)
                    )

        return in_memory
