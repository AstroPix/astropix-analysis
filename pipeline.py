import os, subprocess, argparse
from datetime import datetime
import tqdm
import matplotlib.pyplot as plt
from matplotlib.norm import LogNorm
import pandas as pd

import rowcolMatching_astropix_v3
import astropix_v3_decoder


def bindecode(full_file_name, outputfile):
    start_time=datetime.now()
    print(f'\nStart Time: {datetime.strftime(start_time,"%Y-%m-%d   %H:%M:%S")}\n')
    bin_file_size=astropix_v3_decoder.get_bin_file_size(full_file_name)
    print(f'{full_file_name} \n Size of File={round(bin_file_size/1024/1024,2)}MB\n')
    read_file=open(full_file_name,'rb')

    row_0_list=['dec_ord', 'readout', 'layer', 'chipID', 'payload', 'location', 'isCol', 'timestamp', 'tot_msb', 'tot_lsb', 'tot_total', 'tot_us', 'fpga_ts'] # make 'dec_ord' ''
    row_0_string=','.join(row_0_list)
    if os.path.isfile(outputfile):
        write_file=open(outputfile,'a')
    else:
        write_file=open(outputfile,'w')
        write_file.write(f'{row_0_string}\n')

    stored_split_first_part=None
    line_counter=0
    total_length_decoded=0
    chunk_size=1024
    progress_bar=tqdm.tqdm(total=int(bin_file_size/chunk_size)+1)
    while True:
        chunk = read_file.read(chunk_size)
        if not chunk:
            break
        _, stored_split_first_part, line_counter, single_chunk_length_decoded = astropix_v3_decoder.Decode_and_Write_Line(chunk,stored_split_first_part,line_counter,write_file,is_bin=True)#send data here
        total_length_decoded+=single_chunk_length_decoded
        progress_bar.update(1)

    read_file.close()
    write_file.close()
    finish_time=datetime.now()
    elapsed_time=finish_time-start_time
    print(f'Finish Time: {datetime.strftime(finish_time,"%Y-%m-%d   %H:%M:%S")} \n Time Elapsed: {elapsed_time.days} days, {elapsed_time.seconds // 3600} hours, {(elapsed_time.seconds % 3600) // 60} minutes, {elapsed_time.seconds % 60} seconds')
    print('\n')
    print(f'Total number of bytes in binary file: {bin_file_size}')
    print(f'Total number of decoded bytes: {total_length_decoded}')
    print(f'Percentage decoded: {round((total_length_decoded/bin_file_size)*100,2)}%')



class RowColMatch:
    def __init__(self):
        rcmatch = "./rowcolmatch/rowcolmatch"
        if os.path.isfile(rcmatch) and os.access(rcmatch, os.X_OK):
            print("Found rowcolmatch executable")
            def _rowcolmatch(*args):
                return subprocess.run([rcmatch, *args])
            self.rowcolmatch = _rowcolmatch
        else:
            print("Using the python rowcolmatch as a library")
            self.rowcolmatch = rowcolMatching_astropix_v3.rowcolmatch
    def __call__(self, *args):
        return self.rowcolmatch(*args)


def hitmap(d, **kwargs):
  plt.hist2d(d.col, d.row, (range(36), range(36)), **kwargs)
  plt.xlabel("Col")
  plt.ylabel("Row")
  plt.colorbar(); plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Integrated pipeline to analyze A-STEP data")
    parser.add_argument("-n", "--name", nargs='+', help="Name of file or files for a given run")
    parser.add_argument("-o", "--output", help="Name of csv output files")
    parser.add_argument("-l", "--layer", type=int, help="Number of layers to process (default=1)", default=1)
    args = parser.parse_args()
    for f in args.name:
        bindecode(args.name, args.output)
    rcmatch = RowColMatch()
    rcmatch(args.output, layer=args.layer+1)
    data = pd.read_csv(args.output[:-4]+"_matched.csv")
    for layer in range(1,args.layer+1):
        for chip in range(4):
            hitmap(data[(data.layer==layer)&(data.chipID==chip)])










