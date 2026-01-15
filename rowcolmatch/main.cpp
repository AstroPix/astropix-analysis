#include <iostream>
#include <vector>
#include <string>
#include <cstring>
#include "data_structs.h"
#include "rowcolmatch.h"
#include "csv_io.h"

static void usage() {
    std::cout <<
    "Usage: rowcolmatch <file.csv> [options]\n\n"
    "Options:\n"
    "  -q, --quiet           Suppress output\n"
    "  -l, --layers <int>    Number of layers (default: 3)\n"
    "  -c, --chips <int>     Number of chips per layer (default: 4)\n"
    "  --mints <int>         Min TS difference (default: 0)\n"
    "  --maxts <int>         Max TS difference (default: 1)\n"
    "  --mintot <int>        Min ToT difference (default: 6)\n"
    "  --maxtot <int>        Max ToT difference (default: 15)\n";
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: rowcolmatch <file.csv>\n";
        return 1;
    }

    std::string filename;
    bool quiet = false;
    int layers = 3, chips = 4;
    int mints = 0, maxts = 1;
    int mintot = 6, maxtot = 15;

    // --- Parse arguments ---
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];

        if (arg == "-q" || arg == "--quiet") quiet = true;
        else if (arg == "-l" || arg == "--layers") layers = std::stoi(argv[++i]);
        else if (arg == "-c" || arg == "--chips") chips = std::stoi(argv[++i]);
        else if (arg == "--mints") mints = std::stoi(argv[++i]);
        else if (arg == "--maxts") maxts = std::stoi(argv[++i]);
        else if (arg == "--mintot") mintot = std::stoi(argv[++i]);
        else if (arg == "--maxtot") maxtot = std::stoi(argv[++i]);
        else if (arg[0] != '-') filename = arg;
        else {
            usage();
            return 1;
        }
    }

    if (filename.empty()) {
        usage();
        return 1;
    }

    auto data = CSVReader::readHalfHits(filename);

    // Filter corrupted data
    std::vector<HalfHit> dataf;
    for (const auto& h : data) {
        if (h.payload == 4 && h.location < 35) {
            dataf.push_back(h);
        }
    }

    if (!quiet) {
        double pct = data.empty() ? 0.0 :
            100.0 * dataf.size() / data.size();
        std::cout << data.size() << " decoded halfhits read, "
                  << dataf.size() << " valid ("
                  << pct << "%)\n";
    }

    std::vector<MatchedHit> allMatches;

    for (int layer = 0; layer < layers; ++layer) {
        for (int chip = 0; chip < chips; ++chip) {
            std::vector<HalfHit> datac;
            for (const auto& h : dataf) {
                if (h.layer == layer && h.chipID == chip)
                    datac.push_back(h);
            }

            auto matches = rowcolmatch(
                datac,
                [&](int x, int y) { return x - y >= mints && x - y <= maxts; },
                [&](int x, int y) { return x - y >= mintot && x - y <= maxtot; }
            );

            if (!quiet) {
                double pct = datac.empty() ? 0.0 :
                    100.0 * matches.size() * 2.0 / datac.size();

                std::cout << "Layer " << layer
                          << ", Chip " << chip
                          << ": " << datac.size()
                          << " halfhits found, "
                          << matches.size()
                          << " hits matched ("
                          << pct << "%)\n";
            }

            allMatches.insert(allMatches.end(),
                              matches.begin(),
                              matches.end());
        }
    }

    CSVWriter::writeMatchedHits(
        filename.substr(0, filename.size() - 4) + "_matched.csv",
        allMatches
    );

    return 0;
}



