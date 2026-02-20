import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import scipy as sp


def find_all_good_header_indexes(bytes):
    filter_bitstring = '11111111_11111000_00000111'.replace('_', '')
    filter = int(filter_bitstring, 2).to_bytes(3,'big')
    b'\r\x00\x07'

    data = np.frombuffer(bytes, dtype=np.uint8)
    x = np.frombuffer(filter, dtype=np.uint8)
    b = np.frombuffer(b'\r\x00\x07', dtype=np.uint8)

    # Create sliding windows of shape (N-2, 3)
    windows = np.lib.stride_tricks.sliding_window_view(data, 3)

    # Apply condition
    matches = np.all((windows & x) == b, axis=1)

    indices = np.nonzero(matches)[0]

    return indices


filename='Runs_Injection/New_ASTEP_FW_Binaries_2-6-26/v4_20260206-142305.bin'
with open(filename, 'rb') as stream:
    # data=stream.readlines()
    data=stream.read()


hit_indices=find_all_good_header_indexes(data)
end_indices=np.append(hit_indices[1:],len(data))


for start_index,next_start_index in zip(hit_indices,end_indices):
    print(data[start_index:next_start_index].hex())


#### for now going to check that the start is 0d and then 01, 02, or 03, then xxxxx111 for any ChipID and astropix payload=7

# byte_filter=11111111_11111000_00000111



