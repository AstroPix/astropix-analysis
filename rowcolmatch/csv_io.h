#pragma once
#include <vector>
#include <string>
#include "data_structs.h"

class CSVReader {
public:
    static std::vector<HalfHit> readHalfHits(const std::string& filename);
};

class CSVWriter {
public:
    static void writeMatchedHits(
        const std::string& filename,
        const std::vector<MatchedHit>& hits
    );
};
