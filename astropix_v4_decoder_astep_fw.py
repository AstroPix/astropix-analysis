import tqdm
import numpy as np
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

def decode(hit, sample_clock_period_ns: int = 5, use_negedge_ts: bool = True): # sample_clock_period_ns 5 or 25?
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

def find_first_good_header_index(byte_data):
    # for now going to check that the start is 0d and then 01, 02, or 03, then xxxxx111 for any ChipID and astropix payload=7
    # byte_filter = 11111111_11111000_00000111
    filter_bitstring = '11111111_11111000_00000111'.replace('_', '')
    mask = int(filter_bitstring, 2).to_bytes(3, 'big')
    target = b'\r\x00\x07'

    data = np.frombuffer(byte_data, dtype=np.uint8)
    mask_arr = np.frombuffer(mask, dtype=np.uint8)
    target_arr = np.frombuffer(target, dtype=np.uint8)

    n = len(data)

    for i in range(n - 2): # Stops at first match
        if ((data[i:i+3] & mask_arr) == target_arr).all():
            return i

    return -1  # no match

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

            good_index=find_first_good_header_index(chunk)
            continue_bool=True
            while continue_bool:
                len_hit=chunk[good_index]
                decoded_hit=decode(chunk[good_index:good_index+len_hit+1])
                decoded_hit_string=','.join(str(x) for x in decoded_hit)
                write_file.write(f'{decoded_hit_string}\n')
                good_index+=((len_hit+1)+find_first_good_header_index(chunk[(good_index+len_hit+1):]))
                if len(chunk[good_index:])<len_hit:
                    retained_hit_split_across_chunks=chunk[good_index:]
                    continue_bool=False
                if good_index==-1:
                    continue_bool=False

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
