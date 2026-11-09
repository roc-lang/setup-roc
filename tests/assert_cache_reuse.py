"""Assert portable cache reuse for the sole CacheSmoke module, not test outcomes."""

from pathlib import Path
import re
import sys


def verify(text, mode):
    text = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", text)
    if not re.search(r"^No errors found in .+ for CacheSmoke\.roc\s*$", text, re.MULTILINE):
        raise ValueError("missing successful CacheSmoke module check")
    matches = re.findall(r"^\s*Modules: (\d+) total, (\d+) cached, (\d+) built\s*$", text, re.MULTILINE)
    expected = {"cold": ("1", "0", "1"), "restored": ("1", "1", "0")}[mode]
    if matches != [expected]:
        raise ValueError(f"{mode} CacheSmoke module cache counts must be {expected}; got {matches}")


if __name__ == "__main__":
    verify(Path(sys.argv[2]).read_text(), sys.argv[1])
