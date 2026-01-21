#include <vector>
#include <functional>
#include <iostream>
#include "data_structs.h"

std::vector<MatchedHit> rowcolmatch(
    const std::vector<HalfHit>& chip0,
    std::function<bool(int,int)> fts,
    std::function<bool(int,int)> ftot)
{
    std::vector<MatchedHit> output;

    for (size_t linenb = 0; linenb < chip0.size(); ++linenb) {
        const auto& rowHit = chip0[linenb];
        //std::cout << rowHit.toStr() << std::endl;

        if (rowHit.isCol == 0) {
            bool foundcol = false;
            //size_t i = linenb + 1;
            //std::cout << "Matching " << linenb << "\nrow: " << rowHit.toStr() << std::endl;
            //while (i < chip0.size() && (!foundcol || chip0[i].isCol == 1)) {
            for (size_t i = linenb + 1;
                 i < chip0.size() && (!foundcol || chip0[i].isCol == 1);
                 ++i) {

                const auto& colHit = chip0[i];
                //std::cout << i << " col: " << colHit.toStr() << " foundcol=" << foundcol << std::endl;
                if (colHit.isCol == 1) {
                    if (!foundcol) foundcol = true;

                    if (fts(rowHit.timestamp, colHit.timestamp) &&
                        ftot(rowHit.tot_total, colHit.tot_total)) {
                        //std::cout << "match!" << std::endl;
                        output.push_back({
                            rowHit.layer,
                            rowHit.chipID,
                            rowHit.location,
                            colHit.location,
                            rowHit.timestamp,
                            colHit.timestamp,
                            rowHit.tot_total,
                            colHit.tot_total,
                            rowHit.tot_us,
                            colHit.tot_us,
                            rowHit.fpga_ts,
                            colHit.fpga_ts
                        });
                    }
                }
                //++i;
            }
        }
        //if (linenb > 100) return output;
    }

    return output;
}

