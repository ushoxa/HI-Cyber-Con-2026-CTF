#!/bin/sh
# usage: sh solve.sh <dir containing chall.jpg and the docx> <outdir>
KEY=$(python3 -I "$(dirname "$0")/docx_whitespace.py" "$1/Those numbers are process counts.docx")
echo "steghide key from docx whitespace: $KEY"
steghide extract -sf "$1/chall.jpg" -p "$KEY" -xf "$2/steghide_extracted.txt" -f
cat "$2/steghide_extracted.txt"; echo
