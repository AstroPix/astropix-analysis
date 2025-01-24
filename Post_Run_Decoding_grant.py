import numpy as np
import pandas as pd
import binascii
import decode

from tqdm import tqdm as tqdm

def heading_tester(string):
    return_bool=True
    string_list=[i for i in string.replace('ff','bc').split('bc') if i!='']
    for i in string_list:
        if (i[0:2]!='e0'):
            return_bool=False
    return return_bool

def decoder(title_string):
    csvframe =pd.DataFrame(columns = [
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
                'tot_us'
            ])
    f=np.loadtxt(title_string, skiprows=7,dtype=str)
    strings=[a[2:-1] for a in f[:,1]]
    for i in strings:
        if heading_tester(i): #this step filters for the correct header byte: 'e0'
            decode_object=decode.Decode(bytesperhit=8)
            rawdata=list(binascii.unhexlify(i))
            list_hits=decode_object.hits_from_readoutstream(rawdata, reverse_bitorder=True)
            hits=decode_object.decode_astropix4_hits(list_hits)
            csvframe=pd.concat([csvframe,hits])
    csvframe.index.name = 'dec_ord'
    csvframe.to_csv(title_string.replace('.log','.csv'))

Title_String=input('Name of .log File: ')
decoder(Title_String)