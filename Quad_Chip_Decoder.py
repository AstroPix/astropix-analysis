import binascii
import numpy as np
import tqdm
from datetime import datetime
import argparse



''' this script takes the .log files of a source run and returns the .csv into the same directory 
filtering function works to fix common issues seen with decoding raw lines from the .log file'''

def decode_astep_hit(hit, i:int, dec_ord, printer:bool = False):
        astep_header=int(hit[:2],16)
        layer_id=int(hit[2:4],16)
        v3_hit=binascii.unhexlify(hit[4:14])
        fpga_time_stamp=int(hit[14:],16)
        
        
        """
        Decode 5byte Frames from AstroPix 3

        Byte 0: Header      Bits:   7-3: ID
                                    2-0: Payload
        Byte 1: Location            7: Col
                                    6: reserved
                                    5-0: Row/Col
        Byte 2: Timestamp
        Byte 3: ToT MSB             7-4: 4'b0
                                    3-0: ToT MSB
        Byte 4: ToT LSB

        :param list_hists: List with all hits
        i: int - Readout number

        :returns: Dataframe with decoded hits
        """

        header, location, timestamp, tot_msb, tot_lsb = v3_hit

        chip_id          = header >> 3
        payload     = header & 0b111
        col         = location >> 7 & 1
        location   &= 0b111111
        timestamp   = timestamp
        tot_msb    &= 0b1111
        tot_lsb     = int(v3_hit[4])
        tot_total   = (tot_msb << 8) + tot_lsb
        tot_us      = (tot_total * 10) / 1000.0 # the 10 here is the self._sampleclock_period_ns

        # hit_pd.append([i,id, payload, location, col, timestamp, tot_msb, tot_lsb, tot_total, tot_us, time.time()])
        hit_pd=[dec_ord, i, layer_id, chip_id, payload, location, col, timestamp, tot_msb, tot_lsb, tot_total, tot_us, fpga_time_stamp]
                
        return hit_pd




def find_all_indexes(text, substring):
    indexes = []
    start_index = 0
    while True:
        index = text.find(substring, start_index)
        if index == -1:
            break
        indexes.append(index)
        start_index = index + 1
    return np.array(indexes)

def diff_consecutive(input_list):
    return_list=[input_list[i+1] - input_list[i] for i in range(len(input_list) - 1)]
    return np.array(return_list)


def count_lines(filename):
    with open(filename, 'r') as file:
        return sum(1 for line in file)

def main(args):

    start_time=datetime.now()
    print(f'\nStart Time: {datetime.strftime(start_time,"%Y-%m-%d   %H:%M:%S")}\n')

    full_file_name=args.name


    total_lines=count_lines(full_file_name)
    print(f'{full_file_name} \n Lines={total_lines}\n')

    read_file=open(full_file_name,'r')
    write_file=open(full_file_name.replace('.log','.csv'),'w')

    row_0_list=['dec_ord', 'readout', 'layer', 'chipID', 'payload', 'location', 'isCol', 'timestamp', 'tot_msb', 'tot_lsb', 'tot_total', 'tot_us', 'fpga_ts'] # make 'dec_ord' ''
    row_0_string=','.join(row_0_list)

    write_file.write(f'{row_0_string}\n')

    stored_split_first_part=None

    progress_bar=tqdm.tqdm(total=total_lines)
    line_counter=0
    for full_line in read_file:
        progress_bar.update(1)
        line=full_line.split('INFO:')[1]
        if line[0]=='b':
            full_data_string=line[2:-1]
            if stored_split_first_part is not None:
                full_data_string=stored_split_first_part+full_data_string

            no_quote_list=[] #need to figure out why this is necessary in the first place
            for j in full_data_string.split("\'"):
                if j!="":
                    no_quote_list.append(j)
            no_quote_string=''.join(no_quote_list)

            no_ff_list=[]
            for j in no_quote_string.split('ffff'): 
                if j != '':
                    no_ff_list.append(j)
            no_ff_string=''.join(no_ff_list)

            list_of_right_header_indexes=find_all_indexes(no_ff_string,'0a01')
            difference_list=diff_consecutive(list_of_right_header_indexes)
            mask_list=difference_list>=22
            mask_list=np.append(mask_list,True)
            list_of_right_header_indexes=list_of_right_header_indexes[mask_list]

            if list_of_right_header_indexes[-1]+22>len(no_ff_list):
                stored_split_first_part=no_ff_string[list_of_right_header_indexes[-1]:]
                no_ff_string=no_ff_string[:list_of_right_header_indexes[-1]]
                list_of_right_header_indexes=list_of_right_header_indexes[:-1]
            else:
                stored_split_first_part=None

            for dec_ord, one_right_header_index in enumerate(list_of_right_header_indexes):
                hit=no_ff_string[one_right_header_index:one_right_header_index+22]
                decoded_hit=decode_astep_hit(hit,line_counter,dec_ord)
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


    parser.add_argument
    args = parser.parse_args()
    main(args)