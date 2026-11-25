import os


def asset_path(filename):
    """Full path to a file in the assets folder, no matter where you run the app from."""
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "assets", filename)