clean:
	rm *.hlt
	rm *.log
	rm nohup.out

archive:
	today=$$(date +%Y-%m-%d.%H:%M:%S); \
		zip archives/dexbot_0.2_$$today.zip dexbot/*.py halitesrc/*.py MyBot.py

playoff:
	nohup ./scripts/50run.sh &

run:
	./scripts/runGame.sh

time:
	./scripts/timeit.sh
