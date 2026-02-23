import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import scipy as sp
import argparse


def gray_to_dec(gray: int) -> int:
        """
        Decode Gray code to decimal

        :param gray: Gray code

        :returns: Decoded decimal
        """
        bits = gray >> 1
        while bits:
            gray ^= bits
            bits >>= 1
        return gray

def decode(hit, sample_clock_period_ns: int = 5, use_negedge_ts: bool = True): #sample_clock_period_ns 5 or 25?
    pack_len    = int(hit[0])
    layer       = int(hit[1])
    id          = int(hit[2]) >> 3
    payload     = int(hit[2]) & 0b111
    row         = int(hit[3]) >> 3
    col         = ((int(hit[3]) & 0b111) << 2) + (int(hit[4]) >> 6)
    tsneg1      = (int(hit[4]) >> 5) & 0b1
    ts1         = ((int(hit[4]) & 0b11111) << 9) + (int(hit[5]) << 1) + (int(hit[6]) >> 7)
    tsfine1     = (int(hit[6]) >> 4) & 0b111
    tstdc1      = ((int(hit[6]) & 0b1111) << 1) + (int(hit[7]) >> 7)

    tsneg2      = (int(hit[7]) >> 6) & 0b1
    ts2         = ((int(hit[7]) & 0b111111) << 8) + int(hit[8])
    tsfine2     = (int(hit[9]) >> 5) & 0b111
    tstdc2      = int(hit[9]) & 0b11111

    ts1_dec = gray_to_dec((ts1 << 3) + tsfine1) << 1 | (tsneg1 & use_negedge_ts)
    ts2_dec = gray_to_dec((ts2 << 3) + tsfine2) << 1 | (tsneg2 & use_negedge_ts)

    if ts2_dec > ts1_dec:
        tot_total = ts2_dec - ts1_dec
    else:
        tot_total = 2**18 - 1 + ts2_dec - ts1_dec
    tot_us      = (tot_total * sample_clock_period_ns)/1000.0
    fpga_ts     = int.from_bytes(hit[10:14], 'big')
    hit_data=[pack_len, layer, id, payload, row, col, tsneg1, ts1, tsfine1, tstdc1, tsneg2, ts2, tsfine2, tstdc2, ts1_dec, ts2_dec, tot_us, fpga_ts]
    return hit_data

def find_all_good_header_indexes(bytes):
    # for now going to check that the start is 0d and then 01, 02, or 03, then xxxxx111 for any ChipID and astropix payload=7
    # byte_filter=11111111_11111000_00000111
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


def main(args):
    with open(args.filename, 'rb') as stream:
        # data=stream.readlines()
        data=stream.read()


    hit_indices=find_all_good_header_indexes(data)
    end_indices=np.append(hit_indices[1:],len(data))


    for start_index,next_start_index in zip(hit_indices,end_indices):
        single_hit=data[start_index:next_start_index]
        single_hit_hex=single_hit.hex()
        try:
            decoded_hit=decode(single_hit)
            print([decoded_hit[4],decoded_hit[5],decoded_hit[-2]])
            # print(decoded_hit)
        except IndexError as IE:
            print(f'IndexError: {IE}')



if __name__=='__main__':
    parser = argparse.ArgumentParser(
        description="Decode astropix v4 data from astep-fw running"
    )

    parser.add_argument(
        'filename',
        type=str,
        help='Input filename to decode, required to run'
    )

    args = parser.parse_args()

    main(args)



