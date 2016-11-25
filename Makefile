clean:
	rm *.hlt
	rm *.log

archive:
	today=$$(date +%Y-%m-%d.%H:%M:%S); \
		zip archives/dexbot_0.5.2b_$$today.zip dexbot.config dexbot/*.py halitesrc/*.py MyBot.py

playoff:
	./scripts/50run.sh > playoff.out
	cat playoff.out | grep "rank #1" | grep "DexBot" | wc -l

run:
	./scripts/runGame.sh

runmulti:
	./scripts/runMulti.sh

time:
	./scripts/timeit.sh
