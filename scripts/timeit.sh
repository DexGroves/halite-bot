#!/bin/bash

if hash python3 2>/dev/null; then
    time halite -d "25 35" -s 12345 "python3 MyBot.py" "python3 ReferenceBot.py"
else
    time halite -d "25 35" -s 12345 "python MyBot.py" "python ReferenceBot.py"
fi
