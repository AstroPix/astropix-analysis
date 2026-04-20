import numpy as np
import os
import argparse

import New_Source_Decoder

def extension_finder(extension,directory='./'):
    files=[x for x in os.listdir(directory) if x.casefold().endswith(extension)]
    if directory!='./':
        files=[directory+'/'+x for x in files]
    return files


parser=argparse.ArgumentParser(description='Loops over folders to decode all files within')

parser.add_argument('-i','--input', required=True, type=str, 
                    help='Name of input top level directory')

parser.add_argument('-n', '--name', required=False,
                    help='Name of input .log file')

parser.add_argument('-V', '--chipVer', required=False, type=int,
                    help='Chip version - provide an int')

parser.add_argument
args = parser.parse_args()

folder_list=[x[0] for x in os.walk(args.input.replace('\\','/'))]
args.chipVer=4
for folder in folder_list:
    file_list=extension_finder('.log',folder)
    for file in file_list:
        args.name=file
        New_Source_Decoder.main(args)