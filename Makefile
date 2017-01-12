clean:
	rm *.hlt
	rm *.log

archive:
	today=$$(date +%Y-%m-%d.%H:%M:%S); \
		zip archives/dexbot_0.16b_$$today.zip dexlib/*.py halitesrc/*.py MyBot.py

playoff:
	./scripts/50run.sh > playoff.out
	cat playoff.out | grep "rank #1" | grep "DexBot" | wc -l

run:
	./scripts/runGame.sh

solo:
	halite -d "30 30" "python3 MyBot.py"

rj:
	halite -d "25 25" "python3 MyBotBattleMode1.py" "python3 MyBot.py"

runmulti:
	./scripts/runMulti.sh

time:
	./scripts/timeit.sh
