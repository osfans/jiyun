#!/usr/bin/env python3
"""Merge all NN.md files back into 集韻.md"""

import glob

# Collect files in order
md_files = sorted(glob.glob("[0-9][0-9].md"))
if not md_files:
    raise SystemExit("No NN.md files found.")

print(f"Found {len(md_files)} files: {md_files}")

# Read and concatenate
parts = []
for path in md_files:
    with open(path, encoding="utf-8") as f:
        parts.append(f.read())

# Write merged file
output_path = "jiyun.md"
with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n".join(parts))

print(f"Merged into {output_path}")
