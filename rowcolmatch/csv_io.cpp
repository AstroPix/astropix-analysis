#include "csv_io.h"
#include <fstream>
#include <sstream>
#include <iostream>

std::vector<HalfHit> CSVReader::readHalfHits(const std::string& filename) {
    std::vector<HalfHit> data;
    std::ifstream file(filename);
    std::string line;

    if (!file.is_open()) {
        throw std::runtime_error("Cannot open file: " + filename);
    }

    // Skip header
    std::getline(file, line);

    while (std::getline(file, line)) {
        std::stringstream ss(line);
        HalfHit h;
        std::string tmp;

        std::getline(ss, tmp, ','); h.layer = std::stoi(tmp);
        std::getline(ss, tmp, ','); h.chipID = std::stoi(tmp);
        std::getline(ss, tmp, ','); h.payload = std::stoi(tmp);
        std::getline(ss, tmp, ','); h.location = std::stoi(tmp);
        std::getline(ss, tmp, ','); h.isCol = std::stoi(tmp);
        std::getline(ss, tmp, ','); h.timestamp = std::stoi(tmp);
        std::getline(ss, tmp, ','); h.tot_total = std::stoi(tmp);
        std::getline(ss, tmp, ','); h.tot_us = std::stod(tmp);
        std::getline(ss, tmp, ','); h.fpga_ts = std::stoll(tmp);

        data.push_back(h);
    }

    return data;
}

void CSVWriter::writeMatchedHits(
    const std::string& filename,
    const std::vector<MatchedHit>& hits
) {
    std::ofstream file(filename);

    if (!file.is_open()) {
        throw std::runtime_error("Cannot open output file: " + filename);
    }

    // Header
    file << "layer,chipID,row,col,row_timestamp,col_timestamp,"
         << "row_tot,col_tot,row_tot_us,col_tot_us,"
         << "row_fpga_ts,col_fpga_ts\n";

    for (const auto& h : hits) {
        file << h.layer << ","
             << h.chipID << ","
             << h.row << ","
             << h.col << ","
             << h.row_timestamp << ","
             << h.col_timestamp << ","
             << h.row_tot << ","
             << h.col_tot << ","
             << h.row_tot_us << ","
             << h.col_tot_us << ","
             << h.row_fpga_ts << ","
             << h.col_fpga_ts << "\n";
    }
}
