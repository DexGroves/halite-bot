#!/bin/bash

if hash python3 2>/dev/null; then
    halite -d "25 35" "python3 MyBot.py" "python3 ReferenceBot.py"
else
    halite -d "25 35" "python MyBot.py" "python ReferenceBot.py"
fi
