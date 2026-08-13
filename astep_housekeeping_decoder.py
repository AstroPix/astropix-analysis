import numpy as np
import struct
import argparse
import re
import time

from datetime import datetime, timezone

from send_data_to_influxdb import Influx_Write

def convertBytestoTemperature(rawTemp: bytearray) -> float:
    rawTemp = (int.from_bytes(rawTemp,'little')) >> 4
    return  rawTemp * 503.975 / 4096 - 273.15

def convertBytesToVCCInt(rawVcc: bytearray) -> float :
    rawVcc = (int.from_bytes(rawVcc,'little')) >> 4
    return rawVcc / 4096 * 3

def convertBytesToADCVal(rawADC: bytearray) -> float:
    return int.from_bytes(rawADC,'big') / 4096 * 3.3

def decode(packet: bytearray, precision: int = 2):
    """ Housekeeping Packet Format:
        8 Bytes FSW UTC Time
        4 Bytes FPGA Counter Time
        18 Bytes ADC: 2 Sync Bytes (\x10\x10) + 2 Bytes per 8 Channels
        14 Bytes FPGA: 2 Sync Bytes (\x0c\x0c) + 3 FPGA Temp Reads + 3 FPGA VCC Reads
        2 Bytes containing bufferSize (Note, may want to eventually convert to occupancy rather than raw)
        0x to 3x: 14 Bytes FPGA Counter: 2 Bytes Layer ID (e.g. Layer 2 = \x02\x02), 4 Bytes each Frame, Idle, Wronglength Counter
        3 Bytes Layer Status Counters: L0, L1, L2
        2 Bytes of HV Board temp from BB ADC"""
    fswtime = datetime.fromtimestamp(struct.unpack('d',packet[0:8])[0],tz=timezone.utc)#.strftime("%Y-%m-%d %H:%M:%S")
    fpgatime = int.from_bytes(packet[8:12],'little')
    
    ADCvalues = [convertBytesToADCVal(packet[14:30][i : i + 2]) for i in range(0,16,2)]
    L0Temp = ADCvalues[3] # missing calibration
    L1Temp = ADCvalues[2] # missing calibration
    L2Temp = ADCvalues[1] # missing calibration
    SecVolt = ADCvalues[0] * 2. 
    HVMon = ADCvalues[7] / 0.0125
    L0Current = ADCvalues[4] / 10.
    L1Current = ADCvalues[5] / 10.
    L2Current = ADCvalues[6] / 10.

    fpgatemp = np.round(np.mean([convertBytestoTemperature(packet[32:38][i : i + 2]) for i in range(0, 6, 2)]),precision).item()
    fpgaVCCInt = np.round(np.mean([convertBytesToVCCInt(packet[38:44][i : i + 2]) for i in range(0, 6, 2)]),precision).item()

    bufferBytes = packet[44:46]
    bufferSize = int.from_bytes(bufferBytes,'little')

    counterBytes = packet[46:60]
    layerinfo = [counterBytes[i:i+14] for i in range(0,len(counterBytes),14)]
    L0Frames = L0Idle = L0Wrong = 0
    L1Frames = L1Idle = L1Wrong = 0
    L2Frames = L2Idle = L2Wrong = 0

    for l in layerinfo:
        if l[0] == 0:
            L0Frames = int.from_bytes(l[2:5],'little')
            L0Idle = int.from_bytes(l[6:9],'little')
            L0Wrong = int.from_bytes(l[10:13],'little')
        elif l[0] == 1:
            L1Frames = int.from_bytes(l[2:5],'little')
            L1Idle = int.from_bytes(l[6:9],'little')
            L1Wrong = int.from_bytes(l[10:13],'little')
        elif l[0] == 2:
            L2Frames = int.from_bytes(l[2:5],'little')
            L2Idle = int.from_bytes(l[6:9],'little')
            L2Wrong = int.from_bytes(l[10:13],'little')

    statusBytes = packet[60:63]
    L0Status = int.from_bytes(statusBytes[0],'little')
    L1Status = int.from_bytes(statusBytes[1],'little')
    L2Status = int.from_bytes(statusBytes[2],'little')

    HVtempBytes = packet[63:65]
    rawHVV = int.from_bytes(HVtempBytes,'little')
    HVtemp = np.round(rawHVV  / 4096 * 1.8 / 2e-3 - 273 ),precision).item()

    hk_data = [fswtime,fpgatime,fpgatemp,fpgaVCCInt,SecVolt,HVMon,L0Temp,L1Temp,L2Temp,HVtemp,
               L0Current,L1Current,L2Current,L0Frames,L0Idle,L0Wrong,L1Frames,L1Idle,L1Wrong,L2Frames,L2Idle,L2Wrong,L0Status,L1Status,L2Status,bufferSize]
    return hk_data

