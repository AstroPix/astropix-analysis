import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import scipy as sp
import os
import math


def safe_int_convert(value):
    try:
        return int(value)
    except ValueError:
        return value
    

def extension_finder(extension,directory='./',save_list=False,print_list=False): #option to save the list to a txt file, don't include the .txt suffix, option to print the list
    files=[x for x in os.listdir(directory) if x.casefold().endswith(extension)] #searches for lower case or upper case versions of the extension
    if directory!='./':
        files=[directory+'/'+x for x in files]

    numbered_list=[i for i in files if isinstance(safe_int_convert(i.split('-')[-1].split('.')[0]),int) and safe_int_convert(i.split('-')[-1].split('.')[0])<500]
    not_numbered_list=[i for i in files if i not in numbered_list]

    flip_array=np.array([[i,int(s.split('-')[-1].split('.')[0])] for i,s in enumerate(numbered_list)]).reshape(len(numbered_list),2)
    sorted_flip_array=flip_array[flip_array[:,1].argsort()]
    ordered_numbered_csv=[numbered_list[i] for i in sorted_flip_array[:,0]]
    return_csv=not_numbered_list+ordered_numbered_csv

    if save_list:
        output_name=input('What is the name of the output .txt file?')
        with open(f'{output_name}.txt','w') as stream:
            for i in return_csv:
                stream.write(i+'\n')        #writes each element of the list to a new line of the text document
    if print_list:
        print(return_csv)
        
    return return_csv



def get_first_number(title_string): #returns the first number as an integer that appears in the title string, used to get the run injection voltage
    title_string=title_string.split('/')[-1] #only looks at the file name, ignores the directories
    indicator0,indicator1=True,False
    test_list=[]
    for i in title_string:
        if i.isnumeric() and indicator0:
            indicator1,indicator0= True,False
        if i.isnumeric() and indicator1:
            test_list.append(i)
        elif indicator1:
            indicator1=False
    return str(''.join(test_list))



def data_cleaner(title_string):
    df=pd.read_csv(title_string)
    tot_us_array=np.array(df['tot_us'])
    dec_order_array=np.array(df['dec_ord'])
    row_array, column_array = np.array(df['row']), np.array(df['col'])
    mask_array=np.zeros_like(tot_us_array)
    for i,s in enumerate(dec_order_array):
        if s==0 and row_array[i] <= 16 and column_array[i]<=16:
            mask_array[i]=1
        elif s!=0:
            mask_array[i]=0
            mask_array[i-1]=0
        else:
            mask_array[i]=0
    mask_array=mask_array.astype(bool)

    tot_us_array=tot_us_array[mask_array]
    dec_order_array=dec_order_array[mask_array]
    id_array=np.array(df['id'])[mask_array]
    payload_array=np.array(df['payload'])[mask_array]
    row_array=row_array[mask_array]
    column_array=column_array[mask_array]
    ts1_array=np.array(df['ts1'])[mask_array]
    tsfine1_array=np.array(df['tsfine1'])[mask_array]
    ts2_array=np.array(df['ts2'])[mask_array]
    tsfine2_array=np.array(df['tsfine2'])[mask_array]
    tsneg1_array=np.array(df['tsneg1'])[mask_array]
    tsneg2_array=np.array(df['tsneg2'])[mask_array]
    tstdc1_array=np.array(df['tstdc1'])[mask_array]
    tstdc2_array=np.array(df['tstdc2'])[mask_array]
    ts_dec1_array=np.array(df['ts_dec1'])[mask_array]
    ts_dec2_array=np.array(df['ts_dec2'])[mask_array]
    for i in range(len(tot_us_array)):
        if tot_us_array[i] < 0:
            tot_us_array[i]+=6553.6
    data=np.array([dec_order_array,id_array,payload_array,
                   row_array,column_array,ts1_array,tsfine1_array,
                   ts2_array,tsfine2_array,tsneg1_array,tsneg2_array,
                   tstdc1_array,tstdc2_array,ts_dec1_array,ts_dec2_array,
                   tot_us_array
                   ])
    return np.transpose(data)



def data_from_csv(title_string,row=None,column=None, simple_mask_bool:bool=False):
    df=pd.read_csv(title_string)
    tot_us_array=np.array(df['tot_us'])
    dec_order_array=np.array(df['dec_ord'])
    row_array, column_array = np.array(df['row']), np.array(df['col'])
    mask_array=np.zeros_like(tot_us_array)
    if row!=None and column!=None:
        for i,s in enumerate(dec_order_array):
            if s==0 and row_array[i] == row and column_array[i]==column:
                mask_array[i]=1
            elif s!=0:
                mask_array[i]=0
                mask_array[i-1]=0
            else:
                mask_array[i]=0
        mask_array=mask_array.astype(bool)
        tot_us_array=tot_us_array[mask_array]
        row_array=row_array[mask_array]
        column_array=column_array[mask_array]
        for i in range(len(tot_us_array)):
            if tot_us_array[i] < -6000:
                tot_us_array[i]+=6553.6
        noise_mask_array=np.zeros_like(tot_us_array)
        for i,s in enumerate(tot_us_array):
            if s > 10:
                noise_mask_array[i]=1
        noise_mask_array=noise_mask_array.astype(bool)
        tot_us_array=tot_us_array[noise_mask_array]
        row_array=row_array[noise_mask_array]
        column_array=column_array[noise_mask_array]
    
    for i in range(len(tot_us_array)):
        if tot_us_array[i] < -6300:
            tot_us_array[i]+=6553.6
    simple_mask_array=np.zeros_like(tot_us_array)
    if simple_mask_bool:
        for i,s in enumerate(tot_us_array):
            if s < 300 and s > 0:
                simple_mask_array[i]=1
        simple_mask_array=simple_mask_array.astype(bool)
        tot_us_array=tot_us_array[simple_mask_array]
        row_array=row_array[simple_mask_array]
        column_array=column_array[simple_mask_array]
    return np.array([row_array, column_array, tot_us_array]).transpose()


