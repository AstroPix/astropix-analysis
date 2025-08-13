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

"""Unit tests for the legacy module.
"""

from astropix_analysis import ASTROPIX_ANALYSIS_TESTS_DATA
from astropix_analysis.legacy import AstroPixLogFile


SAMPLE_RUN_ID = '20250722_094253'


def test_log_file():
    """Read and iterate over a log file.
    """
    file_path = ASTROPIX_ANALYSIS_TESTS_DATA / SAMPLE_RUN_ID / 'threshold_40mV_20250722-094253.log'
    with AstroPixLogFile(file_path) as input_file:
        header = input_file.header
        print(header)
        assert header.options().get('threshold') == 40.
        assert header.options().get('vinj') == 300.
        for readout_id, readout_data in input_file:
            assert readout_id == 0
            assert isinstance(readout_data, str)
            break
