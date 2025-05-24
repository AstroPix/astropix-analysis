import binascii
import numpy as np
import tqdm
from datetime import datetime
import argparse



''' this script takes the .log files of a source run and returns the .csv into the same directory 
filtering function works to fix common issues seen with decoding raw lines from the .log file'''

def decode_astep_hit(hit, i:int, dec_ord, printer:bool = False,is_bin=False):
        if is_bin:
            astep_header=int.from_bytes(hit[:1], 'big')
            layer_id=int.from_bytes(hit[1:2], 'big')
            v3_hit=hit[2:7]
            fpga_time_stamp=int.from_bytes(hit[7:], 'little')


        else:
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
    
def get_bin_file_size(filename):
    with open(filename, 'rb') as f:
        f.seek(0, 2)  # Move to the end of the file
        size = f.tell()
        return size

def Decode_and_Write_Line(full_line,stored_split_first_part,line_counter,write_file, is_bin=False):
    decoded_list=[]
    if is_bin:
        if stored_split_first_part is not None:
                full_line=stored_split_first_part+full_line
        
        search_value_bytes = bytes.fromhex("0a01")
        start = 0
        list_of_right_header_indexes=[]
        while True:
            index = full_line.find(search_value_bytes, start)
            if index == -1:
                break
            start = index + 1
            list_of_right_header_indexes.append(index)
        list_of_right_header_indexes=np.array(list_of_right_header_indexes)
        if list_of_right_header_indexes.size!=0:
            difference_list=diff_consecutive(list_of_right_header_indexes)
            mask_list=difference_list>=11
            mask_list=np.append(mask_list,True)
            # print(mask_list)
            # print(list_of_right_header_indexes)
            list_of_right_header_indexes=list_of_right_header_indexes[mask_list]


            if list_of_right_header_indexes[-1]+11>len(full_line):
                stored_split_first_part=full_line[list_of_right_header_indexes[-1]:]
                full_line=full_line[:list_of_right_header_indexes[-1]]
                list_of_right_header_indexes=list_of_right_header_indexes[:-1]
            else:
                stored_split_first_part=None

            for decode_index, one_right_header_index in enumerate(list_of_right_header_indexes):
                    hit=full_line[one_right_header_index:one_right_header_index+11]
                    decoded_hit=decode_astep_hit(hit,0,0,is_bin=True) #currently all readout number and decode order set to 0
                    write_string=','.join(str(x) for x in decoded_hit)
                    write_file.write(f'{write_string}\n')
                    decoded_list.append(decoded_hit)




    else:
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
            if len(list_of_right_header_indexes)>0:
                difference_list=diff_consecutive(list_of_right_header_indexes)
                mask_list=difference_list>=22
                mask_list=np.append(mask_list,True)
                list_of_right_header_indexes=list_of_right_header_indexes[mask_list]

                if list_of_right_header_indexes[-1]+22>len(no_ff_string):
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
                    decoded_list.append(decoded_hit)


        line_counter+=1
    return decoded_list, stored_split_first_part, line_counter

def main(args):

    start_time=datetime.now()
    print(f'\nStart Time: {datetime.strftime(start_time,"%Y-%m-%d   %H:%M:%S")}\n')

    full_file_name=args.name
    is_bin_file=args.bin

    if is_bin_file:
        bin_file_size=get_bin_file_size(full_file_name)
        # print(f'{full_file_name} \n Size of File={bin_file_size/1024}KB\n')
        print(f'{full_file_name} \n Size of File={round(bin_file_size/1024/1024,2)}MB\n')
    else:
        total_lines=count_lines(full_file_name)
        print(f'{full_file_name} \n Lines={total_lines}\n')

    if is_bin_file:
        read_file=open(full_file_name,'rb')
    else:
        read_file=open(full_file_name,'r')
    if is_bin_file:
        write_file=open(full_file_name.replace('.bin','.csv'),'w')
    else:
        write_file=open(full_file_name.replace('.log','.csv'),'w')

    row_0_list=['dec_ord', 'readout', 'layer', 'chipID', 'payload', 'location', 'isCol', 'timestamp', 'tot_msb', 'tot_lsb', 'tot_total', 'tot_us', 'fpga_ts'] # make 'dec_ord' ''
    row_0_string=','.join(row_0_list)

    write_file.write(f'{row_0_string}\n')

    stored_split_first_part=None
    line_counter=0
    chunk_size=1024

    if is_bin_file:
        progress_bar=tqdm.tqdm(total=int(bin_file_size/chunk_size)+1)
    if not is_bin_file:
        progress_bar=tqdm.tqdm(total=total_lines)

    if is_bin_file:
        while True:
            chunk = read_file.read(chunk_size)
            if not chunk:
                break
            decoded_hit_list, stored_split_first_part, line_counter = Decode_and_Write_Line(chunk,stored_split_first_part,line_counter,write_file,is_bin=True)#send data here
            progress_bar.update(1)
    else: 
        for full_line in read_file:#increment line_counter
            progress_bar.update(1)
        #read_file.read(line_counter) ??
        #data=read_file.read(...)
            decoded_hit_list, stored_split_first_part, line_counter = Decode_and_Write_Line(full_line,stored_split_first_part,line_counter,write_file,is_bin=False)#send data here

    read_file.close()
    write_file.close()
    finish_time=datetime.now()
    elapsed_time=finish_time-start_time
    print(f'Finish Time: {datetime.strftime(finish_time,"%Y-%m-%d   %H:%M:%S")} \n Time Elapsed: {elapsed_time.days} days, {elapsed_time.seconds // 3600} hours, {(elapsed_time.seconds % 3600) // 60} minutes, {elapsed_time.seconds % 60} seconds')

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Offline Quadchip Decoder')
    parser.add_argument('-n', '--name', required=True,
                    help='Name of input .log file')
    parser.add_argument('-b','--bin', required=False, type=bool, default=False,
                        help='True if using a binary file as the input, default false for .log file as input')


    parser.add_argument
    args = parser.parse_args()
    main(args)
