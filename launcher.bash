#!/bin/bash
adddate() {
    while IFS= read -r line; do
        printf '%s %s\n' "$(date)" "$line";
    done
}

if pgrep -a python | grep 'main.py' &>/dev/null; then
	echo 'already running'
else
	jack_control start
	cd '/windows/Users/Annalisa Baronetto/PycharmProjects/GastroDigitalShirt - Code for Recording/'
	python3 main.py 2>&1 | adddate | tee "/home/abaronetto/Desktop/run_$(date +"%F %T").log"
fi
