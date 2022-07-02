from pathlib import Path
from pkg_resources import resource_filename
import json
import pandas as pd
import numpy as np
import os
import sys

# kepler is optional, check if installed.
try:
    from keplergl import KeplerGl
except:
    has_kepler = False
else:
    has_kepler = True


class HiddenPrints:
    """Disables stdout prints for a block of code."""

    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, "w")

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout


def is_valid_lat(val: str) -> bool:
    """Given a string, check if it corresponds to a valid decimal latitude value"""
    try:
        val = float(val)
        return val >= -90 and val <= 90
    except:
        return False


def is_valid_lon(val: str) -> bool:
    """Given a string, check if it corresponds to a valid decimal longitude value"""
    try:
        val = float(val)
        return val >= -180 and val <= 180
    except:
        return False


def read_csv_file(filename):
    """Read input csv file, dropping rows that don't have valid location data."""
    df = pd.read_csv(filename)
    initial_rows = len(df)

    df = df.dropna(subset=["lat", "lon"])
    df = df.replace(
        {np.nan: None}
    )  # replace for other fields not to break kepler parsing
    print(f"Ignored {initial_rows - len(df)} coordinates with NaN")

    valid_index = df.lat.astype(str).apply(is_valid_lat) & df.lon.astype(str).apply(
        is_valid_lon
    )
    if len(df_invalid := df[~valid_index]):
        print(f"Found {len(df_invalid)} invalid coordinate pairs, ignoring:")
        print(df_invalid[["lat", "lon"]].to_string())
    return df[valid_index]


def ensure_file_path(dirname, filename):
    """Ensure a parent directory exists for a file."""
    path = Path(dirname)
    path.mkdir(parents=True, exist_ok=True)
    return path / filename


def write_output_file(dirname, filename, data):
    """Write a file, ensuring parent directories."""
    filepath = ensure_file_path(dirname, filename)

    with open(filepath, "w") as f:
        f.write(data)

    return filepath


def write_visualization(dirname, filename, data):
    """Write a visualization, ensuring parent directories."""

    if not has_kepler:
        return None

    # Hide kepler stdout output.
    with HiddenPrints():
        map = KeplerGl()

    map.add_data(data=data, name="clusters")

    # config configures a default color scheme for our clusters layer.
    config_file = resource_filename("geoclustering", "kepler_config.json")
    with open(config_file) as f:
        map.config = json.loads(f.read())

    filepath = ensure_file_path(dirname, filename)

    # Hide kepler stdout output.
    with HiddenPrints():
        map.save_to_html(file_name=str(filepath), center_map=True)

    return filepath
