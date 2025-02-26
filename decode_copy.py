# -*- coding: utf-8 -*-
""""""
''' a copy of the decode.py file from the astropix_python git repository, with one dependency from that repository commented out and changing 
the return of the decode_astropix4_hits function to be a list instead of a pandas data frame'''
"""
Created on Tue Dec 28 19:03:40 2021

@author: Nicolas Striebig
"""

import pandas as pd
import time

import logging
# from modules.setup_logger import logger


logger = logging.getLogger(__name__)

class Decode:
    def __init__(self, sampleclock_period_ns: int = 5, nchips: int = 1, bytesperhit: int = 5):
        self._sampleclock_period_ns = sampleclock_period_ns
        self._bytesperhit = bytesperhit
        self._idbits = 3
        self._nchips = nchips

        self._header = set()
        self._header_rev = set()
        self._gen_header()

    def _gen_header(self):
        """
        Pregenerate header bytes for nchips in a row
        """

        self._header = set()
        self._header_rev = set()

        for i in range(self._nchips):
            id = (i << self._idbits) + self._bytesperhit - 1
            self._header.add(id)

            id_rev = int(f'{id:08b}'[::-1], 2)
            self._header_rev.add(id_rev)

    def gray_to_dec(self, gray: int) -> int:
        """
        Decode Gray code to decimal
        :param gray: Gray code
        :returns: Decoded decimal
        """
        bits = gray >> 1
        while bits:
            gray ^= bits
            bits >>= 1
        return gray

    def reverse_bitorder(self, data: bytearray) -> bytearray:
        reversed_data = bytearray()

        for item in data:
            item_rev = int(bin(item)[2:].zfill(8)[::-1], 2)
            reversed_data.append(item_rev)

        return reversed_data

    def hits_from_readoutstream(self, readout: bytearray, reverse_bitorder: bool = True) -> list:
        """
        Find hits in readoutstream

        :param readout: Readout stream
        :param reverse_bitorder: Reverse Bitorder per byte

        :returns: Position of hits in the datastream
        """

        length = len(readout)
        hitlist = []
        i=0

        header = self._header_rev if reverse_bitorder else self._header
        bytesperhit = self._bytesperhit

        while i < length:
            if readout[i] not in header:
                i += 1
            else:
                if i + bytesperhit <= length:
                    if reverse_bitorder:
                        hitlist.append(self.reverse_bitorder(readout[i:i + bytesperhit]))
                    else:
                        hitlist.append(readout[i:i + bytesperhit])

                    i += bytesperhit
                else:
                    break

        return hitlist

    def decode_astropix3_hits(self, list_hits: list, i:int, printer:bool = False) -> pd.DataFrame:
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

        hit_pd = []

        for hit in list_hits:
             if len(hit) == self._bytesperhit:
                header, location, timestamp, tot_msb, tot_lsb = hit

                id          = header >> 3
                payload     = header & 0b111
                col         = location >> 7 & 1
                location   &= 0b111111
                timestamp   = timestamp
                tot_msb    &= 0b1111
                tot_lsb     = int(hit[4])
                tot_total   = (tot_msb << 8) + tot_lsb
                tot_us      = (tot_total * self._sampleclock_period_ns) / 1000.0

                hit_pd.append([i,id, payload, location, col, timestamp, tot_msb, tot_lsb, tot_total, tot_us, time.time()])
                if printer:
                    logger.info(
                    "Header: ChipId: %d\tPayload: %d\t"
                    "Location: %d\tRow/Col: %d\t"
                    "Timestamp: %d\t"
                    "ToT: MSB: %d\tLSB: %d Total: %d (%f us)",
                    id, payload, location, col, timestamp, tot_msb, tot_lsb, tot_total, tot_us
                    )

        return pd.DataFrame(hit_pd, columns=['readout','Chip ID','payload','location', 'isCol', 'timestamp', 'tot_msb','tot_lsb','tot_total', 'tot_us', 'hittime'])

    def decode_astropix4_hits(self, list_hits: list, printer:bool = False) -> pd.DataFrame:
        """
        Decode 8byte Frames from AstroPix 4
        :param list_hists: List with all hits
        :returns: Dataframe with decoded hits
        """

        hit_pd = []

        for hit in list_hits:
            if len(hit) == self._bytesperhit:
                header, byte1, byte2, byte3, byte4, byte5, byte6, byte7 = hit

                id          = header >> 3
                payload     = header & 0b111
                row         = byte1 >> 3
                col         = ((byte1 & 0b111) << 2) + (byte2 >> 6)

                tsneg1      = (byte2 >> 5) & 0b1
                ts1         = ((byte2 & 0b11111) << 9) + (byte3 << 1) + (byte4 >> 7)
                tsfine1     = (byte4 >> 4) & 0b111
                tstdc1      = ((byte4 & 0b1111) << 1) + (byte5 >> 7)

                tsneg2      = (byte5 >> 6) & 0b1
                ts2         = ((byte5 & 0b111111) << 8) + byte6
                tsfine2     = (byte7 >> 5) & 0b111
                tstdc2      = byte7 & 0b11111

                ts_dec1     = self.gray_to_dec((ts1 << 3) + tsfine1)
                ts_dec2     = self.gray_to_dec((ts2 << 3) + tsfine2)

                if ts_dec2 >= ts_dec1:
                    tot_us      = (ts_dec2 - ts_dec1) / 20
                else:
                    # If TS counter wrapped -> ts_dec2 < ts_dec1
                    tot_us      = (2**17 - ts_dec1 + ts_dec2) / 20

                hit_pd.append([id, payload, row, col, ts1, tsfine1, ts2, tsfine2, tsneg1, tsneg2, tstdc1, tstdc2,
                               ts_dec1, ts_dec2, tot_us])

                if printer:
                    logger.info(
                    "Header: ChipId: %d\tPayload: %d\t"
                    "Row: %d\t Col: %d\t"
                    "TS1: %d\t TS1_fine %d\t"
                    "TS2: %d\t TS2_fine %d\t"
                    "TS1_dec: %d\t TS2_dec %d\t"
                    "Total ToT [us]: %f us",
                    id, payload, row, col, ts1, tsfine1, ts2, tsfine2, ts_dec1, ts_dec2, tot_us
                    )

        #return pd.DataFrame(hit_pd, columns=['id', 'payload', 'row', 'col', 'ts1', 'tsfine1', 'ts2',
        #                                     'tsfine2', 'tsneg1', 'tsneg2', 'tstdc1', 'tstdc2', 'ts_dec1', 'ts_dec2','tot_us'])
        return hit_pd