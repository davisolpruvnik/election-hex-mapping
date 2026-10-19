# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "marimo>=0.23.3",
#     "matplotlib>=3.11.2",
#     "numpy>=2.5.4",
#     "pandas>=3.0.6",
#     "seaborn>=0.13.2",
# ]
# ///

import marimo

__generated_with = "0.25.1"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import seaborn as sns

    return mo, np, pd, plt


@app.cell
def _():
    import geopandas as gpd
    import carto_flow.symbol_cartogram as smb

    return gpd, smb


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Importing the barangay data of the municipality
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(rf"""
    We need two datasets: the election data (preferably `.parquet`), and the barangay `.geojson` file).
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Since this works fine on single municipalities with just the right amount of barangays and precincts, import the `.geojson` file where the map data is in.

    A process to merge select `.geojson` folders containing individual shapefiles can be included here soon.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    For now, we will import a processed municipality; for this notebook: Infanta, Quezon.
    """)
    return


@app.cell
def _(gpd):
    infanta_geo = gpd.read_file('data/infanta_barangays.geojson')
    return (infanta_geo,)


@app.cell
def _(infanta_geo):
    infanta_geo
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Barangay names may differ in casings than they are in the election data, so we need to convert the barangay names into lowercase. Doing the same for towns and provinces is **only optional**.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Barangay name column in election data is `adm4_en`.
    """)
    return


@app.cell
def _(infanta_geo):
    infanta_geo['brgy_lowered'] = infanta_geo['adm4_en'].astype(str).str.strip().str.lower()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Import election data
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We will import the full election data, it is in `.parquet` format for faster processing and reading.
    """)
    return


@app.cell
def _(pd):
    df_full = pd.read_parquet('data/election_master_file.parquet')
    return (df_full,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The data contains nationwide results down to precinct levels of each barangays in the Philippines. You are free to choose what province or specific place(s) you want to pick.
    """)
    return


@app.cell
def _():
    # # Filter regions
    # df_full_{province of choice} = df_full[df_full['province'] == '{province of choice}'] (or if multiple, replace == with `.isin([specific provinces]))

    # # Filter municipalities
    # df_full_{province_municipality of choice} = df_full[(df_full['province'] == '{province of choice}') & (df_full['municipality'] == '{municipality of choice}')] (or if multiple, replace == with `.isin([specific municipalities]))

    # Same mechanism for barangays, just add the filters after the municipality filter
    return


@app.cell
def _(df_full):
    df_full.sample(10, random_state=42)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Apply the filter for province or municipality depending on your preference. For this part, we'll do the same filter we did on the `.geojson`. We also do the same lowercase application, this time with all units (provinces, towns, barangays).
    """)
    return


@app.cell
def _(df_full):
    df_result_infanta = df_full[(df_full['province'] == 'QUEZON') & (df_full['municipality'] == 'INFANTA')]
    return (df_result_infanta,)


@app.cell
def _(df_result_infanta):
    df_result_infanta['brgy_lowered'] = df_result_infanta['barangay'].astype(str).str.strip().str.lower()
    df_result_infanta['town_lowered'] = df_result_infanta['municipality'].astype(str).str.strip().str.lower()
    df_result_infanta['prov_lowered'] = df_result_infanta['province'].astype(str).str.strip().str.lower()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    After the process, we now merge them, thru their common variable: the barangay lowercase version (`brgy_lowered`).
    """)
    return


@app.cell
def _(df_result_infanta, infanta_geo):
    merged_gdf = infanta_geo[["brgy_lowered", "geometry"]].merge(
        df_result_infanta, on="brgy_lowered", how="left"
    )
    return (merged_gdf,)


@app.cell
def _(merged_gdf):
    merged_gdf
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Now, we move to counting number of clustered precincts per barangay, because this would act as a filler or the element replacing the shapefiles of the map, while still accessing precinct data for the election details.
    """)
    return


@app.cell
def _(merged_gdf):
    # 3. Count unique precinct IDs per barangay
    barangay_precinct_counts = (
        merged_gdf[merged_gdf["precinct_id"] != ""]
        .groupby(["brgy_lowered", "barangay", "geometry"])["precinct_id"]
        .nunique()
        .reset_index(name="precinct_count")
    )
    return (barangay_precinct_counts,)


