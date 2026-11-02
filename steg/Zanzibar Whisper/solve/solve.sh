#!/bin/sh
# Zanzibar Whisper - steghide with an empty passphrase.   usage: sh solve.sh zanzibar_whisper.jpg outdir
steghide info "$1" -p ""
steghide extract -sf "$1" -p "" -xf "$2/zanzibar_flag2.txt" -f
cat "$2/zanzibar_flag2.txt"