def spectra_plotting(*title_strings, row=None, column=None, 
                     plot_title_string: str = '', plot_x_label:str='', plot_y_label:str='', label_units:str='',
                     cutoff=None, num_bins=25,
                     save_fig_bool:bool=False, fig_title:str=''):
    title_dict=dict(zip([get_first_number(i) for i in title_strings],title_strings)) #sorting the list of titles by the first number in the title string
    new_title_list=[title_dict[i]for i in sorted(title_dict.keys())]

    fig,axes=plt.subplots()
    for title in new_title_list:
        delete_list=[]
        results_list=data_from_csv(title,row,column)[:,2]
        if cutoff!=None and type(cutoff)==int:
            for i,s in enumerate(results_list):
                if s>cutoff:
                    delete_list.append(i)
            for i in reversed(delete_list):
                results_list=np.delete(results_list,i)
        axes.hist(results_list,bins=num_bins,histtype='step',label=f'{get_first_number(title)} {label_units}')

    axes.set_title(plot_title_string)
    axes.set_xlabel(plot_x_label)
    axes.set_ylabel(plot_y_label)
    if save_fig_bool:
        axes.legend()
    else:
        axes.legend(loc='center left', bbox_to_anchor=(1,0.5))

    if save_fig_bool:
        plt.savefig(fig_title,dpi=600)


def bin_center(bin_list):
    centers=[]
    for i in range(len(bin_list)-1):
        centers.append((bin_list[i]+bin_list[i+1])/2)
    return np.array(centers)



def gaussian(x,A,mu,sigma):
    return A*np.exp(-0.5*((x-mu)/sigma)**2)

def gaussian_noise(x,A,mu,sigma,noise):
    return (A-noise)*np.exp(-0.5*((x-mu)/sigma)**2)+noise

def slope(x,left,right,top,bottom):
    slope=(bottom-top)/(right-left)

    return (
    (x<left)              *   (top)      +
    ((x>=left) & (x<right))  *   (top + slope*(x-left))      +
    (x>=right)             *   (bottom))

def gaussian_noise_and_slope(x,A,mu,sigma,top,bottom,left,right):
    slope=(bottom-top)/(right-left)

    return (
    (x<left)              *   (gaussian_noise(x,A,mu,sigma,top))      +
    ((x>=left) & (x<right))  *   (top + slope*(x-left))      +
    (x>=right)             *   (bottom))

def split_gaussian(x,A,mu,sigma,noise):
    return (
    (x<mu)              *   (gaussian_noise(x,A,mu,sigma,noise))      +
    (x>=mu)             *   (gaussian_noise(x,A,mu,sigma,0)))

def gaussian_linear_noise(x,A,mu,sigma,noise_a,noise_b):
    noise=noise_a*x+noise_b
    return (A-noise_a*x+noise_b)*np.exp(-0.5*((x-mu)/sigma)**2)+noise_a*x+noise_b


def gaussian_linear_noise_and_slope(x,A,mu,sigma,top,bottom,left,right,noise_left,noise_bottom):
    slope=(bottom-top)/(right-left)
    noise_a_temp=(top-noise_bottom)/(left-noise_left)
    noise_b_temp=noise_bottom-noise_a_temp*noise_left

    return (
    (x<left)              *   (gaussian_linear_noise(x,A,mu,sigma,noise_a_temp,noise_b_temp))      +
    ((x>=left) & (x<right))  *   (top + slope*(x-left))      +
    (x>=right)             *   (bottom))

def pixel_plot(axes, results_array, plot_title=None, row_bool:bool=False, col_bool:bool=False):
    pixel_plot=axes.imshow(results_array)
    if row_bool:
        axes.set_xlabel('Rows')
    if col_bool:
        axes.set_ylabel('Columns')
    axes.set_xticks(np.arange(0,13,1))
    axes.set_yticks(np.arange(0,16,1))
    axes.set_ylim(-0.51,15.56)
    axes.set_xlim(-0.56,12.5)
    for i in range(17):
        axes.hlines(i-0.5,xmin=-0.5,xmax=16.5,colors='k')
        axes.vlines(i-0.5,ymin=-0.5,ymax=16.5,colors='k')
    if plot_title != None:
        axes.set_title(plot_title)
    return pixel_plot



def averageTOT_from_dict(dict:dict, row_in_string:int, col_in_string:int):
    results_array=np.zeros([16,13])
    file_list=list(dict.values())
    for i in file_list:
        data=data_from_csv(i)[:,2]
        if len(data)!=0:
            title_list=i.replace('_','-').replace('Pixel','-').split('-')
            col,row=int(title_list[col_in_string]),int(title_list[row_in_string])
            results_array[row,col]=np.average(data)
    return results_array