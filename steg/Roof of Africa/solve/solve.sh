#!/bin/sh
# Roof of Africa - steghide key = Kilimanjaro's height in metres (5895).
# usage: sh solve.sh roof_of_africa.jpg outdir
steghide info "$1" -p 5895
steghide extract -sf "$1" -p 5895 -xf "$2/steghide_extracted.txt" -f
cat "$2/steghide_extracted.txt"; echo
