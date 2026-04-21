import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors
import argparse

def mkplots(m, m2=None):
  # Plot 1
  plt.hist(m.row_timestamp-m.col_timestamp, bins=np.arange(-10, 11, 1))
  if m2 is not None: plt.hist(m2.row_timestamp-m2.col_timestamp, bins=np.arange(-10, 11, 1))
  plt.yscale("log")
  plt.grid(True, "both")
  plt.xlabel("Row TS - Col TS")
  plt.ylabel("Matched hits")
  plt.grid(True, "both"); plt.show()
  # Plot 2
  plt.hist(m.row_tot-m.col_tot, bins=np.arange(-50, 50, 1))
  if m2 is not None: plt.hist(m2.row_tot-m2.col_tot, bins=np.arange(-50, 50, 1))
  plt.yscale("log")
  plt.grid(True, "both")
  plt.xlabel("Row ToT - Col ToT")
  plt.ylabel("Matched hits")
  plt.grid(True, "both"); plt.show()
  # Plot 3
  plt.hist(m.row_fpga_ts-m.col_fpga_ts, bins=np.arange(-500, 50, 1))
  if m2 is not None: plt.hist(m2.row_fpga_ts-m2.col_fpga_ts, bins=np.arange(-500, 50, 1))
  plt.yscale("log")
  plt.grid(True, "both")
  plt.xlabel("Row FPGA TS - Col FPGA TS")
  plt.ylabel("Matched hits")
  plt.grid(True, "both"); plt.show()
  # Plot 4
  plt.scatter(m.row_tot, m.row_tot-m.col_tot, s=.1)
  if m2 is not None: plt.scatter(m2.row_tot, m2.row_tot-m2.col_tot, s=.1)
  plt.xlabel("Row ToT")
  plt.ylabel("Row ToT - Col ToT")
  plt.grid(True, "both"); plt.show()
  # Plot 5
  if m2 is None: plt.hist2d(m.row_timestamp - m.col_timestamp, m.row_tot-m.col_tot, (np.arange(-4, 6, 1), np.arange(-4000, 4300, 10)), norm=matplotlib.colors.LogNorm())
  else: plt.hist2d(m2.row_timestamp - m2.col_timestamp, m2.row_tot-m2.col_tot, (np.arange(-4, 6, 1), np.arange(-4000, 4300, 10)), norm=matplotlib.colors.LogNorm())
  plt.colorbar()
  plt.xlabel("Row TS - Col TS")
  plt.ylabel("Row ToT - Col ToT")
  plt.grid(True, "both"); plt.show()

  

def rowcolmatch(chip0, fts=lambda x,y: x-y==0 or x-y==1, ftot=lambda x,y: x-y>6 and x-y<15):
  """
  Performs Row-Col matching for AstroPix V3 (A-STEP firmware)
  :param chip0: pandas DataFrame of decoded hits
  :param fts: function (int, int) -> bool, condition on the row and col TS to match half-hits
  :param ftot: function (int, int) -> bool, condition on the row and col ToT_total value to match hits (default: True)
  :retuns: pandas DataFrame of matched hits
  """
  #outdict = {"dec_ord":[], "readout":[], "layer":[], "chipID":[], "payload":[], "location":[], "isCol":[], "timestamp":[], "tot_msb":[], "tot_lsb":[], "tot_total":[], "tot_us":[], "fpga_ts":[]}
  outdict = {"layer":[], "chipID":[], "row":[], "col":[], "row_timestamp":[], "col_timestamp":[], 
              "row_tot":[], "col_tot":[], "row_tot_us":[], "col_tot_us":[], "row_fpga_ts":[], "col_fpga_ts":[]}
  linenb = 0
  while linenb < len(chip0):
    index = chip0.index[linenb]
    #print(f"line={linenb}, i={index}, isCol={chip0.isCol[index]}, ts={chip0.timestamp[index]}")
    if chip0.isCol[index] == 0: # Try to match this row to a col
      foundcol = False
      i = linenb + 1
      while i < len(chip0) and (not(foundcol) or chip0.isCol[chip0.index[i]]==1):
        colindex = chip0.index[i]
        if chip0.isCol[colindex]==1: # Skip other rows
          if not(foundcol): foundcol=True
          #print(chip0.timestamp[index], chip0.index[i], chip0.isCol[chip0.index[i]], chip0.timestamp[chip0.index[i]])
          if fts(chip0.timestamp[index], chip0.timestamp[colindex]) and ftot(chip0.tot_total[index], chip0.tot_total[colindex]):
            #print(f"{index}\t{chip0.index[i]}\t{chip0.timestamp[index]}\t{chip0.timestamp[chip0.index[i]]}\t{chip0.tot_total[index]}\t{chip0.tot_total[chip0.index[i]]}")
            outdict["layer"].append(chip0.layer[index])
            outdict["chipID"].append(chip0.chipID[index])
            outdict["row"].append(chip0.location[index])
            outdict["col"].append(chip0.location[colindex])
            outdict["row_timestamp"].append(chip0.timestamp[index])
            outdict["col_timestamp"].append(chip0.timestamp[colindex])
            outdict["row_tot"].append(chip0.tot_total[index])
            outdict["col_tot"].append(chip0.tot_total[colindex])
            outdict["row_tot_us"].append(chip0.tot_us[index])
            outdict["col_tot_us"].append(chip0.tot_us[colindex])
            outdict["row_fpga_ts"].append(chip0.fpga_ts[index])
            outdict["col_fpga_ts"].append(chip0.fpga_ts[colindex])
        i += 1
    linenb += 1 # Skip cols
  return pd.DataFrame.from_dict(outdict)

