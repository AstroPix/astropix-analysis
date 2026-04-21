# astropix-analysis
Decoding and analysis of AstroPix V3+

## Decoding AstroPix Data
To decode data taken using the astep-fw git repository use one of the following decoders, depending on your hardware version:
- astropix_v3_decoder.py
    - Used for AstroPix V3 single chip
    - Used for V3 quad chips
- CompairDecoder.py
    - Used for ComPair2 hardware
    - (Very similar to astropix_v3_decoder.py, functionallity will be merged at a later date)
- astropix_v4_decoder.py
    - Used for AstroPix V4 single chip

## AstroPix V3 Row-Column Matching
There are two options for V3 row-column matching:
- rowcolMatching_astropix_v3.py
    - This python script takes command line arguments to do row column matching for astropix V3
    - Supports arguments for multiple chips and multiple lanes
- rowcolmatch/rowcolmatch.cpp
    - Must `make rowcolmatch/rowcolmatch` to create executable
    - Same arguments and logic as rowcolmatching_astropix_v3.py, works much much faster
