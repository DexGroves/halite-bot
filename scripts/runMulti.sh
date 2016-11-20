#!/bin/bash

if hash python3 2>/dev/null; then
    halite -d "20 35" "python3 MyBot.py" "python3 ReferenceBot.py" "python ReferenceBot.py" "python ReferenceBot.py"
else
    halite -d "50 49" "python MyBot.py" "python ReferenceBot.py" "python ReferenceBot.py" "python ReferenceBot.py"
fi
