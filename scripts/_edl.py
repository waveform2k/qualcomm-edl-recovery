"""Shared bootstrap for the scripts that drive bkerler/edl (edlclient).

edlclient is found by a normal import first. When it is installed outside the
interpreter's path (the nixpkgs `edl` wrapper, for one), set EDL_SITE_PACKAGES
to a colon-separated list of site-packages directories; see
references/environment.md.
"""
import os
import runpy
import site
import sys


def ensure_edlclient():
    try:
        import edlclient  # noqa: F401
        return
    except ImportError:
        pass
    for path in os.environ.get("EDL_SITE_PACKAGES", "").split(":"):
        if path:
            site.addsitedir(path)
    import edlclient  # noqa: F401  (raises when still missing)


def sahara_class():
    ensure_edlclient()
    from edlclient.Library import sahara
    return sahara.sahara


def run_edl(argv):
    """Run edl's command-line entry point with the given arguments."""
    ensure_edlclient()
    sys.argv = ["edl"] + list(argv)
    runpy.run_module("edlclient.edl", run_name="__main__", alter_sys=True)
