import numpy as np
import pandas as pd
import binascii
import decode_copy
import tools_grant

from tqdm import tqdm as tqdm


'''this script takes the .log files of a source run and returns the final .csv into the same directory.
there is a problem where some hits get stored in multiple lines in the .log file, this script fixes that issue and recovers those hits.
lastly, some of the .log files are very large and cannot be read into memory all at once so this script breaks the decoding into 
multiple steps and combines all the csv files in the end, this results in a relatively long run time ~10 minutes.'''

full_file_name=input('Name of .log File: ')
lines=int(input('Number of lines in .log File: '))

file_name_list=full_file_name.split('/')

directory_name=f'{file_name_list[0]}/{file_name_list[1]}'

file_name=full_file_name.split('.')[0]

maxrows=100000

for k in range(round(lines/maxrows)):
    skip_rows=7+(k*maxrows)
    
    print(f'skiprows={skip_rows}')
    print(f'maxrows={maxrows}')
    print('\n')

    all_text=np.loadtxt(full_file_name, skiprows=skip_rows, max_rows=maxrows, dtype=str)
    no_ff=[]
    print('Text Loaded In, 4 Steps to Go')
    for i in tqdm(all_text[:,1]):
        for j in i[2:-1].split('ff'):
            if j != '':
                no_ff.append(j)
    no_ff_string=''.join(no_ff)
    split_bc=no_ff_string.split('bc')
    good_split_bc=[]
    print('Step 1/4 Completed')
    for i in tqdm(split_bc):
        if i!='':
            good_split_bc.append(i)
    all_filtered=[]
    print('Step 2/4 Completed')
    for i in tqdm(good_split_bc):
        if len(i)==16 and i[0:2]=='e0':
            all_filtered.append(i)
    all_hits_list=[]
    print('Step 3/4 Completed')
    for i in tqdm(all_filtered):
        decode_object=decode_copy.Decode(bytesperhit=8)
        rawdata=list(binascii.unhexlify(i))
        list_hits=decode_object.hits_from_readoutstream(rawdata, reverse_bitorder=True)
        hits=decode_object.decode_astropix4_hits(list_hits)
        all_hits_list.append(hits)
    print('Step 4/4 Completed, Converting to .csv file')
    print('\n')

    all_hits_array=np.array(all_hits_list).reshape(len(all_hits_list),15)

    csvframe=pd.DataFrame(all_hits_array, columns = [
                'id',
                'payload',
                'row',
                'col',
                'ts1',
                'tsfine1',
                'ts2',
                'tsfine2',
                'tsneg1',
                'tsneg2',
                'tstdc1',
                'tstdc2',
                'ts_dec1',
                'ts_dec2',
                'tot_us'])
    csvframe.index.name = 'dec_ord'
    csv_name=str(f'{file_name}-{k}.csv')
    csvframe.to_csv(csv_name)

all_csv=tools_grant.extension_finder('.csv',directory_name)

df_concat = pd.concat([pd.read_csv(f) for f in all_csv ], ignore_index=True) #this ignore_index is important so the dec_ord column isn't repeated

df_concat.to_csv(f'{file_name}.csv',index=False) #this index=False is again important so the dec_ord column isn't repeated