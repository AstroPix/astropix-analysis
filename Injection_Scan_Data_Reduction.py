import numpy as np
import os
import argparse

parser=argparse.ArgumentParser(description='Reducing Injection Scan Data')
parser.add_argument('-i', '--input', required=True, type=str, help='Name of input top level directory containing VPDAC folders')
parser.add_argument('-o', '--output', required=True, type=str, help='Name of output text file, does not need the .txt suffix')

parser.add_argument
args=parser.parse_args()

def extension_finder(extension,directory='./'):
    files=[x for x in os.listdir(directory) if x.casefold().endswith(extension)]
    if directory!='./':
        files=[directory+'/'+x for x in files]
    return files

def count_lines(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        return sum(1 for lines in file)

def Get_Threshold_Counts_Array(VPDAC, TuneDAC, column):
    folder_name=f'Runs_Injection/Pisa_Data/TuneDAC_{TuneDAC}/Col_{column}'

    threshold_counts_list=[]
    file_list=extension_finder('.csv',folder_name)
    for file_name in file_list:
        threshold=int(file_name.split('/')[-1].split('_')[1].rstrip('mV'))
        counts=count_lines(file_name)-1
        threshold_counts_list.append([threshold,counts])
    threshold_counts_array=np.array(threshold_counts_list)
    threshold_counts_array=threshold_counts_array[np.argsort(threshold_counts_array[:,0])]

    return threshold_counts_array

# top_directory=args.input.replace('\\','/')
# number_of_thresholds=len(extension_finder('csv',top_directory+'/TuneDAC_0/Col_0'))
# VPDAC_Threshold_Counts_Array=np.zeros((8,13,number_of_thresholds,2))
# for TuneDAC in np.arange(8):
#     for col in np.arange(13):
#         folder_name=top_directory+f'/TuneDAC_{TuneDAC}/Col_{col}'
#         threshold_counts_list=[]
#         file_list=extension_finder('.csv',folder_name)
#         for file_name in file_list:
#             threshold=int(file_name.split('/')[-1].split('_')[1].rstrip('mV'))
#             counts=count_lines(file_name)-1
#             threshold_counts_list.append([threshold,counts])
#         threshold_counts_array=np.array(threshold_counts_list)
#         threshold_counts_array=threshold_counts_array[np.argsort(threshold_counts_array[:,0])]
#         VPDAC_Threshold_Counts_Array[TuneDAC,col]=threshold_counts_array

# np.savetxt(args.output+'.txt',VPDAC_Threshold_Counts_Array.flatten())

top_directory=args.input.replace('\\','/')
number_of_thresholds=len(extension_finder('csv',top_directory+'/VPDAC_10/TuneDAC_0/Col_0'))
Full_Threshold_Counts_Array=np.zeros((4,8,13,number_of_thresholds,2))
for i_VPDAC,VPDAC in enumerate([10,20,30,40]):
    for TuneDAC in np.arange(8):
        for col in np.arange(13):
            folder_name=top_directory+f'/VPDAC_{VPDAC}/TuneDAC_{TuneDAC}/Col_{col}'
            threshold_counts_list=[]
            file_list=extension_finder('.csv',folder_name)
            for file_name in file_list:
                threshold=int(file_name.split('/')[-1].split('_')[1].rstrip('mV'))
                counts=count_lines(file_name)-1
                threshold_counts_list.append([threshold,counts])
            threshold_counts_array=np.array(threshold_counts_list)
            threshold_counts_array=threshold_counts_array[np.argsort(threshold_counts_array[:,0])]
            Full_Threshold_Counts_Array[i_VPDAC,TuneDAC,col]=threshold_counts_array

np.savetxt(args.output+'.txt',Full_Threshold_Counts_Array.flatten())
