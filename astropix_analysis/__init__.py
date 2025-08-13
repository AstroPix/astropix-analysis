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

from pathlib import Path
import subprocess
import sys

from loguru import logger

from ._version import __version__ as __base_version__


PACKAGE_NAME = 'astropix-analysis'
ASTROPIX_ANAYSIS_URL = 'https://github.com/AstroPix/astropix-analysis'


# pylint: disable=protected-access
LOGGING_LEVELS = tuple(level for level in logger._core.levels)
DEFAULT_LOGGING_LEVEL = 'DEBUG'


def reset_logger(level: str = DEFAULT_LOGGING_LEVEL) -> int:
    """Minimal configuration facility for the loguru logger.

    A few remarks about the loguru internals. In order to keep the API clean, the
    author of the library made the deliberate decision not to allow to change handlers,
    so that the preferred way to change the logger configuration is to remove all the
    existing handlers and start from scratch---this is exactly what we are doing here.

    Also note that whenever you add a new handler, you get back an ID that can be used
    to remove the handler later on. The default handler (which we get rid of at the
    first call to this function) is guaranteed to have ID 0.

    Arguments
    ---------
    level : str
        The minimum logging level to be used by the logger. Defaults to 'DEBUG'.
        Other possible values are 'INFO', 'WARNING', 'ERROR', and 'CRITICAL'.

    Returns
    -------
    int
        The ID of the handler that was added.
    """
    # Remove all existing handlers.
    logger.remove()
    # Create a plain, terminal-based logger.
    fmt = '>>> <level>[{level}] {message}</level>'
    return logger.add(sys.stderr, level=level, colorize=True, format=fmt)


reset_logger()


# Basic package structure.
ASTROPIX_ANALYSIS_ROOT = Path(__file__).parent
ASTROPIX_ANALYSIS_BASE = ASTROPIX_ANALYSIS_ROOT.parent
ASTROPIX_ANALYSIS_TESTS = ASTROPIX_ANALYSIS_BASE / 'tests'
ASTROPIX_ANALYSIS_TESTS_DATA = ASTROPIX_ANALYSIS_TESTS / 'data'


def _git_info() -> str:
    """If we are in a git repo, we want to add the necessary information to the
    version string.

    This will return something along the lines of ``+gf0f18e6.dirty``.
    """
    # pylint: disable=broad-except
    try:
        # Retrieve the git short sha.
        sha = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ASTROPIX_ANALYSIS_TESTS,
            stderr=subprocess.DEVNULL
            ).decode().strip()
        suffix = f'+g{sha}'
        # If we have uncommitted changes, append a `.dirty` to the version suffix.
        dirty = subprocess.call(
            ["git", "diff", "--quiet"],
            cwd=ASTROPIX_ANALYSIS_BASE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
            ) != 0
        if dirty:
            suffix = f'{suffix}.dirty'
        return suffix
    except Exception:
        return ''


__version__ = f'{__base_version__}{_git_info()}'


def start_message() -> str:
    """Return a simple start message for the applications.
    """
    return f"""
    Welcome to {PACKAGE_NAME} {__version__}

    Copyright (C) 2025, the astropix team.

    {PACKAGE_NAME} comes with ABSOLUTELY NO WARRANTY.
    This is free software, and you are welcome to redistribute it under certain
    conditions. See the LICENSE file for details.

    Visit {ASTROPIX_ANAYSIS_URL} for more information.
    """
