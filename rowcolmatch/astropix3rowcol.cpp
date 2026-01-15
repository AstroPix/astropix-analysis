#include <vector>
#include <functional>
#include <string>

struct HalfHit {
    int layer;
    int chipID;
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

std::vector<MatchedHit> rowcolmatch(
    const std::vector<HalfHit>& chip0,
    std::function<bool(int,int)> fts =
        [](int x, int y) { return (x - y == 0) || (x - y == 1); },
    std::function<bool(int,int)> ftot =
        [](int x, int y) { return (x - y > 6) && (x - y < 15); }
) {
    std::vector<MatchedHit> output;

    size_t linenb = 0;
    while (linenb < chip0.size()) {
        const HalfHit& rowHit = chip0[linenb];

        // Try to match only rows
        if (rowHit.isCol == 0) {
            bool foundcol = false;
            size_t i = linenb + 1;

            while (i < chip0.size() &&
                   (!foundcol || chip0[i].isCol == 1)) {

                const HalfHit& colHit = chip0[i];

                if (colHit.isCol == 1) {
                    if (!foundcol)
                        foundcol = true;

                    if (fts(rowHit.timestamp, colHit.timestamp) &&
                        ftot(rowHit.tot_total, colHit.tot_total)) {

                        MatchedHit mh;
                        mh.layer = rowHit.layer;
                        mh.chipID = rowHit.chipID;
                        mh.row = rowHit.location;
                        mh.col = colHit.location;
                        mh.row_timestamp = rowHit.timestamp;
                        mh.col_timestamp = colHit.timestamp;
                        mh.row_tot = rowHit.tot_total;
                        mh.col_tot = colHit.tot_total;
                        mh.row_tot_us = rowHit.tot_us;
                        mh.col_tot_us = colHit.tot_us;
                        mh.row_fpga_ts = rowHit.fpga_ts;
                        mh.col_fpga_ts = colHit.fpga_ts;

                        output.push_back(mh);
                    }
                }
                ++i;
            }
        }
        ++linenb; // Skip cols
    }

    return output;
}

#include <iostream>
#include <cstdlib>

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: rowcolmatch <filename>\n";
        return 1;
    }

    int layers = 3;
    int chips = 4;
    int mints = 0;
    int maxts = 1;
    int mintot = 6;
    int maxtot = 15;

    // Assume data has already been read from CSV
    std::vector<HalfHit> data;   // decoded halfhits
    std::vector<HalfHit> dataf;  // filtered halfhits

    // Example filtering (payload & location filtering omitted for brevity)
    for (const auto& h : data) {
        if (h.location < 35) {
            dataf.push_back(h);
        }
    }

    std::vector<MatchedHit> allMatches;

    for (int layer = 0; layer < layers; ++layer) {
        for (int chip = 0; chip < chips; ++chip) {
            std::vector<HalfHit> datac;
            for (const auto& h : dataf) {
                if (h.layer == layer && h.chipID == chip) {
                    datac.push_back(h);
                }
            }

            auto matches = rowcolmatch(
                datac,
                [&](int x, int y) {
                    int d = x - y;
                    return d >= mints && d <= maxts;
                },
                [&](int x, int y) {
                    int d = x - y;
                    return d >= mintot && d <= maxtot;
                }
            );

            std::cout << "Layer " << layer
                      << ", Chip " << chip
                      << ": " << datac.size()
                      << " halfhits found, "
                      << matches.size()
                      << " hits matched\n";

            allMatches.insert(allMatches.end(),
                              matches.begin(),
                              matches.end());
        }
    }

    // Write allMatches to CSV (not shown)

    return 0;
}




