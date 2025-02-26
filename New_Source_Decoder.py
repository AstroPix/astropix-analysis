import binascii
import decode_copy
import decode
import subprocess
import tqdm
from datetime import datetime


''' this script takes the .log files of a source run and returns the .csv into the same directory 
filtering function works to fix common issues seen with decoding raw lines from the .log file'''

def Filter_Function(String):
    Good_List=[]
    if 16<=len(String)<=1000: # lower bound to filter out cutoff hits, upper bound to ignore the first few lines of a .log that are usually nonsense
        if len(String)==16 and String[0:2]=='e0': # normal string decoding, looking for header byte 'e0'
            Good_List.append(String)
        elif String[-16:-14]=='e0': # catches the case of two back to back hits in the same string with no 'bc' idle byte in between
            good_part=String[-16:]  # this filter should also catch the case of one hit partially writing over another, leading the cutoff hit to get filtered out
            Good_List.append(good_part)
            other_part=String[:-16]
            Good_List=Good_List+Filter_Function(other_part)
        elif String[-2:]=='bc': # catches the case of two hits in the same string with only one 'bc' idle byte in between
            other_part=String[:-2]
            Good_List=Good_List+Filter_Function(other_part)
    return Good_List


full_file_name=input('Name of .log File: ')


start_time=datetime.now()
print(f'\nStart Time: {datetime.strftime(start_time,"%Y-%m-%d   %H:%M:%S")}\n')

result=subprocess.run(['wc','-l',full_file_name],capture_output=True, text=True)
output=result.stdout

total_lines=int((output.removesuffix(f'{full_file_name}\n')))

print(f'{result.stdout} \n Lines={total_lines}\n')

read_file=open(full_file_name,'r')


write_file=open(full_file_name.replace('.log','.csv'),'w')
row_0_list=['dec_ord','id', 'payload', 'row', 'col', 'ts1', 'tsfine1', 'ts2', 'tsfine2', 'tsneg1', 'tsneg2', 'tstdc1', 'tstdc2', 'ts_dec1', 'ts_dec2', 'tot_us']
row_0_string=','.join(row_0_list)
write_file.write(f'{row_0_string}\n')

stored_split_first_part=None


progress_bar=tqdm.tqdm(total=total_lines)

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
        split_bc=no_ff_string.split('bcbc') # splits on 'bcbc' idle bytes to avoid splitting on 'bc' that may appear in a hit
        good_split_bc=[]
        for i in split_bc:
            if i!='':
                good_split_bc.append(i)

        if len(good_split_bc)>1: # this helps fix the split hit issue
            if len(good_split_bc[-1])<16:
                stored_split_first_part=good_split_bc[-1]
                good_split_bc=good_split_bc[:-1]
            else:
                stored_split_first_part=None

        all_filtered=[]
        for hit_string in good_split_bc:
            all_filtered=all_filtered+Filter_Function(hit_string)

        decode_object=decode.Decode(bytesperhit=8)
        dec_order_counter=0
        for i in all_filtered:
            rawdata=list(binascii.unhexlify(i))
            list_hits=decode_object.hits_from_readoutstream(rawdata, reverse_bitorder=True)
            decoded_hits_list=decode_object.decode_astropix4_hits(list_hits)
            for hits_i in decoded_hits_list:
                hits_i=[dec_order_counter]+hits_i
                dec_order_counter+=1 # the correct implimentation of the dec_ord, counting up for each hit in a string
                write_string=','.join(str(x) for x in hits_i)
                write_file.write(f'{write_string}\n')

read_file.close()
write_file.close()
finish_time=datetime.now()
elapsed_time=finish_time-start_time
print(f'Finish Time: {datetime.strftime(finish_time,"%Y-%m-%d   %H:%M:%S")} \n Time Elapsed: {elapsed_time.days} days, {elapsed_time.seconds // 3600} hours, {(elapsed_time.seconds % 3600) // 60} minutes, {elapsed_time.seconds % 60} seconds')