def identify_index(data):
    """Use pre-defined sync bytes to identify and extract housekeeping indexes"""
    mask_one = b'\x10\x10'
    mask_two = b'\x0c\x0c'
    pattern = re.compile(re.escape(mask_one) + b'.{' + str(16).encode() + b'}' + re.escape(mask_two), re.DOTALL)
    matched = re.finditer(pattern,data)
    return [m.start() - 12 for m in matched]

def main(args):
    read_file=open(args.filename,'rb')
    data = read_file.read()
    read_file.close()
    
    write_file=open(args.filename.replace('.bin','.csv'),'w')
    header = ['fswtime','fpgatime','fpgatemp','fpgaVCCInt','SecVolt','HVMon','L0Temp','L1Temp','L2Temp',
              'L0Current','L1Current','L2Current','L0Frames','L0Idle','L0Wrong','L1Frames','L1Idle','L1Wrong',
              'L2Frames','L2Idle','L2Wrong']
    headerstring = ','.join(header)
    write_file.write(f'{headerstring}\n')
    
    pkt_indices = identify_index(data)
    packages = [data[i:j] for i,j in zip([0] + pkt_indices, pkt_indices + [None])][1:]

    for p in packages:
        decoded_hit = decode(p)

        decoded_string=','.join(str(x) for x in decoded_hit)
        write_file.write(f'{decoded_string}\n')

    write_file.close()

def read_from_offset(file_path, bytes_to_skip):
    try:
        with open(file_path, 'rb') as file:
            file.seek(bytes_to_skip)
            return file.read()
    except OSError as e:
        print(f'Error reading file: {e}')
        return b''


def live_decode(data,write_file,influx_obj):
    
    pkt_indices = identify_index(data)
    packages = [data[i:j] for i,j in zip([0] + pkt_indices, pkt_indices + [None])][1:]

    for p in packages:
        decoded_hit = decode(p)
        # print(f'Timestamp from fsw {decoded_hit[0]}, {type(decoded_hit[0])}')

        decoded_string=','.join(str(x) for x in decoded_hit)
        write_file.write(f'{decoded_string}\n')
        influx_obj.write_housekeeping_point(*decoded_hit)

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
    org = 'ASTEP'
    token='ZaAOdbYZXQtsYMSlSRmr4kNaJPsJq2OTlqUgZvkb_5Qk85_DF_8ZZ65K3Zr9w6QzkPTMKu2nA5_78Bzh35kFaA=='


    write_file=open(args.filename.replace('.bin','.csv'),'w')
    header = ['fswtime','fpgatime','fpgatemp','fpgaVCCInt','SecVolt','HVMon','L0Temp','L1Temp','L2Temp',
              'L0Current','L1Current','L2Current','L0Frames','L0Idle','L0Wrong','L1Frames','L1Idle','L1Wrong','L2Frames','L2Idle','L2Wrong']
    headerstring = ','.join(header)
    write_file.write(f'{headerstring}\n')


    influx_object=Influx_Write(url=url,org=org,bucket=bucket,api_token=token, write_precision='NS')
    gobool = True
    running_file_length=0
    while gobool:
        try:
            time.sleep(10)
            data=read_from_offset(args.filename, running_file_length)
            print(f'decoding data of length: {len(data)}')
            running_file_length+=len(data)
            if data:
                live_decode(data,write_file,influx_object)
                influx_object.send_points_to_influx()
        except KeyboardInterrupt:
            gobool = False
            write_file.close()
            
