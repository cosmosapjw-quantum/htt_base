"""Extract defs (full body, to blank line) and theorem statements (to first ':=')."""
import re, sys
src = open(sys.argv[1]).read().split("\n")
out, buf, mode = [], [], None
for line in src + [""]:
    m = re.match(r"^(theorem|noncomputable def|def|abbrev) ", line)
    if m and mode is None:
        mode, buf = ("thm" if m.group(1) == "theorem" else "def"), []
    if mode == "def":
        if line.strip() == "":
            out.append("\n".join(buf)); mode = None
        else:
            buf.append(line)
    elif mode == "thm":
        buf.append(line)
        if ":=" in line:
            txt = "\n".join(buf); out.append(txt[:txt.index(":=")].rstrip()); mode = None
print("\n\n".join(out))
