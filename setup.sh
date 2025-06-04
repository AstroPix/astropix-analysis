#!/bin/bash

# See this stackoverflow question
# http://stackoverflow.com/questions/59895/getting-the-source-directory-of-a-bash-script-from-within
# for the magic in this command
SETUP_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Base package root. All the other relevant folders are relative to this
# location.
export ASTROPIX_ANALYSIS_ROOT=$SETUP_DIR

# Add the root folder to the $PYTHONPATH so that we can effectively import
# the relevant modules.
export PYTHONPATH=$ASTROPIX_ANALYSIS_ROOT:$PYTHONPATH

# Add the bin folder to the $PATH environmental variable so that we can run the
# analysis scripts.
export PATH=$ASTROPIX_ANALYSIS_ROOT/bin:$PATH

# Print the new environment for verification.
echo "ASTROPIX_ANALYSIS_ROOT ->" $ASTROPIX_ANALYSIS_ROOT
echo "PATH ->" $PATH
echo "PYTHONPATH ->" $PYTHONPATH