@app.cell
def _(barangay_precinct_counts):
    barangay_precinct_counts
    return


@app.cell
def _(barangay_precinct_counts, gpd, merged_gdf):
    barangay_precinct_counts_df = gpd.GeoDataFrame(
        barangay_precinct_counts,
        geometry="geometry",
        crs=merged_gdf.crs  # use the CRS of your original boundaries GeoDataFrame
    )
    return (barangay_precinct_counts_df,)


@app.cell
def _(barangay_precinct_counts_df, smb):
    symbol_carto = smb.create_symbol_cartogram(
        barangay_precinct_counts_df,
        # provide a column with the number of tiles per state
        tile_count="precinct_count",
        # place the tiles on a shared hexagon lattice
        layout=smb.MosaicLayout(spacing=0.06),
        show_progress=False,
    )
    return (symbol_carto,)


@app.cell
def _(plt, symbol_carto):
    import matplotlib.patheffects as pe
    from shapely.ops import unary_union
    from shapely.geometry import Polygon

    fig, ax = plt.subplots(1, 1, figsize=(10, 8))

    # 1. Base cartogram plot
    symbol_carto.plot(
        ax=ax,
        column="precinct_count",
        edgecolor="none",      # ← this
        linewidth=0,           # ← and this, for safety
        legend_kwds={"shrink": 0.75},
    )

    # 2. Extract tiles GeoDataFrame
    symbols_gdf = (
        symbol_carto.to_geodataframe()
        if hasattr(symbol_carto, "to_geodataframe")
        else symbol_carto.symbols
    )

    # 3. Build only the exterior outlines per barangay
    exterior_lines = []
    centroids = {}

    # Slightly buffer to bridge the 0.06 gap so tiles fuse into solid shapes
    buffer_dist = 0.035

    for brgy, group in symbols_gdf.groupby("barangay"):
        # Bridge gaps and union all hex tiles for this barangay
        buffered_union = unary_union(group.geometry.buffer(buffer_dist))
        # Un-buffer back to original footprint
        merged = buffered_union.buffer(-buffer_dist)

        # Store centroid for label positioning
        centroids[brgy] = merged.centroid

        # Extract strictly the outer perimeter (ignoring all interior rings/holes)
        if merged.geom_type == "Polygon":
            exterior_lines.append(merged.exterior)
        elif merged.geom_type == "MultiPolygon":
            for poly in merged.geoms if merged.geom_type == "MultiPolygon" else [merged]:
                exterior_lines.append(poly.buffer(-0.02).exterior)

    # 5. Place single barangay labels at each cluster centroid
    for brgy, pt in centroids.items():
        ax.text(
            pt.x,
            pt.y,
            str(brgy),
            ha="center",
            va="center",
            fontsize=8,
            color="white",
            fontweight="bold",
            zorder=4,
            path_effects=[pe.withStroke(linewidth=2, foreground="black")],
        )

    plt.show()
    return pe, symbols_gdf


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    This visualization just means that the numbers of precincts filled out the shape of the barangay. For example, Dinahican has 7 precincts, the visualization automatically distributed the hex shapes to fill out the shapes encompassing the barangay.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Now, let's do the mapping based on variables: mapping barangay/precincts by turnout (how many people out of registered voters actually went out to vote).
    """)
    return


@app.cell
def _(df_result_infanta, np, pd):
    # Use the filtered election data for this to leave the data with geometries unaffected and corrupted

    precinct_df = (
            df_result_infanta[
                df_result_infanta['precinct_id'].notna() & 
                (df_result_infanta['precinct_id'].astype(str).str.strip() != '')
            ]
            .groupby(['barangay', 'precinct_id'], as_index=False)
            .agg({
                'registered_voters': 'first',
                'actual_voters': 'first',
            })
        )

    # Ensure numeric types
    precinct_df['registered_voters'] = pd.to_numeric(precinct_df['registered_voters'], errors='coerce').fillna(0).astype(int)
    precinct_df['actual_voters'] = pd.to_numeric(precinct_df['actual_voters'], errors='coerce').fillna(0).astype(int)

    # Calculate precinct-specific turnout percentage
    precinct_df['turnout_pct'] = np.where(
            precinct_df['registered_voters'] > 0,
            ((precinct_df['actual_voters'] / precinct_df['registered_voters']) * 100).round(2),
            0.0
        )

    # Sort predictably within each barangay
    precinct_df = precinct_df.sort_values(by=['barangay', 'precinct_id']).reset_index(drop=True)
    return (precinct_df,)


@app.cell
def _(np, precinct_df):
    barangay_df = (
            precinct_df
            .groupby('barangay', as_index=False)
            .agg({
                'precinct_id': 'count',
                'registered_voters': 'sum',
                'actual_voters': 'sum',
            })
            .rename(columns={'precinct_id': 'total_precincts'})
        )

    # Calculate overall barangay turnout percentage
    barangay_df['turnout_pct'] = np.where(
            barangay_df['registered_voters'] > 0,
            ((barangay_df['actual_voters'] / barangay_df['registered_voters']) * 100).round(2),
            0.0
        )

    barangay_df = barangay_df.sort_values(by='turnout_pct', ascending=False).reset_index(drop=True)
    return (barangay_df,)


@app.cell
def _(barangay_df):
    barangay_df
    return


@app.cell
def _(precinct_df, symbols_gdf):
    precinct_df_mapped = precinct_df.copy()
    precinct_df_mapped['tile_idx'] = precinct_df_mapped.groupby('barangay').cumcount()

    symbols_copy = symbols_gdf.copy()
    symbols_copy['tile_idx'] = symbols_copy.groupby('barangay').cumcount()

        # Merge on both barangay AND tile_idx
    hex_carto_gdf = symbols_copy.merge(
            precinct_df_mapped,
            on=['barangay', 'tile_idx'],
            how='left'
        ).drop(columns=['tile_idx'])
    return (hex_carto_gdf,)


@app.cell
def _(hex_carto_gdf):
    hex_carto_gdf
    return


@app.cell
def _(hex_carto_gdf, pd, pe, plt):
    # 1. Safety check: ensure turnout_pct is numeric
    hex_carto_gdf["turnout_pct"] = pd.to_numeric(
        hex_carto_gdf["turnout_pct"], errors="coerce"
    )

    # 2. Setup figure & axis
    fig_, ax_1 = plt.subplots(1, 1, figsize=(12, 10), facecolor="#f8fafc")
    ax_1.set_facecolor("#f8fafc")

    # 3. Plot individual precinct hexes on ax_1 using Natural Breaks (5 bins)
    hex_carto_gdf.plot(
        ax=ax_1,
        column="turnout_pct",
        scheme="natural_breaks",  # Uses Jenks Natural Breaks
        k=5,  # 5 bins
        cmap="YlGnBu",
        edgecolor="#ffffff",
        linewidth=0.75,
        legend=True,
        missing_kwds={"color": "#cbd5e1", "label": "No Data"},
        legend_kwds={
            "loc": "lower left",  # Position of the discrete legend
            "title": "Voter Turnout (%)",
            "frameon": True,
            "facecolor": "#ffffff",
            "edgecolor": "#e2e8f0",
            "fontsize": 8.5,
            "title_fontsize": 9.5,
        },
        zorder=2,
    )

    # 4. Center barangay labels on ax_1
    for brgy_1, group_1 in hex_carto_gdf.groupby("barangay"):
        center_1 = group_1.geometry.unary_union.centroid
        ax_1.text(
            center_1.x,
            center_1.y,
            str(brgy_1).upper(),
            ha="center",
            va="center",
            fontsize=6.5,
            color="#ffffff",
            fontweight="bold",
            zorder=4,
            path_effects=[pe.withStroke(linewidth=2.5, foreground="#0f172a")],
        )

    ax_1.set_title(
        "Infanta, Quezon — Precinct-Level Voter Turnout",
        fontsize=13,
        fontweight="bold",
        pad=14,
        color="#0f172a",
    )
    ax_1.set_axis_off()
    plt.tight_layout()
    plt.show()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    This is the turnout plot, using the hex visualization we made in the code above.

    We can see that the Poblacion and Dinahican area have lower turnouts compared to the rest of Infanta's barangays.

    This is just one of the variables where you can apply this visualization; you can also use this on the mayoral race winners, or number of registered voters, or anything else, all while giving you the last shot for an area you prefer.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    You can use Jenks natural breaks division of colors, this is used in the election detail section of BetterInfanta.
    """)
    return


if __name__ == "__main__":
    app.run()
