import binascii
import decode_copy
import tqdm
from datetime import datetime
import argparse



''' this script takes the .log files of a source run and returns the .csv into the same directory 
filtering function works to fix common issues seen with decoding raw lines from the .log file'''

def Filter_Function(String,chip_version):
    if chip_version==4:
        header_string='e0'
        characters_per_hit=16
    elif chip_version==3:
        header_string='20'
        characters_per_hit=10

    Good_List=[]

    if characters_per_hit<=len(String)<=1000: # lower bound to filter out cutoff hits, upper bound to ignore the first few lines of a .log that are usually nonsense
        if len(String)==characters_per_hit and String[0:2]==header_string: # normal string decoding, looking for header byte 'e0'
            Good_List.append(String)
        elif String[-characters_per_hit:-(characters_per_hit-2)]==header_string: # catches the case of two back to back hits in the same string with no 'bc' idle byte in between
            good_part=String[-characters_per_hit:]  # this filter should also catch the case of one hit partially writing over another, leading the cutoff hit to get filtered out
            Good_List.append(good_part)
            other_part=String[:-characters_per_hit]
            Good_List=Good_List+Filter_Function(other_part,chip_version)
        elif String[-2:]=='bc': # catches the case of two hits in the same string with only one 'bc' idle byte in between
            other_part=String[:-2]
            Good_List=Good_List+Filter_Function(other_part,chip_version)
    return Good_List

def count_lines(filename):
    with open(filename, 'r') as file:
        return sum(1 for line in file)

def main(args):

    start_time=datetime.now()
    print(f'\nStart Time: {datetime.strftime(start_time,"%Y-%m-%d   %H:%M:%S")}\n')

    full_file_name=args.name
    version_number=args.chipVer

    if version_number==4:
        Bytes_per_hit=8
    elif version_number==3:
        Bytes_per_hit=5

    Characters_per_hit=2*Bytes_per_hit

    total_lines=count_lines(full_file_name)
    print(f'{full_file_name} \n Lines={total_lines}\n')

    read_file=open(full_file_name,'r')
    write_file=open(full_file_name.replace('.log','.csv'),'w')

    if version_number==4:
        row_0_list=['dec_ord','id', 'payload', 'row', 'col', 'ts1', 'tsfine1', 'ts2', 'tsfine2', 'tsneg1', 'tsneg2', 'tstdc1', 'tstdc2', 'ts_dec1', 'ts_dec2', 'tot_us']
    elif version_number==3:
        row_0_list=['dec_ord','readout', 'Chip ID', 'payload', 'location', 'isCol', 'timestamp', 'tot_msb', 'tot_lsb', 'tot_total', 'tot_us']
    row_0_string=','.join(row_0_list)

    write_file.write(f'{row_0_string}\n')

    stored_split_first_part=None

    progress_bar=tqdm.tqdm(total=total_lines)
    line_counter=0
    for line in read_file:
        progress_bar.update(1)
        if line[0].isdigit(): # the first character of a data line should be a digit, filters out the first  7 lines of config settings
            full_data_string=line.split('\t')[-1][2:-2]
            no_ff_list=[]
            for j in full_data_string.split('ffff'): 
                if j != '':
                    no_ff_list.append(j)
            no_ff_string=''.join(no_ff_list)
            if stored_split_first_part is not None:
                no_ff_string=stored_split_first_part+no_ff_string
            split_bc_strings=[]
            for i in no_ff_string.split('bcbc'): # splits on 'bcbc' idle bytes to avoid splitting on 'bc' that may appear in a hit
                if i!='':
                    split_bc_strings.append(i)

            if len(split_bc_strings)>1 and len(split_bc_strings[-1])<Characters_per_hit: # this helps fix the split hit issue
                stored_split_first_part=split_bc_strings[-1]
                split_bc_strings=split_bc_strings[:-1]
            else:
                stored_split_first_part=None

            all_filtered_hits=[]
            for one_string in split_bc_strings:
                all_filtered_hits=all_filtered_hits+Filter_Function(one_string, chip_version=version_number)

            decode_object=decode_copy.Decode(bytesperhit=Bytes_per_hit)
            dec_order_counter=0
            for not_decoded_hit in all_filtered_hits:
                rawdata=list(binascii.unhexlify(not_decoded_hit))
                list_hits=decode_object.hits_from_readoutstream(rawdata, reverse_bitorder=True)
                if version_number==4:
                    decoded_hits_list=decode_object.decode_astropix4_hits(list_hits)
                elif version_number==3:
                    decoded_hits_list=decode_object.decode_astropix3_hits(list_hits,i=line_counter)
                for decoded_hit in decoded_hits_list:
                    decoded_hit=[dec_order_counter]+decoded_hit
                    dec_order_counter+=1 # the correct implimentation of the dec_ord, counting up for each hit in a string
                    write_string=','.join(str(x) for x in decoded_hit)
                    write_file.write(f'{write_string}\n')
            line_counter+=1

    read_file.close()
    write_file.close()
    finish_time=datetime.now()
    elapsed_time=finish_time-start_time
    print(f'Finish Time: {datetime.strftime(finish_time,"%Y-%m-%d   %H:%M:%S")} \n Time Elapsed: {elapsed_time.days} days, {elapsed_time.seconds // 3600} hours, {(elapsed_time.seconds % 3600) // 60} minutes, {elapsed_time.seconds % 60} seconds')

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Astropix Driver Code')
    parser.add_argument('-n', '--name', required=True,
                    help='Name of input .log file')

    parser.add_argument('-V', '--chipVer', required=True, type=int,
                    help='Chip version - provide an int')

    parser.add_argument
    args = parser.parse_args()
    main(args)