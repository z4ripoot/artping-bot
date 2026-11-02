"""Starts the bot from a script path, for hosts that can't run `python -m fjormcord.bot.artping` (such as PebbleHost).

Running `src/fjormcord/bot/artping/__main__.py` directly fails with "No module named 'fjormcord'": Python puts the
script's own directory on the path, not `src`. This file sits in the repository root and adds `src` itself.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from fjormcord.bot.artping.__main__ import main  # noqa: E402

if __name__ == "__main__":
    main()
