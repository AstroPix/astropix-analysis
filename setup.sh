#!/bin/bash

# See this stackoverflow question
# http://stackoverflow.com/questions/59895/getting-the-source-directory-of-a-bash-script-from-within
# for the magic in this command
SETUP_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

#
# Base package root. All the other releavant folders are relative to this
# location.
#
export ASTROPIX_ANALYSIS_ROOT=$SETUP_DIR

#
# Data directory that can be used inside the code. To be defined by each users 
#
export ASTROPIX_DATA=

#
# Add the root folder to the $PYTHONPATH so that we can effectively import
# the relevant modules.
#
export PYTHONPATH=$ASTROPIX_ANALYSIS_ROOT:$PYTHONPATH
