# QuadChip Decoder README

## Document Structure
- The format of this decoder is similar to the single chip decoder found in New_Source_Decoder.py and documented in the Source_Decoder_README, it is a good idea to be generally familiar with the way that decoding works before looking more into the quad chip decoding 
- A few terms are present that seem somewhat similar but mean different things in the context of this decoding.
- A string of data (or just a string) is defined as one line in the .log file usually looking like\
`2025-03-05 17:11:32,602:602.__main__.INFO: b'0a0104007f07fa0000000009010b040160000000000...ffff`
- A hit of data (or just a hit) is defined as one packet of data that can be completely decoded resulting in information about the row, column, and time over threshold being human readable



## General Notes
- We start looking for actual data after the `INFO:` part of the line
- We then look for the first character of the line to be `b` to insure we are looking at lines of data
- Similar to single chip decoding, we split on all appearances of `ffff`
- To find all occurances of the correct ASTEP header `0a01` we search for every index where this text appears
- Using this list of indexes, we check to make sure all of them are 22 characters appart (the length of a complete string)
- If they are less than 22 characters apart, we only include the second instance of `0a01` because we assume the first hit got written over by the second hit
- Then the list of correct indexes is itterated over and the corresponding hits are passed through the decoding function with the decoding order and line number passed into the function too
- The main decoding and writing portion was changed to be a function acting on one line at a time so it can be called in the live decoder, this shouldn't impact any performance in this script
- For a binary data file, this is much simpler, we simply read in 1024 bytes at a time, look for the index of `0a01` in hex, check if they are 11 bytes apart, then act on the resulting strings of data
- Choosing a binary input file is decided when running the file using the argparse package with arguement '-b'

## Decode Function 
- This decoding function is built on top of the v3 decoding function found in astropix-python
- Initially the astep header, layer ID, v3 undecoded hit, and fpga time step are seperated
- Then the v3 hit is decoded using the previously mentioned v3 decoding function
- Lastly, the relevant values are returned in the order that has previously been used: `'dec_ord', 'readout', 'layer', 'chipID', 'payload', 'location', 'isCol', 'timestamp', 'tot_msb', 'tot_lsb', 'tot_total', 'tot_us', 'fpga_ts'`