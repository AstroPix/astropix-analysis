#pragma once
#include <functional>
#include "data_structs.h"

std::vector<MatchedHit> rowcolmatch(
    const std::vector<HalfHit>& chip0,
    std::function<bool(int,int)> fts,
    std::function<bool(int,int)> ftot
);
