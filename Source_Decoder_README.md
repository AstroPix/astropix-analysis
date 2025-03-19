# Source Decoder README

## Document Structure
- Examples in this README are taken from AstroPix v4 data, the same principles are used when decoding v3 data as well, differences are specified in the respective v3 and v4 sections
- A few terms are present that seem somewhat similar but mean different things in the context of this decoding.
- A string of data (or just a string) is defined as one line in the .log file usually looking like\
`2	b'bcbce01091fc044abf04bcbcbcbc...bcbcffff...ffff'`
- A hit of data (or just a hit) is defined as one packet of data that can be completely decoded resulting in information about the row, column, and time over threshold being human readable

## General Notes
- Lines are read in one at a time instead of a large number at once as in previous versions to avoid issue with duplicate lines being read in, this also makes the decoding much faster
- The first check is if the first character of a line is a digit, this avoids trying to decode the first 7 lines which are configuration information
- We split on the string `ffff` instead of `ff` to avoid splitting on an `ff` that might randomly appear in a hit
- We split on `bcbc` instead of the idle byte `bc` for the same reason
- We could use the right_strip() and left_strip() functions instead of splitting but this gets tripped up on a case where a hit randomly appearing in the middle of all of the `ff`s of the string, the only reason to change this is to speed up the decoding but this isn't the current bottleneck
- The stored_split_first_part is present to correct the following problem. Sometimes a hit will get split across two strings of data with the start of the hit being at the very end of the first string and the end of the hit at the very beginning of the next string not preceeded by any idle `bc` bytes. An example of this is taken from data measured during a Barium133 Radioactive Source run:\
`49 b'bcbce01a6dea0d34a506bcbc...bcbcbcbcffff...ffffbcbce082a1170cd0`\
\
`50	b'1303bcbce08ca0d508d28606bcbcbc...bcbce0d4b6470bd8cf01bcbcbcbcbcbcffffffff...`

- Here the hit `e082a1170cd0` is seen at the end of the first string and the hit `1303` is at the beginning of the second. Neither of these are a complete hit of 16 characters, but are split from each other. When recombined, they form the complete hit `e082a1170cd01303` that is 16 characters. stored_split_first_part is used to check if the last hit in a string is less than 16 characters long, if it is, we save that hit and append it to the very front of the next string. 

## Filter Function 
- The filter function first checks for the correct length of a hit, the lower bound is the intrinsic length of a hit (2 times the number of bytes per hit), the upper bound is arbitrarily set to 1000 to avoid trying to decode the first few strings of a source run that generally are not real data and just dumped by the fpga, they look something like this:
`0	b'ff07e0dcdfff0ffeff07e01cfcef0ffeff07e012feff0ff8ff07e002fdf70ffedf07e01affff0ffeff07e09cdcff0dfeff07e092feff0ffeff07e092fdff0f6efb07e082ffbe0ffefd07e042dcff0ffeff07e052fe7f0ffefd07e05cfdff0ffafb07e052ffff0ffeff07e0d2fcff0ffeff07e0dcfeff0bfeff07e0d2fdfe0ffeff07e0c2ffff0ffeff07e0028cbf0bd6bf07e00afeff0ffeff07e012fdfb0ffeff07e006dfff0ffeff07e082fcfb0ffcff07e08afeff0ffeff07e08afdff0ffe9f07e092dfff0fdeff07e052fcff07feff07e04afebf0feeef07e042f9bf0ffeef03e04adfff0ffefe07e0cad4ff0ffeff07e0c2feff0ffeff07e0caf5ff0f7eff07e0d2fffb0ffef707e012bcf707fefd07e01ad6ff0ffeff07e00ad5ff0ffefb07e092fcff0feeff07e09afeff0feeff07e09afddf0ffeff07e08adfbf0feeff07e04c1c240e0e9706e0481a25048e5e05e052fdff0ffefd07e05abfff0ffeff05e0dadcff0feeff07e0d2beff0bfeff07e0cc1dbb008cdf05e0caffff0ffeff07e00afcef0ffeef07e006feff0ffeff07e01afdff0ffeff07e08adcff0ffeff07e086feff0ffeff07e086fdff0ffaff07e09afff70feeff07e04afcff0e7eff06e05afeff0ffebf07e04afdff0ffeff07e046ffff0ffefd07e0c6fcff0ffeff07e0cafeff0ffeff07e0dafdfd0ffeff07e0daffff0bfeff07e0007c140a3c4d07e006fdf30f6eff07e09afcf70ffeff07e086ffbe0ffeff07e05ad4ff0ffeff07e046beff0ffeff07e05afdff0ffeff07e0dafeff0ffeff07e0c6fdef0ffeff07e0c6d7fe0ffeff06e01afcff0efeff07e086fcff0ffeff07e098fd46067eba00e090ffe90cfc9a07e046fcff0ffeff07e046fdff0ffeff07e0c6fefe0ffeff07e006fcff0ffefe07e0c83f95039e9f03e050aaf30a548901e008a9d40d54f002ffff...`
- In general the filter function works by looking from right to left on a string and checking the correct length (2 * bytes per hit) for the correct header
- There are three other checks the filter function performs to correcly pass the typical form of a hit, and three other forms that aren't as common
1. If the length of the string is the correct length and starts with the correct header it is identified as a hit and passed
2. If the string is longer than the correct length but the correct header appears the correct length from the end of the string, that part of the string is identified as a hit, passed and the rest of the string is sent through the filter function again, this helps catch the following two cases:\
 `e09022e107921c06e08c239605105601` where two hits (both starting with the header `e0`) are directly next to each other not padded by any idle bytes, both hits will eventually get passed by the filter function\
 `e0d2fc1903fe0d4bf6e01dcf106` here the second hit (starting with the header `e0`) overwrites part of the first hit, the second hit will get passed by the filter function while the cutoff first hit will eventually get filtered out
3. If the string is longer than the correct length and the last two characters are `bc`, then the filter function takes of the `bc` and feeds the resulting string back into the filter function, this helps catch the last case:\
`e01265ca00b2fb00bce000ca200e44b300` here are two hits (both starting with the header `e0`) where the second hit will get correctly passed by the previous check, then the remaining string `e01265ca00b2fb00bc` will get `bc` taken off from the end and put back into the filter function where it will then be passed as a hit


## AstroPix v4
- For a chip ID of 0 and a payload of 7, the v4 header is `e0` (payload is bytes per hit -1 )
- There are 8 bytes per hit, which means there are 16 characters per hit


## AstroPix v3
- For a chip ID of 0 and a payload of 4, the v3 header is `20` (payload is bytes per hit -1 )
- There are 5 bytes per hit, which means there are 10 characters per hit
- Because the row readout is seperate from the column readout, most "full hits" (a row and a column) are back to back, this doesn't cause any issues because of the second check in the filter function
- The above behavior of v3 (row hits and column hits usually not being seperated by any `bc` idle bytes) does impact how the split hit issue is addressed. Now, for v3 we are looking for anything less that 2 * characters_per_hit in the last hit of the string instead of just 1 * characters_per_hit as seen in v4