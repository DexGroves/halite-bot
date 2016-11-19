clean:
	rm nohup.out
	rm *.hlt
	rm *.log

archive:
	today=$$(date +%Y-%m-%d.%H:%M:%S); \
		zip archives/dexbot_0.1_$$today.zip dexbot/*.py halitesrc/*.py MyBot.py

playoff:
	nohup ./50run.sh &
