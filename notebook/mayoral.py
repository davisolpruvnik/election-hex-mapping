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
    Now, we move to processing the local election results of the chosen area, this time, the elections for mayor and vice mayor of Infanta, Quezon.
    """)
    return


@app.cell
def _(merged_gdf, np, pd):
    # ---------------------------------------------------------
    # 1. CANDIDATE NAME MAPPING / DISAMBIGUATION
    # ---------------------------------------------------------
    NAME_MAP = {
        # Mayor candidates (distinct surnames)
        "RUANTO, LORD ARNEL L.": "Ruanto",
        "RUANTO, L.A.": "Ruanto",
        "ESCUETA, ERIBERTO C.": "Escueta",
        "ESCUETA, EBIT": "Escueta",
        # Vice Mayor candidates (shared surname "America")
        "AMERICA, FILIPINA GRACE R.": "America (Grace)",
        "AMERICA, GRACE": "America (Grace)",
        "AMERICA, MANNIE A.": "America (Mannie)",
        "AMERICA, BRO. MANNIE": "America (Mannie)",
    }


    def clean_candidate_name(raw_name: str, contest_candidates: list) -> str:
        """Returns mapped name, or falls back to Surname (Firstname) extraction."""
        raw = str(raw_name).strip()

        if raw in NAME_MAP:
            return NAME_MAP[raw]
        for k, v in NAME_MAP.items():
            if k.lower() in raw.lower() or raw.lower() in k.lower():
                return v

        if "," in raw:
            surname = raw.split(",")[0].strip().title()
            first_part = raw.split(",")[1].split("(")[0].strip().title()
        else:
            parts = raw.split()
            surname = parts[-1].title()
            first_part = " ".join(parts[:-1]).title()

        other_surnames = [
            c.split(",")[0].strip().title() if "," in c else c.split()[-1].title()
            for c in contest_candidates
            if c != raw
        ]

        if surname in other_surnames:
            first_known = first_part.split()[0] if first_part else ""
            return f"{surname} ({first_known})".strip()

        return surname

    # Clean boolean masks (No DataFrame wrapping!)
    is_mayor = merged_gdf["contest_code"] == 856200
    is_vm = merged_gdf["contest_code"] == 956200

    GEO_KEY = "precinct_id"


    # ---------------------------------------------------------
    # 3. HELPER: PROCESS A TWO-CANDIDATE RACE PER PRECINCT
    # ---------------------------------------------------------
    def process_two_way_race(
        contest_df, prefix="mayor", target_violet_cand="Ruanto"
    ):
        contest_df = contest_df.copy()
        contest_df["votes"] = pd.to_numeric(
            contest_df["votes"], errors="coerce"
        ).fillna(0)

        # Pivot votes: index = precinct_id, columns = raw candidate names
        cand_votes = (
            contest_df.groupby([GEO_KEY, "candidate"])["votes"]
            .sum()
            .unstack(fill_value=0)
        )

        raw_cands = list(cand_votes.columns)
        cand_clean_map = {
            raw: clean_candidate_name(raw, raw_cands) for raw in raw_cands
        }

        # Match target Violet candidate
        target_lower = target_violet_cand.lower()
        violet_col = next(
            (
                raw
                for raw in raw_cands
                if target_lower in cand_clean_map[raw].lower()
                or target_lower in raw.lower()
                or any(
                    token in cand_clean_map[raw].lower()
                    for token in target_lower.split()
                    if len(token) > 3
                )
            ),
            raw_cands[0],
        )
        green_col = next(
            (raw for raw in raw_cands if raw != violet_col), raw_cands[0]
        )

        total_votes = cand_votes[violet_col] + cand_votes[green_col]

        # Calculate precinct-level percentages
        pct_violet = np.where(
            total_votes > 0, (cand_votes[violet_col] / total_votes) * 100.0, np.nan
        )
        pct_green = np.where(
            total_votes > 0, (cand_votes[green_col] / total_votes) * 100.0, np.nan
        )

        winner = np.where(
            cand_votes[violet_col] > cand_votes[green_col],
            cand_clean_map[violet_col],
            np.where(
                cand_votes[green_col] > cand_votes[violet_col],
                cand_clean_map[green_col],
                "Tie",
            ),
        )

        # Scale: > 50 = Violet (Ruanto / Mannie), < 50 = Green (Escueta / Grace)
        diverging_pct = pct_violet

        return (
            pd.DataFrame(
                {
                    f"{prefix}_winner": winner,
                    f"winner_{prefix}_pct": np.nanmax(
                        np.column_stack([pct_violet, pct_green]), axis=1
                    ).round(2),
                    f"diverging_{prefix}_pct": diverging_pct.round(2),
                },
                index=cand_votes.index,
            ),
            cand_clean_map[green_col],
            cand_clean_map[violet_col],
        )

    return GEO_KEY, is_mayor, is_vm, process_two_way_race


@app.cell(hide_code=True)
def _(is_mayor, is_vm, merged_gdf, process_two_way_race):
    mayor_res, mayor_green, mayor_violet = process_two_way_race(
        merged_gdf[is_mayor], prefix="mayor", target_violet_cand="Ruanto"
    )
    vm_res, vm_green, vm_violet = process_two_way_race(
        merged_gdf[is_vm], prefix="vice_mayor", target_violet_cand="Mannie"
    )
    return mayor_res, vm_res


@app.cell
def _(GEO_KEY, gpd, mayor_res, merged_gdf, vm_res):
    meta_cols = [
        c
        for c in [
            "geometry",
            "region",
            "province",
            "municipality",
            "brgy_lowered",
            "barangay",
            "voting_center",
            "precinct_id",
            "precinct_in_cluster",
            "registered_voters",
            "actual_voters",
            "valid_ballots",
            "turnout_pct",
        ]
        if c in merged_gdf.columns
    ]

    base_geo = merged_gdf.drop_duplicates(subset=[GEO_KEY]).set_index(GEO_KEY)[
        [col for col in meta_cols if col != GEO_KEY]
    ]

    merged_gdf_1 = gpd.GeoDataFrame(
        base_geo, geometry="geometry", crs=merged_gdf.crs
    )

    # Join precinct results back onto the base metadata
    merged_gdf_2 = gpd.GeoDataFrame(
        merged_gdf_1.join(mayor_res).join(vm_res).reset_index(),
        geometry="geometry",
        crs=merged_gdf.crs,
    )

    # ---------------------------------------------------------
    # 6. COMBINED MAYOR-VICE WINNER PAIRINGS PER PRECINCT
    # ---------------------------------------------------------
    merged_gdf_2["mayor_vice_winners"] = (
        merged_gdf_2["mayor_winner"] + "-" + merged_gdf_2["vice_mayor_winner"]
    )

    print(f"Total Precincts Processed: {len(merged_gdf_2)}")
    print("\nPrecinct Breakdown of Tandem Winners:")
    print(merged_gdf_2["mayor_vice_winners"].value_counts())
    print("\nSample Preview with non-50 numbers:")
    print(
        merged_gdf_2[
            [
                "barangay",
                "precinct_id",
                "mayor_winner",
                "diverging_mayor_pct",
                "vice_mayor_winner",
                "diverging_vice_mayor_pct",
                "mayor_vice_winners",
            ]
        ].head()
    )
    return (merged_gdf_2,)


@app.cell
def _(merged_gdf_2):
    # 3. Count unique precinct IDs per barangay
    barangay_precinct_counts = (
        merged_gdf_2[merged_gdf_2["precinct_id"] != ""]
        .groupby(["brgy_lowered", "barangay", "geometry"])["precinct_id"]
        .nunique()
        .reset_index(name="precinct_count")
    )
    return (barangay_precinct_counts,)


@app.cell
def _(barangay_precinct_counts):
    barangay_precinct_counts
    return


@app.cell(hide_code=True)
def _(barangay_precinct_counts, gpd, merged_gdf):
    barangay_precinct_counts_df = gpd.GeoDataFrame(
        barangay_precinct_counts,
        geometry="geometry",
        crs=merged_gdf.crs  # use the CRS of your original boundaries GeoDataFrame
    )
    return (barangay_precinct_counts_df,)


@app.cell
def _(barangay_precinct_counts_df, gpd, merged_gdf_2, smb):
    import matplotlib.patches as mpatches
    import matplotlib.patheffects as pe
    from shapely.geometry import MultiPolygon, Polygon
    from shapely.ops import unary_union

    # ==============================================================================
    # 1. CREATE A CLEAN BARANGAY-LEVEL BASE FOR THE CARTOGRAM
    # ==============================================================================
    # 💡 smb needs exactly 1 row per barangay with its precinct count
    barangay_carto_base = (
        merged_gdf_2.groupby("barangay")
        .agg(
            geometry=("geometry", "first"), precinct_count=("precinct_id", "count")
        )
        .reset_index()
    )
    barangay_carto_base = gpd.GeoDataFrame(
        barangay_carto_base, geometry="geometry", crs=merged_gdf_2.crs
    )

    # ==============================================================================
    # 2. GENERATE SYMBOL CARTOGRAM LATTICE
    # ==============================================================================
    symbol_carto = smb.create_symbol_cartogram(
        barangay_precinct_counts_df,
        # provide a column with the number of tiles per state
        tile_count="precinct_count",
        # place the tiles on a shared hexagon lattice
        layout=smb.MosaicLayout(spacing=0.06),
        show_progress=False,
    )

    symbols_gdf = (
        symbol_carto.to_geodataframe()
        if hasattr(symbol_carto, "to_geodataframe")
        else symbol_carto.symbols
    )

    return MultiPolygon, Polygon, mpatches, pe, symbols_gdf, unary_union


@app.cell(hide_code=True)
def _(
    MultiPolygon,
    Polygon,
    gpd,
    merged_gdf_2,
    mpatches,
    pe,
    plt,
    symbols_gdf,
    unary_union,
):
    # Sort precincts deterministically within each barangay
    precinct_sorted = merged_gdf_2.sort_values(
        ["barangay", "precinct_id"]
    ).reset_index(drop=True)
    precinct_sorted["tile_idx"] = precinct_sorted.groupby("barangay").cumcount()

    # Number the hex tiles within each barangay
    symbols_copy = symbols_gdf.copy()
    symbols_copy["tile_idx"] = symbols_copy.groupby("barangay").cumcount()

    # Columns to transfer from precinct results
    cols_to_transfer = [
        c
        for c in [
            "precinct_id",
            "registered_voters",
            "actual_voters",
            "mayor_winner",
            "vice_mayor_winner",
            "mayor_vice_winners",
            "diverging_mayor_pct",
            "diverging_vice_mayor_pct",
            "turnout_pct",
        ]
        if c in precinct_sorted.columns
    ]

    # 💡 hex_carto_gdf now has 1 row per PRECINCT with its true geometry hex tile
    hex_carto_gdf = symbols_copy.merge(
        precinct_sorted[["barangay", "tile_idx"] + cols_to_transfer],
        on=["barangay", "tile_idx"],
        how="left",
    ).drop(columns=["tile_idx"])

    # ==============================================================================
    # 4. COLOR PALETTE DEFINITION (Ruanto/Mannie = Violet, Escueta/Grace = Green)
    # ==============================================================================
    TANDEM_COLORS = {
        "Ruanto-America (Mannie)": "#7c3aed",  # Violet (Slate A)
        "Escueta-America (Grace)": "#10b981",  # Green (Slate B)
        "Ruanto-America (Grace)": "#f59e0b",  # Amber / Gold (Split Ticket)
        "Escueta-America (Mannie)": "#06b6d4",  # Cyan (Alternative Split Ticket)
    }
    DEFAULT_COLOR = "#94a3b8"  # Slate fallback

    hex_carto_gdf["fill_color"] = (
        hex_carto_gdf["mayor_vice_winners"].map(TANDEM_COLORS).fillna(DEFAULT_COLOR)
    )

    # ==============================================================================
    # 5. COMPUTE EXTERIOR BOUNDARIES & CENTROIDS PER BARANGAY
    # ==============================================================================
    exterior_lines = []
    centroids = {}
    buffer_dist = 0.035  # Bridges the 0.06 layout gap

    for brgy, group in hex_carto_gdf.groupby("barangay"):
        buffered_union = unary_union(group.geometry.buffer(buffer_dist))
        merged = buffered_union.buffer(-buffer_dist)

        centroids[brgy] = merged.centroid

        if isinstance(merged, Polygon):
            exterior_lines.append(merged.exterior)
        elif isinstance(merged, MultiPolygon):
            for poly in merged.geoms:
                exterior_lines.append(poly.exterior)

    outlines_gdf = gpd.GeoSeries(exterior_lines, crs=hex_carto_gdf.crs)

    # ==============================================================================
    # 6. RENDER THE CARTOGRAM PLOT
    # ==============================================================================
    fig, ax = plt.subplots(1, 1, figsize=(13, 11), facecolor="#f8fafc")
    ax.set_facecolor("#f8fafc")

    # A. Plot individual precinct hex tiles (each shows its own precinct winner!)
    hex_carto_gdf.plot(
        ax=ax,
        color=hex_carto_gdf["fill_color"],
        edgecolor="#ffffff",
        linewidth=0.7,
        zorder=2,
    )

    # C. Place single barangay labels at each cluster centroid
    for brgy, pt in centroids.items():
        ax.text(
            pt.x,
            pt.y,
            str(brgy).upper(),
            ha="center",
            va="center",
            fontsize=6.5,
            color="#ffffff",
            fontweight="bold",
            zorder=4,
            path_effects=[pe.withStroke(linewidth=2.5, foreground="#0f172a")],
        )

    # D. Legend for observed pairings
    observed_pairs = [
        p
        for p in hex_carto_gdf["mayor_vice_winners"].dropna().unique()
        if p in TANDEM_COLORS
    ]

    legend_handles = [
        mpatches.Patch(color=TANDEM_COLORS[pair], label=pair)
        for pair in observed_pairs
    ]

    legend = ax.legend(
        handles=legend_handles,
        title="Mayor & Vice-Mayor Tandem Winners",
        title_fontsize=11,
        fontsize=9.5,
        loc="lower left",
        frameon=True,
        facecolor="#ffffff",
        edgecolor="#cbd5e1",
        framealpha=0.95,
        borderpad=0.8,
        labelspacing=0.5,
    )
    legend.get_title().set_fontweight("bold")

    ax.set_title(
        "Infanta, Quezon — Precinct Hex Cartogram: Tandem Winners",
        fontsize=14,
        fontweight="bold",
        pad=16,
        color="#0f172a",
    )
    ax.set_axis_off()

    plt.tight_layout()
    plt.show()
    return centroids, hex_carto_gdf, outlines_gdf


@app.cell
def _(mo):
    mo.md(r"""
    This visualization just means that the numbers of precincts filled out the shape of the barangay. For example, Dinahican has 7 precincts, the visualization automatically distributed the hex shapes to fill out the shapes encompassing the barangay.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    Now, let's do the mapping based on winners for mayor and vice mayor per precinct, by how much each winners led, they are already represented by the color and shades.
    """)
    return


@app.cell
def _(centroids, hex_carto_gdf, np, outlines_gdf, pe, plt):
    import mapclassify
    import matplotlib.colors as mcolors
    # ==============================================================================
    # 1. MIRRORED JENKS BINS (FOLLOWING THE MAX % CANDIDATE)
    # ==============================================================================
    def get_mirrored_jenks_bins(series, center=50.0, k=3):
        vals = series.dropna().values

        # Candidate real vote shares
        green_shares = 100.0 - vals
        violet_shares = vals

        max_green = green_shares.max()
        max_violet = violet_shares.max()

        # Base max rounded to nearest 5%
        peak_share = max(max_green, max_violet)
        base_max = int(round(peak_share / 5.0) * 5)
        base_max = max(base_max, 55)

        # 1. Select the dominant candidate's winning precincts
        if max_violet >= max_green:
            dominant_cand = "violet"
            lead_shares = violet_shares[violet_shares >= center]
        else:
            dominant_cand = "green"
            lead_shares = green_shares[green_shares >= center]

        # Clip to base_max
        lead_shares_clipped = np.clip(lead_shares, center, base_max)

        # 2. Run Jenks on the dominant candidate's winning precincts (50% -> base_max)
        k_clean = min(len(np.unique(lead_shares_clipped)), k)
        if k_clean > 1:
            nb = mapclassify.NaturalBreaks(lead_shares_clipped, k=k_clean)
            # Only take intermediate cutoffs between 50 and base_max
            breaks = [round(b, 1) for b in nb.bins if center < b < base_max]
        else:
            breaks = []

        # 3. Calculate the margins (deltas) above 50%
        deltas = [round(b - center, 1) for b in breaks]
        max_delta = float(base_max - center)  # e.g., 65 - 50 = 15.0

        # 4. Mirror those exact deltas symmetrically across 50%
        # Left (Green coordinates): 50 - delta
        # Right (Violet coordinates): 50 + delta
        left_coords = [round(center - d, 1) for d in reversed(deltas)]
        right_coords = [round(center + d, 1) for d in deltas]

        lower_bound = round(center - max_delta, 1)
        upper_bound = round(center + max_delta, 1)

        bins = sorted(
            list(
                set(
                    [lower_bound]
                    + left_coords
                    + [center]
                    + right_coords
                    + [upper_bound]
                )
            )
        )

        return bins, base_max, lower_bound, upper_bound, dominant_cand


    # ==============================================================================
    # 2. PLOTTING FUNCTION
    # ==============================================================================
    def plot_race_cartogram(
        gdf,
        outlines,
        centroids_dict,
        column_name,
        title,
        cand_green_name,
        cand_violet_name,
        filename=None,
        k=3,
    ):
        # A. Calculate mirrored bins
        bins, base_max, lower_bound, upper_bound, dominant = (
            get_mirrored_jenks_bins(gdf[column_name], center=50.0, k=k)
        )

        # Number of bins on each side is guaranteed equal
        n_side = (len(bins) - 1) // 2

        green_shades = [
            mcolors.to_hex(plt.cm.Greens_r(x))
            for x in np.linspace(0.15, 0.75, n_side)
        ]
        violet_shades = [
            mcolors.to_hex(plt.cm.Purples(x))
            for x in np.linspace(0.35, 0.88, n_side)
        ]
        discrete_palette = green_shades + violet_shades

        cmap_jenks = mcolors.ListedColormap(discrete_palette)
        norm_jenks = mcolors.BoundaryNorm(bins, ncolors=cmap_jenks.N)

        # Clip data on map to the symmetric window
        gdf_plot = gdf.copy()
        gdf_plot["clipped_val"] = gdf_plot[column_name].clip(
            lower_bound, upper_bound
        )

        # B. Setup Figure
        fig, ax = plt.subplots(1, 1, figsize=(12, 11), facecolor="#f8fafc")
        ax.set_facecolor("#f8fafc")

        # C. Plot hex tiles
        plot_map = gdf_plot.plot(
            ax=ax,
            column="clipped_val",
            cmap=cmap_jenks,
            norm=norm_jenks,
            edgecolor="#ffffff",
            linewidth=0.7,
            legend=True,
            legend_kwds={
                "orientation": "horizontal",
                "shrink": 0.6,
                "pad": 0.04,
                "aspect": 26,
                "spacing": "uniform",
            },
            zorder=2,
        )

        # D. Outer barangay boundaries
        outlines.plot(ax=ax, color="#0f172a", linewidth=1.75, zorder=3)

        # E. Center barangay labels
        for brgy, pt in centroids_dict.items():
            ax.text(
                pt.x,
                pt.y,
                str(brgy).upper(),
                ha="center",
                va="center",
                fontsize=6.5,
                color="#ffffff",
                fontweight="bold",
                zorder=4,
                path_effects=[pe.withStroke(linewidth=2.5, foreground="#0f172a")],
            )

        # F. Colorbar with identical, mirrored percentages
        cbar = plot_map.get_figure().axes[-1]
        cbar.set_facecolor("#f8fafc")
        cbar.set_xticks(bins)

        tick_labels = []
        for i, b in enumerate(bins):
            if i == 0:
                tick_labels.append(f"{cand_green_name}\n({base_max}%)")
            elif b == 50.0:
                tick_labels.append("50%\n(Tie)")
            elif i == len(bins) - 1:
                tick_labels.append(f"{cand_violet_name}\n({base_max}%)")
            elif b < 50.0:
                # Displays actual percentage for Green (100 - b)
                tick_labels.append(f"{100.0 - b:.1f}%")
            else:
                # Displays actual percentage for Violet (b)
                tick_labels.append(f"{b:.1f}%")

        cbar.set_xticklabels(
            tick_labels, fontsize=8.5, fontweight="medium", color="#0f172a"
        )
        cbar.tick_params(size=5, color="#64748b")

        lead_cand_name = cand_violet_name if dominant == "violet" else cand_green_name
        cbar.set_title(
            f"Vote Share (%) — Symmetric Jenks (Followed {lead_cand_name}'s Peak: {base_max}%)",
            fontsize=10,
            fontweight="bold",
            pad=10,
            color="#0f172a",
        )

        ax.set_title(
            title,
            fontsize=14,
            fontweight="bold",
            pad=16,
            color="#0f172a",
        )
        ax.set_axis_off()

        plt.tight_layout()
        if filename:
            plt.savefig(filename, dpi=300, bbox_inches="tight")
        plt.show()


    # ==============================================================================
    # 3. GENERATE PLOTS
    # ==============================================================================

    # --- MAYOR RACE ---
    plot_race_cartogram(
        gdf=hex_carto_gdf,
        outlines=outlines_gdf,
        centroids_dict=centroids,
        column_name="diverging_mayor_pct",
        title="Infanta, Quezon — Mayoral Results (Mirrored Jenks Breaks)",
        cand_green_name="Escueta",
        cand_violet_name="Ruanto",
        k=3,
        filename="./output/mayor_mirrored_jenks.png",
    )

    # --- VICE MAYOR RACE ---
    plot_race_cartogram(
        gdf=hex_carto_gdf,
        outlines=outlines_gdf,
        centroids_dict=centroids,
        column_name="diverging_vice_mayor_pct",
        title="Infanta, Quezon — Vice Mayoral Results (Mirrored Jenks Breaks)",
        cand_green_name="America (Grace)",
        cand_violet_name="America (Mannie)",
        k=3,
        filename="./output/vice_mayor_mirrored_jenks.png",
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    This is the results plot, using the hex visualization we made in the code above.

    We can see that the Infanta's barangays are mostly Ruanto for mayor while almost distributed evenly between the two Americas for vice mayor, and the Ruanto-Mannie clinching the two largest barangays Dinahican and Gumian, and Grace America winning in central barangays.

    This is just one of the variables where you can apply this visualization; you can also use this on the turnouts, or number of registered voters, or anything else, all while giving you the last shot for an area you prefer.
    """)
    return


if __name__ == "__main__":
    app.run()
