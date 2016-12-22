clean:
	rm *.hlt
	rm *.log

archive:
	today=$$(date +%Y-%m-%d.%H:%M:%S); \
		zip archives/dexbot_0.7.1_$$today.zip configs/* dexbot.config dexbot/*.py halitesrc/*.py MyBot.py

playoff:
	./scripts/50run.sh > playoff.out
	cat playoff.out | grep "rank #1" | grep "DexBot" | wc -l

run:
	./scripts/runGame.sh

rj:
	halite -d "25 25" "python3 MyBotBattleMode1.py" "python3 MyBot.py"

runmulti:
	./scripts/runMulti.sh

time:
	./scripts/timeit.sh
