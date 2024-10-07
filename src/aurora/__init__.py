from functools import lru_cache
from subprocess import STDOUT

VERSION = "2.0.0"


@lru_cache(1)
def get_full_version(git_commit=True):
    commit = ""
    if git_commit:
        import subprocess

        try:
            res = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], stderr=STDOUT)
            commit = "-" + res.decode("utf8")[:-1]
        except (subprocess.CalledProcessError, FileNotFoundError):  # pragma: no-cover
            pass

    return f"{VERSION}{commit}"


@lru_cache(1)
def get_git_status(clean="(nothing to commit)", dirty="(uncommitted changes)"):
    import subprocess

    try:
        uncommited = subprocess.check_output(["git", "status", "-s"], stderr=STDOUT)
        return dirty if uncommited else clean
    except (subprocess.CalledProcessError, FileNotFoundError):  # pragma: no-cover
        return ""
