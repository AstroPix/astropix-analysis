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


# def test_plot_file():
#     """Basic test plotting the content of the sample binary file.

#     """
#     run_id = '20250507_085829'
#     file_name = f'{run_id}_data.csv'
#     file_path = os.path.join(os.path.dirname(__file__), 'data', run_id, file_name)
#     chip_id, payload, row, column, ts_neg1, ts_coarse1, ts_fine1, ts_tdc1, ts_neg2, \
#         ts_coarse2, ts_fine2, ts_tdc2, ts_dec1, ts_dec2, tot_us, readout_id, timestamp = \
#         np.loadtxt(file_path, delimiter=',', unpack=True)
#     dt = np.diff(timestamp) / 1.e6

#     plt.figure('TOT')
#     plt.hist(tot_us, bins=25)
#     plt.xlabel('TOT [$\\mu$s]')

#     plt.figure('Time differences')
#     plt.hist(dt, bins=25)
#     plt.xlabel('$\\Delta$T [ms]')
