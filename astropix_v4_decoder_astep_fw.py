import os
import tqdm
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import scipy as sp
import argparse
from datetime import datetime

def get_bin_file_size(filename):
    with open(filename, 'rb') as f:
        f.seek(0, 2)  # Move to the end of the file
        size = f.tell()
        return size

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

def header_length_check(hit, print_bool:bool = False, last_hit_in_chunk_bool=False):
    '''
    checks for correct length of hit based on header
    '''
    return_bool=True

    length_from_header=int(hit[0])+1
    hit_split_across_chunks=None
    if length_from_header!=len(hit) and not last_hit_in_chunk_bool:
        return_bool=False
    
        if len(hit)>=3:
            length_from_astropix=int(hit[2]) & 0b111
            if len(hit)<length_from_astropix+2+1 and print_bool: # plus 2 for FPGA wrapper start and plus 1 for astropix header byte
                    print(f'Incorrect Astropix Length: {hit.hex()}')
            elif print_bool:
                print(f'Incorrect FPGA Length: {hit.hex()}') # if hit has enough for astropix hit but is too long for fpga length
        elif print_bool:
            print(f'Incorrect FPGA Length: {hit.hex()}') # if hit is too short for fpga length and doen't have astropix header (this really shouldn't happen becuause of byte filter)

    elif length_from_header!=len(hit) and last_hit_in_chunk_bool: # takes care of the problem of one hit being split across data read ins
        return_bool=False
        hit_split_across_chunks=hit
    

    return return_bool, hit_split_across_chunks

def main(args):
    chunk_size=1024


    start_time=datetime.now()
    print(f'\nStart Time: {datetime.strftime(start_time,"%Y-%m-%d   %H:%M:%S")}\n')

    bin_file_size=get_bin_file_size(args.filename)

    if bin_file_size>=105000:
        print(f'{args.filename} \n Size of File: {round(bin_file_size/1024/1024,2)} MB\n')
    else:
        print(f'{args.filename} \n Size of File: {round(bin_file_size/1024,2)} kB\n')

    progress_bar=tqdm.tqdm(total=int(bin_file_size/chunk_size)+1)

    read_file=open(args.filename,'rb')
    write_file=open(args.filename.replace('.bin','.csv'),'w')

    row_0_list=['pack_len', 'layer', 'chipID', 'payload', 'row', 'col', 
                'tsneg1', 'ts1', 'tsfine1', 'tstdc1', 'tsneg2', 'ts2', 
                'tsfine2', 'tstdc2', 'ts1_dec', 'ts2_dec', 'tot_us', 'fpga_ts'] # no decode order or readout number here with just binary being read, I think
    row_0_string=','.join(row_0_list)
    write_file.write(f'{row_0_string}\n')

    retained_hit_split_across_chunks=None

    # main running loop
    try:
        while True:
            chunk = read_file.read(chunk_size)
            if not chunk:
                break
            
            if retained_hit_split_across_chunks is not None: # takes care of the problem of one hit being split across data read ins
                chunk=retained_hit_split_across_chunks+chunk

            hit_indices=find_all_good_header_indexes(chunk)
            end_indices=np.append(hit_indices[1:],len(chunk))

            for start_index,next_start_index in zip(hit_indices,end_indices):
                last_hit_in_chunk_bool = start_index==hit_indices[-1]

                single_hit=chunk[start_index:next_start_index]
                single_hit_hex=single_hit.hex()
                if header_length_check(single_hit, print_bool=True, last_hit_in_chunk_bool=last_hit_in_chunk_bool)[0]: # right now the only check I know to run, will update with more robust filter function as edge cases are found
                        decoded_hit=decode(single_hit)
                        decoded_hit_string=','.join(str(x) for x in decoded_hit)
                        write_file.write(f'{decoded_hit_string}\n')

                if last_hit_in_chunk_bool: # takes care of the problem of one hit being split across data read ins
                    header_length_check_bool, hit_split_across_chunks = header_length_check(single_hit)
                    if header_length_check_bool:
                        decoded_hit=decode(single_hit)
                        decoded_hit_string=','.join(str(x) for x in decoded_hit)
                        write_file.write(f'{decoded_hit_string}\n')
                    else:
                        retained_hit_split_across_chunks=hit_split_across_chunks

        
            progress_bar.update(1)
    except KeyboardInterrupt as KE:
        print(f'KeyboardInterrupt: {KE}')

    read_file.close()
    write_file.close()


if __name__=='__main__':
    parser = argparse.ArgumentParser(
        description="Decode astropix v4 data from astep-fw running, writes .csv file with same name as input file"
    )

    parser.add_argument(
        'filename',
        type=str,
        help='Input filename to decode, required to run'
    )

    args = parser.parse_args()

    main(args)



