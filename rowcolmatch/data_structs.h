#pragma once

struct HalfHit {
    int layer;
    int chipID;
    int payload;
    int location;     // row or column index
    int isCol;        // 0 = row, 1 = col
    int timestamp;
    int tot_total;
    double tot_us;
    long long fpga_ts;
};

struct MatchedHit {
    int layer;
    int chipID;
    int row;
    int col;
    int row_timestamp;
    int col_timestamp;
    int row_tot;
    int col_tot;
    double row_tot_us;
    double col_tot_us;
    long long row_fpga_ts;
    long long col_fpga_ts;
};