if __name__ ==  "__main__":
  parser = argparse.ArgumentParser("Row-Column matching script for AstroPix v3")
  parser.add_argument("filename", help="Name of the decoded .csv file")
  parser.add_argument("-q", "--quiet", action="store_true", help="Suppresses output")
  parser.add_argument("-l", "--layers", type=int, default=3, help="Number of layers/lanes, default=3")
  parser.add_argument("-c", "--chips", type=int, default=4, help="Number of chips per layer/lane, default=4")
  parser.add_argument("--mints", type=int, default=0, help="Minimum halfhit Timestamp difference (row-col) to match, default=0")
  parser.add_argument("--maxts", type=int, default=1, help="Minimum halfhit Timestamp difference (row-col) to match, default=1")
  parser.add_argument("--mintot", type=int, default=6, help="Minimum halfhit ToT difference (row-col) to match, default=7")
  parser.add_argument("--maxtot", type=int, default=15, help="Minimum halfhit ToT difference (row-col) to match, default=14")
  args = parser.parse_args()
  # Read data
  data = pd.read_csv(args.filename)
  dataf = data[(data.payload==4)&(data.location<35)] # Filter corrupted data
  if not args.quiet:
    print(f"{len(data)} decoded halfhits read, {len(dataf)} halfhits are valid ({100*len(dataf)/len(data):.2f}%).")
  # Row-col match per chip
  output = []
  for layer in range(args.layers):
    for chip in range(args.chips):
      datac = dataf[(dataf.chipID==chip)&(dataf.layer==layer)]
      output.append(rowcolmatch(datac, fts=lambda x,y: x-y>=args.mints and x-y<=args.maxts, ftot=lambda x,y: x-y>=args.mintot and x-y<=args.maxtot))
      if not args.quiet:
        print(f"Layer {layer}, Chip {chip}: {len(datac)} halfhits found, {len(output[-1])} hits matched ({100*len(output[-1])*2/max(1, len(datac)):.2f}%).")
  pd.concat(output).to_csv(f"{args.filename[:-4]}_matched.csv")



if __name__ == "__main__" and False: # Set to True to run as a script
  print("Loading data")
  d = pd.read_csv("/Users/alaviron/AstroPix/data/20250624-172917.csv")
  d2 = d[(d.payload==4)&(d.location<35)] # Filter rubbish
  print(f"{100*(1-len(d2)/len(d))}% of the data has been removed as rubbish")
  print("Select Chip ID = 0")
  chip0 = d2[(d2.chipID==0)&(d2.layer==1)]
  print("Perform row-col matching: Only selection is within 5 TS units and row matched within the next col delivery")
  m = rowcolmatch(chip0, fts=lambda x,y: abs(x-y)<5, ftot=lambda x,y: True)
  mkplots(m)
  print("Perform row-col matching: Delta TS = 0 or 1")
  m2 = rowcolmatch(chip0, lambda x,y: x-y==0 or x-y==1, ftot=lambda x,y: True)
  mkplots(m, m2)
  print("Perform row-col matching: Delta TS = 0 or 1, -10 < Delta ToT < 30")
  m3 = rowcolmatch(chip0, lambda x,y: x-y==0 or x-y==1, lambda x,y: x-y>6 and x-y<15)
  mkplots(m, m3)
