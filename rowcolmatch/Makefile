CXX ?= c++
CXXFLAGS = -std=c++17 -O2 -Wall -Wextra -pedantic
LDFLAGS =

SRC = main.cpp csv_io.cpp rowcolmatch.cpp
OBJ = $(SRC:.cpp=.o)
BIN = rowcolmatch

all: $(BIN)

$(BIN): $(OBJ)
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LDFLAGS)

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -f $(OBJ) $(BIN)

.PHONY: all clean
