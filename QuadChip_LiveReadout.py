
import numpy as np
import struct
import argparse
import re
import time
from datetime import datetime, timezone
from send_data_to_influxdb import Influx_Write
import binascii
import tqdm


##################################################################################################################################################

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

##################################################################################################################################################

def find_all_indexes(text, substrings):
    indexes = []
    if type(substrings) is not list:
        substrings=[substrings]

    for substring in substrings:
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

##################################################################################################################################################

def Decode_and_Write_Line(full_line,stored_split_first_part,line_counter,write_file, is_bin=False):
    decoded_list=[]
    length_decoded=0
    if is_bin:
        if stored_split_first_part is not None:
                full_line=stored_split_first_part+full_line
        
        list_of_right_header_indexes=find_all_indexes(full_line,[bytes.fromhex("0a01"),bytes.fromhex("0a02"),bytes.fromhex("0a03")])
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
                    if len(hit)==11: # to fix a problem where a cutoff hit gets passed through, wrong length happens < 0.0001% of the time
                        decoded_hit=decode_astep_hit(hit,0,0,is_bin=True) #currently all readout number and decode order set to 0
                        write_string=','.join(str(x) for x in decoded_hit)
                        write_file.write(f'{write_string}\n')
                        decoded_list.append(decoded_hit)
                        length_decoded+=len(hit)




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

            list_of_right_header_indexes=find_all_indexes(no_ff_string,['0a01','0a02','0a03'])
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
                    if len(hit)==22:
                        decoded_hit=decode_astep_hit(hit,line_counter,dec_ord)
                        write_string=','.join(str(x) for x in decoded_hit)
                        write_file.write(f'{write_string}\n')
                        decoded_list.append(decoded_hit)


        line_counter+=1
    return decoded_list, stored_split_first_part, line_counter, length_decoded

##################################################################################################################################################

def live_decode(data,write_file,influx_obj,stored_split_first_part,line_counter, grid_counts):
    
    # pkt_indices = identify_index(data)
    # packages = [data[i:j] for i,j in zip([0] + pkt_indices, pkt_indices + [None])][1:]

    # for p in packages:
    #     # Decode_and_Write_Line(full_line,stored_split_first_part,line_counter,write_file, is_bin=False)
        
    #     decoded_hit = Decode_and_Write_Line(p)
    #     # print(f'Timestamp from fsw {decoded_hit[0]}, {type(decoded_hit[0])}')

    #     decoded_string=','.join(str(x) for x in decoded_hit)
    #     write_file.write(f'{decoded_string}\n')
    #     influx_obj.write_unmatched_tot_point(self, layer, chip, location, isCol, ToT, timestamp) ###############################

 
    decoded_hit_list, stored_split_first_part, line_counter, single_chunk_length_decoded = Decode_and_Write_Line(data,stored_split_first_part,line_counter,write_file,is_bin=True) #send data here
    #decoded_string=','.join(str(x) for x in decoded_hit_list)
    #print(decoded_hit_list)
    for x in decoded_hit_list:
        if x[3]>=0 and x[3]<=3:
            if x[5]>=0 and x[5]<=34:
                write_file.write(f'{str(x)}\n')
                influx_obj.write_unmatched_tot_point(layer=x[2],
                                                        chip=x[3],
                                                        location=x[5],
                                                        isCol=x[6],
                                                        ToT=x[11])
                if x[6]==0:
                    grid_counts[int(x[3]),int(x[5]),:] += 1
                if x[6]==1:
                    grid_counts[int(x[3]),:,int(x[5])] += 1

    for chip_idx in range(4):
        for row_idx in range(35):
            for col_idx in range(35):
                influx_obj.points.append({
                    "measurement": "activity_grid",
                    "tags":{
                        "live_chip": str(chip_idx),
                        "live_row": str(row_idx),
                        "live_col": str(col_idx),
                    },
                    "fields": {
                        "live_value": int(grid_counts[chip_idx, row_idx, col_idx])
                    }
                })

                    #print(influx_obj.points)
                    #print("N points:", len(influx_obj.points))
                    #for p in influx_obj.points[:5]:
                        #print(p.to_line_protocol())
                #influx_obj.send_points_to_influx()
    return stored_split_first_part, line_counter, grid_counts



def read_from_offset(file_path, bytes_to_skip):
    try:
        with open(file_path, 'rb') as file:
            file.seek(bytes_to_skip)
            return file.read()
    except OSError as e:
        print(f'Error reading file: {e}')
        return b''

    
##################################################################################################################################################
##################################################################################################################################################
##################################################################################################################################################

if __name__=='__main__':
    parser = argparse.ArgumentParser(
        description="Decode housekeeping data for astep generated by astep-fw and writes to .csv file")

    parser.add_argument(
        'filename',
        type=str,
        help='Input filename to decode, required to run'
    )

    args = parser.parse_args()
    # main(args)



if __name__=='__main__':
    url = 'http://localhost:8086'
    # bucket = 'ASTEP_Testing_2'
    # bucket = 'ASTEP_Temperature_Chamber_Data_Test'
    # bucket = 'ASTEP_Temperature_Chamber_Data_Test_2'
    bucket = 'ASTEP_Temperature_Chamber_Data_05-06-2026'
    #bucket = 'ASTEP_QuadChip_LiveReadout'          # should be the same as hk bucket

    org = 'ASTEP'
    token='ZaAOdbYZXQtsYMSlSRmr4kNaJPsJq2OTlqUgZvkb_5Qk85_DF_8ZZ65K3Zr9w6QzkPTMKu2nA5_78Bzh35kFaA=='


    write_file=open(args.filename.replace('.bin','.csv'),'w')
    header = ['dec_ord', 'readout', 'layer', 'chipID', 'payload', 'location', 'isCol', 'timestamp', 'tot_msb', 'tot_lsb', 'tot_total', 'tot_us', 'fpga_ts']
    headerstring = ','.join(header)
    write_file.write(f'{headerstring}\n')


    influx_object=Influx_Write(url=url,org=org,bucket=bucket,api_token=token, write_precision='NS')
    gobool = True
    running_file_length=0
    
    start_time=datetime.now()
    print(f'\nStart Time: {datetime.strftime(start_time,"%Y-%m-%d   %H:%M:%S")}\n')

    stored_split_first_part=None
    line_counter=0
    grid_counts = np.zeros((4,35,35),dtype=int)
    while gobool:
        try:
            time.sleep(10)
            data=read_from_offset(args.filename, running_file_length)
            print(f'decoding data of length: {len(data)}')
            running_file_length+=len(data)
            if data:
                stored_split_first_part, line_counter, grid_counts = live_decode(data,write_file,influx_object, stored_split_first_part, line_counter, grid_counts)
                influx_object.send_points_to_influx()
        except KeyboardInterrupt:
            gobool = False
            write_file.close()










   