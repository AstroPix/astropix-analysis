#include <vector>
#include <functional>
#include "data_structs.h"

std::vector<MatchedHit> rowcolmatch(
    const std::vector<HalfHit>& chip0,
    std::function<bool(int,int)> fts,
    std::function<bool(int,int)> ftot
) {
    std::vector<MatchedHit> output;

    for (size_t linenb = 0; linenb < chip0.size(); ++linenb) {
        const auto& rowHit = chip0[linenb];

        if (rowHit.isCol == 0) {
            bool foundcol = false;

            for (size_t i = linenb + 1;
                 i < chip0.size() && (!foundcol || chip0[i].isCol == 1);
                 ++i) {

                const auto& colHit = chip0[i];
                if (colHit.isCol == 1) {
                    foundcol = true;

                    if (fts(rowHit.timestamp, colHit.timestamp) &&
                        ftot(rowHit.tot_total, colHit.tot_total)) {

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
            }
        }
    }

    return output;
}

