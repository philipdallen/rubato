"""muse_sample — sample-tier rendering from the Rubato CDN libraries.

The highest-quality library on the CDN is VSCO 2 CE (CC0): raw,
self-describing WAV pools (no SFZ in the upload). This package renders
a Mockup through those pools — pitch-faithful resampling, per-part
gains, tempo map, rubato offsets — as the quality tier above the sine
stand-in.
"""

from .pool import InstrumentPool, name_to_midi  # noqa: F401
from .render import (  # noqa: F401
    DEFAULT_INSTRUMENTS,
    LIBRARY,
    load_pools,
    render_mockup_samples,
)
