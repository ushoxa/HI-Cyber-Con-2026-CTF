#!/usr/bin/env python3
"""Whispers in the Margin, step 1: decode space/tab whitespace stego in the .docx.
Each blank-looking paragraph ends in 8 whitespace chars: space=0, tab=1 -> one ASCII byte.
usage: python3 docx_whitespace.py "Those numbers are process counts.docx" """
import re, sys, zipfile
x = zipfile.ZipFile(sys.argv[1]).read("word/document.xml").decode()
out = ""
for p in re.findall(r"<w:p[ >].*?</w:p>", x, re.S):
    s = "".join("\t" if t.group(0) == "<w:tab/>" else t.group(1)
                for t in re.finditer(r"<w:tab/>|<w:t(?: [^>]*)?>(.*?)</w:t>", p, re.S))
    if s.strip() == "" and len(s) >= 8:
        out += chr(int(s[-8:].replace(" ", "0").replace("\t", "1"), 2))
print(out)
