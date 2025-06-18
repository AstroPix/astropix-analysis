# Live Decoder and Plotter README

## General Notes
- This live decoder and plotter can be used with a single AstroPix V3 chip, a single V4 chip, or a quad V3 chip, what version is being used needs to be specified when running the script using the '-V' argument
- The name of the input log file needs to be specified when running the script using the '-n' argument
- The general structure of this script is the same for all versions: read in all data currently in log file, decode and plot this data, then start a loop of waiting 10 seconds, reading in new data from the log file, decoding and plotting this new data, then repeating the loop until stopped by a keyboard interupt
- The following show up in the plot: all pixel ToT histogram, all pixels hit map, and count rate as a function of time
- Because the V3 single chip and V3 quad chip don't record row/column matched hits, the hit map for these versions is an estimate based on the distribution of hits in rows and columns for each chip, in these versions the hit map should only be seen as an estimate and, for any more in depth work, verified with row column matching
- The count number above the histogram is the total number of hits after decoding, while the counts number above the hit map is the number of hits after the estimation procedure mentioned above for V3 and the V3 quad chip, therefore for these versions, the two count numbers shouldn't agree exactly
- After a keyboard interupt, a matplotlib window is still present which allows for the saving of the last version of the plot, only after this plot is closed does the script end


## Decoding Implementation
- To avoid rewriting the full decoding scripts, the decoding and writing function is called depending on which chip version is being used, this means that the respective decoding script needs to be in the same directory as this live decoding and plotting script