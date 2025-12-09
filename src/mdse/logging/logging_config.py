# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://github.com/TFYA99ProjGroup/MDSE/blob/main/LICENSE>.


import logging
import sys
from datetime import datetime
from pathlib import Path


def setup_logging(debug=False):
    logfile = Path(f"logs/simulation_{datetime.now():%Y%m%d_%H%M%S}.log")
    logfile.parent.mkdir(parents=True, exist_ok=True)

    level = logging.DEBUG if debug else logging.INFO

    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Save to log-file
    file_handler = logging.FileHandler(logfile, mode="a")  # "a" = append
    file_handler.setFormatter(formatter)

    # Setup root-logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()  # Rensa gamla handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    logging.debug(f"Logging initialized (debug={debug}, file={logfile})")
