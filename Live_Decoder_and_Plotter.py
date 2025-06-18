import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import pandas as pd
import binascii
#import decode_copy
import time
import tqdm
import os
from datetime import datetime
import Source_Decoder
import Quad_Chip_Decoder
import argparse


''' this script takes the .log files of a source run and returns the .csv into the same directory 
filtering function works to fix common issues seen with decoding raw lines from the .log file'''
def bin_center(bin_list):
    centers=[]
    for i in range(len(bin_list)-1):
        centers.append((bin_list[i]+bin_list[i+1])/2)
    return np.array(centers)


def count_lines(filename):
    with open(filename, 'r') as file:
        return sum(1 for line in file)
    
def read_from_line(file_path, num_lines_to_skip):
    try:    
        with open(file_path, 'r') as file:
            for _ in range(num_lines_to_skip):
                next(file)  # Skip lines efficiently
            return file.readlines()
    except StopIteration:
        print('No new data found')
        return []



def main(args):
    ### Initialize decoding ##

    chip_version=args.chipVer.lower()
    log_file_name=args.name.lstrip('.').replace("\\",'/').lstrip('/')
    creation_timestamp=os.path.getctime(log_file_name)
    creation_time=datetime.fromtimestamp(creation_timestamp)
    file_name_parts=log_file_name.split('/')
    file_name_parts[-1]='Live_Decoding_'+file_name_parts[-1].replace('.log','.csv')
    csv_file_name='/'.join(file_name_parts)

    if chip_version=='4':
        Bytes_per_hit=8
        skip_rows=7
        csv_columns=16
        tot_position=-1
        max_tot=200
    elif chip_version=='3':
        Bytes_per_hit=5
        skip_rows=6
        csv_columns=11
        tot_position=-1
        max_tot=50
    elif chip_version=='quad3':
        skip_rows=121
        csv_columns=13
        tot_position=-2
        max_tot=50

    first_data=read_from_line(log_file_name,skip_rows)
    csv_write_file=open(csv_file_name,'w')

    if chip_version=='4':
        row_0_list=['dec_ord','id', 'payload', 'row', 'col', 'ts1', 'tsfine1', 'ts2', 'tsfine2', 'tsneg1', 'tsneg2', 'tstdc1', 'tstdc2', 'ts_dec1', 'ts_dec2', 'tot_us']
    elif chip_version=='3':
        row_0_list=['dec_ord','readout', 'Chip ID', 'payload', 'location', 'isCol', 'timestamp', 'tot_msb', 'tot_lsb', 'tot_total', 'tot_us']
    elif chip_version=='quad3':
        row_0_list=['dec_ord','readout','layer','Chip ID','payload','location','isCol','timestamp','tot_msb','tot_lsb','tot_total','tot_us','fpga_ts']
    row_0_string=','.join(row_0_list)

    csv_write_file.write(f'{row_0_string}\n')

    stored_split_first_part=None
    line_counter=0
    decoded_data_list=[]
    for line in first_data:
        if chip_version=='3' or chip_version=='4':
            Initial_Live_Decoding_Output=Source_Decoder.Decode_and_Write_Line(line,stored_split_first_part,int(chip_version),line_counter,csv_write_file)
            if Initial_Live_Decoding_Output is not None:
                decoded_line, stored_split_first_part, line_counter = Initial_Live_Decoding_Output[0], Initial_Live_Decoding_Output[1], Initial_Live_Decoding_Output[2]
                for item in decoded_line:
                    decoded_data_list.append(item)
        elif chip_version=='quad3':
            Initial_Live_Decoding_Output=Quad_Chip_Decoder.Decode_and_Write_Line(line,stored_split_first_part,line_counter,csv_write_file)
            if Initial_Live_Decoding_Output is not None:
                decoded_line, stored_split_first_part, line_counter = Initial_Live_Decoding_Output[0], Initial_Live_Decoding_Output[1], Initial_Live_Decoding_Output[2]
                for item in decoded_line:
                    decoded_data_list.append(item)
    log_file_length=len(first_data)+skip_rows
    decoded_data=np.array(decoded_data_list).flatten().reshape(-1,csv_columns)

    ### Plotting Initialization ###


    # fig,axes = plt.subplots(1,2,figsize=(12, 6))
    fig=plt.figure(figsize=(12,9))
    gs=fig.add_gridspec(2,2,height_ratios=[2,1])

    ax0=fig.add_subplot(gs[0,0])    
    ax1=fig.add_subplot(gs[0,1])
    ax2=fig.add_subplot(gs[1,:])
    axes=[ax0,ax1,ax2]


    fig.suptitle(f'Start Time: {creation_time}\nLog File Name: {log_file_name.split("/")[-1]}')


    tot_bin_edges=np.linspace(0,max_tot,201)
    tot_bin_centers=bin_center(tot_bin_edges)
    counts,tot_bins=np.histogram(decoded_data[:,tot_position],bins=tot_bin_edges)
    (step_object,)=axes[0].step(tot_bin_centers,counts)
    axes[0].set_xlabel(r'ToT $(\mu s)$')
    axes[0].set_ylabel('Counts')
    ellapsed_time=datetime.now()-creation_time
    count_rate=round(sum(counts)/max(ellapsed_time.seconds,1),2)
    axes[0].set_title(f'Average Count Rate: {count_rate} Hz\nTotal Counts: {sum(counts)}')

    time_list=[ellapsed_time.seconds]
    count_rate_list=[count_rate]
    axes[2].plot(time_list,count_rate_list,'.-',color='C0')
    axes[2].set_xlabel('Time Since Start of Run (sec)')
    axes[2].set_ylabel('Count Rate (Hz)')

    if chip_version=='4':
        counts_per_pixel_array=np.zeros((13,16))
        rows=decoded_data[:,3].astype(int)
        columns=decoded_data[:,4].astype(int)
        valid_mask= (rows>=0) & (rows<13) & (columns>=0) & (columns<16)
        np.add.at(counts_per_pixel_array,(rows[valid_mask],columns[valid_mask]),1)

        im=axes[1].imshow(np.flip(counts_per_pixel_array,axis=1).T)
        cbar=plt.colorbar(im)
        cbar.set_label('Hits Per Pixel')
        axes[1].set_xticks(np.arange(0,13,1))
        axes[1].set_yticks(np.arange(0,16,1))
        axes[1].set_yticklabels(np.arange(15,-1,-1))
        axes[1].set_xlabel('Rows')
        axes[1].set_ylabel('Columns')
        for i in range(17):
            axes[1].hlines(i-0.5,xmin=-0.5,xmax=12.5,colors='k')   
        for j in range(14):
            axes[1].vlines(j-0.5,ymin=-0.5,ymax=15.5,colors='k') 
        axes[1].set_title(f'Counts: {np.sum(counts_per_pixel_array)}')

    elif chip_version=='3':
        counts_per_pixel_array=np.zeros((35,2))
        location=decoded_data[:,4].astype(int)
        isCol=decoded_data[:,5].astype(int)
        valid_mask= (location>=0) & (location<35) & (isCol>=0) & (isCol<2)
        np.add.at(counts_per_pixel_array,(location[valid_mask],isCol[valid_mask]),1)

        row_fraction=counts_per_pixel_array[:,0]/np.sum(counts_per_pixel_array[:,0])
        col_fraction=counts_per_pixel_array[:,1]/np.sum(counts_per_pixel_array[:,1])
        estimated_pixel_map=np.outer(row_fraction,col_fraction)*np.sum(counts_per_pixel_array[:,0])

        # im=axes[1].imshow((counts_per_pixel_array))
        # im=axes[1].imshow(np.flip(estimated_pixel_map.T,axis=0))
        im=axes[1].imshow(np.flip(estimated_pixel_map,axis=0))
        cbar=plt.colorbar(im,ax=axes[1])
        cbar.set_label('Hits Per Pixel')
        axes[1].set_yticks(np.arange(0,35))
        axes[1].set_yticklabels(np.arange(34,-1,-1),fontsize=5)
        # axes[1].set_xticks([0,1])
        # axes[1].set_xticklabels(['r','c'])
        axes[1].set_xticks(np.arange(0,35))
        axes[1].set_xticklabels(np.arange(0,35,),fontsize=5,rotation=45)
        # axes[1].set_xlabel('Row or Col')
        # axes[1].set_ylabel('Location')
        axes[1].set_ylabel('Rows')
        axes[1].set_xlabel('Columns')

        for i in range(35):
            axes[1].hlines(i-0.5,xmin=-0.5,xmax=34.5,colors='k')   
        for j in range(35):
            axes[1].vlines(j-0.5,ymin=-0.5,ymax=34.5,colors='k') 
        axes[1].set_title(f'Counts: {int(np.sum(counts_per_pixel_array))}')

    elif chip_version=='quad3':
        counts_per_pixel_array=np.zeros((35,4*2))
        chipID=decoded_data[:,3].astype(int)
        location=decoded_data[:,5].astype(int)
        isCol=decoded_data[:,6].astype(int)
        valid_mask= (location>=0) & (location<35) & (isCol>=0) & (isCol<2) & (chipID>=0) & (chipID<4)
        np.add.at(counts_per_pixel_array,(location[valid_mask],2*chipID[valid_mask]+isCol[valid_mask]),1)

        row_fraction_0=counts_per_pixel_array[:,0]/max(np.sum(counts_per_pixel_array[:,0]),1)
        col_fraction_0=counts_per_pixel_array[:,1]/max(np.sum(counts_per_pixel_array[:,1]),1)
        estimated_pixel_map_0=np.outer(row_fraction_0,col_fraction_0)*np.sum(counts_per_pixel_array[:,0])

        row_fraction_1=counts_per_pixel_array[:,2]/max(np.sum(counts_per_pixel_array[:,2]),1)
        col_fraction_1=counts_per_pixel_array[:,3]/max(np.sum(counts_per_pixel_array[:,3]),1)
        estimated_pixel_map_1=np.outer(row_fraction_1,col_fraction_1)*np.sum(counts_per_pixel_array[:,2])

        row_fraction_2=counts_per_pixel_array[:,4]/max(np.sum(counts_per_pixel_array[:,4]),1)
        col_fraction_2=counts_per_pixel_array[:,5]/max(np.sum(counts_per_pixel_array[:,5]),1)
        estimated_pixel_map_2=np.outer(row_fraction_2,col_fraction_2)*np.sum(counts_per_pixel_array[:,4])

        row_fraction_3=counts_per_pixel_array[:,6]/max(np.sum(counts_per_pixel_array[:,6]),1)
        col_fraction_3=counts_per_pixel_array[:,7]/max(np.sum(counts_per_pixel_array[:,7]),1)
        estimated_pixel_map_3=np.outer(row_fraction_3,col_fraction_3)*np.sum(counts_per_pixel_array[:,6])

        estimated_pixel_map_list=np.array([estimated_pixel_map_0,estimated_pixel_map_1,estimated_pixel_map_2,estimated_pixel_map_3])
        grid_mapping=[2,3,0,1]

        host_ax = axes[1]
        host_ax.set_visible(False)  # Hide the base axes
        title_text=fig.text(0.72, 0.9, f'Counts: {int(np.sum(counts_per_pixel_array))}', fontsize=12, ha='center')
        outer_grid = gridspec.GridSpecFromSubplotSpec(2, 2, subplot_spec=host_ax.get_subplotspec(), wspace=0.2, hspace=0.2)

        # grids = [np.random.rand(35, 35) for _ in range(4)]
        vmin = min(g.min() for g in estimated_pixel_map_list)
        vmax = max(g.max() for g in estimated_pixel_map_list)
        im_axes = []
        im_list=[]
        for i in range(4):
            ax = fig.add_subplot(outer_grid[grid_mapping[i]])
            im = ax.imshow(np.flip(estimated_pixel_map_list[i],axis=0), vmin=vmin, vmax=vmax)
            ax.set_title(f'Chip ID {i}',fontsize=7,weight='bold')
            if i==0 or i==1:
                ax.set_xlabel('Columns')
            if i==0 or i==2:
                ax.set_ylabel('Rows')
            for i in range(35):
                ax.hlines(i-0.5,xmin=-0.5,xmax=34.5,colors='k')   
            for j in range(35):
                ax.vlines(j-0.5,ymin=-0.5,ymax=34.5,colors='k') 
            # ax.set_yticks(np.arange(0,35,5))
            ax.set_yticks(np.arange(4,35,5))
            # ax.set_yticklabels(np.arange(34,-1,-5),fontsize=5)
            ax.set_yticklabels(np.arange(30,-1,-5),fontsize=5)
            ax.set_xticks(np.arange(0,35,5))
            ax.set_xticklabels(np.arange(0,35,5),fontsize=5)
            im_axes.append(ax)
            im_list.append(im)

        # Add shared colorbar for one of the imshow plots
        cbar_ax = fig.add_axes([0.91, 0.4, 0.02, 0.5])  # [left, bottom, width, height]
        fig.colorbar(im, cax=cbar_ax, label='Hits Per Pixel')



        # im=axes[1].imshow((np.flip(counts_per_pixel_array,axis=0)))
        # cbar=plt.colorbar(im)
        # cbar.set_label('Hits Per Pixel')
        # axes[1].set_yticks(np.arange(0,35))
        # axes[1].set_yticklabels(np.arange(34,-1,-1))
        # axes[1].set_xticks(np.arange(0,8))
        # axes[1].set_xticklabels(['0\nr','0\nc','1\nr','1\nc','2\nr','2\nc','3\nr','3\nc'])
        # axes[1].set_xlabel('ChipID Number and Row or Col')
        # axes[1].set_ylabel('Location')

        # for i in range(35):
        #     axes[1].hlines(i-0.5,xmin=-0.5,xmax=7.5,colors='k')
        # for j in range(8):
        #     axes[1].vlines(j-0.5,ymin=-0.5,ymax=34.5,colors='k')
        # axes[1].set_title(f'Counts: {np.sum(counts_per_pixel_array)}')

    plt.pause(0.1)
    fig.canvas.draw()
    fig.canvas.flush_events()

    ### Live Plotting and Decoding Loop ###

    continue_bool=True
    log_file_length+=7
    while continue_bool:
        try:
            loop_start_time=datetime.now()
            time.sleep(10)
            print('Loading New Data...')
            new_data=read_from_line(log_file_name,log_file_length)
            print(f'New Data Found, of length {len(new_data)}')

            decoded_data_list=[]
            for line in new_data:
                if chip_version=='3' or chip_version=='4':
                    Live_Decoding_Output=Source_Decoder.Decode_and_Write_Line(line,stored_split_first_part,int(chip_version),line_counter,csv_write_file)
                    if Live_Decoding_Output is not None:
                        decoded_line, stored_split_first_part, line_counter = Live_Decoding_Output[0], Live_Decoding_Output[1], Live_Decoding_Output[2]
                        for item in decoded_line:
                            decoded_data_list.append(item)
                elif chip_version=='quad3':
                    Live_Decoding_Output=Quad_Chip_Decoder.Decode_and_Write_Line(line,stored_split_first_part,line_counter,csv_write_file)
                    if Live_Decoding_Output is not None:
                        decoded_line, stored_split_first_part, line_counter = Live_Decoding_Output[0], Live_Decoding_Output[1], Live_Decoding_Output[2]
                        for item in decoded_line:
                            decoded_data_list.append(item)
            log_file_length+=len(new_data)
            new_decoded_data=np.array(decoded_data_list).flatten().reshape(-1,csv_columns)

            if len(new_decoded_data)>1:

                counts+=np.histogram(new_decoded_data[:,tot_position],bins=tot_bin_edges)[0]
                step_object.set_data(tot_bin_centers,counts)
                axes[0].set_ylim(None, max(counts)*1.1)

                current_time=datetime.now()
                ellapsed_time=current_time-creation_time
                loop_count_rate=len(new_decoded_data)/((current_time-loop_start_time).seconds)
                time_list.append(ellapsed_time.seconds)
                count_rate_list.append(loop_count_rate)
                average_count_rate=round(sum(counts)/ellapsed_time.seconds,2)
                axes[0].set_title(f'Average Count Rate: {average_count_rate} Hz\nTotal Counts: {sum(counts)}')

                if chip_version=='4':
                    rows=new_decoded_data[:,3].astype(int)
                    columns=new_decoded_data[:,4].astype(int)
                    valid_mask= (rows>=0) & (rows<13) & (columns>=0) & (columns<16)
                    np.add.at(counts_per_pixel_array,(rows[valid_mask],columns[valid_mask]),1)
                    im.set_data(np.flip(counts_per_pixel_array,axis=1).T)
                    im.set_clim(vmin=np.min(counts_per_pixel_array),vmax=np.max(counts_per_pixel_array))
                    axes[1].set_title(f'Counts: {int(np.sum(counts_per_pixel_array))}')
                elif chip_version=='3':
                    location=new_decoded_data[:,4].astype(int)
                    isCol=new_decoded_data[:,5].astype(int)
                    valid_mask= (location>=0) & (location<35) & (isCol>=0) & (isCol<2)
                    np.add.at(counts_per_pixel_array,(location[valid_mask],isCol[valid_mask]),1)

                    row_fraction=counts_per_pixel_array[:,0]/np.sum(counts_per_pixel_array[:,0])
                    col_fraction=counts_per_pixel_array[:,1]/np.sum(counts_per_pixel_array[:,1])
                    estimated_pixel_map=np.outer(row_fraction,col_fraction)*np.sum(counts_per_pixel_array[:,0])

                    im.set_data(np.flip(estimated_pixel_map,axis=0))
                    im.set_clim(vmin=np.min(estimated_pixel_map),vmax=np.max(estimated_pixel_map))
                    axes[1].set_title(f'Counts: {np.sum(counts_per_pixel_array)}')
                elif chip_version=='quad3':
                    chipID=new_decoded_data[:,3].astype(int)
                    location=new_decoded_data[:,5].astype(int)
                    isCol=new_decoded_data[:,6].astype(int)
                    valid_mask= (location>=0) & (location<35) & (isCol>=0) & (isCol<2) & (chipID>=0) & (chipID<4)
                    np.add.at(counts_per_pixel_array,(location[valid_mask],2*chipID[valid_mask]+isCol[valid_mask]),1)
                    
                    row_fraction_0=counts_per_pixel_array[:,0]/max(np.sum(counts_per_pixel_array[:,0]),1)
                    col_fraction_0=counts_per_pixel_array[:,1]/max(np.sum(counts_per_pixel_array[:,1]),1)
                    estimated_pixel_map_0=np.outer(row_fraction_0,col_fraction_0)*np.sum(counts_per_pixel_array[:,0])

                    row_fraction_1=counts_per_pixel_array[:,2]/max(np.sum(counts_per_pixel_array[:,2]),1)
                    col_fraction_1=counts_per_pixel_array[:,3]/max(np.sum(counts_per_pixel_array[:,3]),1)
                    estimated_pixel_map_1=np.outer(row_fraction_1,col_fraction_1)*np.sum(counts_per_pixel_array[:,2])

                    row_fraction_2=counts_per_pixel_array[:,4]/max(np.sum(counts_per_pixel_array[:,4]),1)
                    col_fraction_2=counts_per_pixel_array[:,5]/max(np.sum(counts_per_pixel_array[:,5]),1)
                    estimated_pixel_map_2=np.outer(row_fraction_2,col_fraction_2)*np.sum(counts_per_pixel_array[:,4])

                    row_fraction_3=counts_per_pixel_array[:,6]/max(np.sum(counts_per_pixel_array[:,6]),1)
                    col_fraction_3=counts_per_pixel_array[:,7]/max(np.sum(counts_per_pixel_array[:,7]),1)
                    estimated_pixel_map_3=np.outer(row_fraction_3,col_fraction_3)*np.sum(counts_per_pixel_array[:,6])

                    estimated_pixel_map_list=np.array([estimated_pixel_map_0,estimated_pixel_map_1,estimated_pixel_map_2,estimated_pixel_map_3])
                    v_min,v_max=np.min(estimated_pixel_map_list),np.max(estimated_pixel_map_list)

                    for index,im in enumerate(im_list):
                        im.set_data(np.flip(estimated_pixel_map_list[index],axis=0))
                        im.set_clim(vmin=v_min,vmax=v_max)
                    title_text.set_text(f'Counts: {int(np.sum(counts_per_pixel_array))}')

                
                axes[2].plot(time_list,count_rate_list,'.-',color='C0')
                fig.canvas.draw()
                fig.canvas.flush_events()
        except KeyboardInterrupt:
            continue_bool=False
            print('KeyboardInterrupt, Closing Live Plot')

    plt.ioff()
    csv_write_file.close()
    plt.show()

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Plotting and Decoding Live AstroPix Data')
    parser.add_argument('-n', '--name', required=True, help='Name of input .log file')
    parser.add_argument('-V', '--chipVer', required=True, type=str, help='Chip version - provide an str, should be 3, 4 or Quad3')

    parser.add_argument
    args=parser.parse_args()

    main(args)