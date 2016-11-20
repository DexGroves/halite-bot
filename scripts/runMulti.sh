#!/bin/bash

if hash python3 2>/dev/null; then
    halite -d "55 49" "python3 MyBot.py" "python3 ReferenceBot.py" "python3 ReferenceBot.py" "python3 ReferenceBot.py" "python3 ReferenceBot.py" "python3 ReferenceBot.py"
else
    halite -d "55 49" "python MyBot.py" "python ReferenceBot.py" "python ReferenceBot.py" "python ReferenceBot.py" "python ReferenceBot.py" "python ReferenceBot.py"
fi
