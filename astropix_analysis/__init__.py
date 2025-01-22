# Copyright (C) 2025 the astropix team.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


"""System-wide facilities.
"""

import os
from pathlib import Path
import sys

from loguru import logger

# Basic package structure.
ASTROPIX_ANALYSIS_ROOT = Path(__file__).parent
ASTROPIX_ANALYSIS_BASE = ASTROPIX_ANALYSIS_ROOT.parent
ASTROPIX_DATA = None
try:
    ASTROPIX_DATA = os.environ["ASTROPIX_DATA"]
except:
    logger.warning("No ASTROPIX_DATA env path defined")
