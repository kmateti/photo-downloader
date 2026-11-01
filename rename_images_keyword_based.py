from pathlib import Path

input_dir = "E:/kiron/Pictures/Albums/2025/2025-01-20-Cozumel"

keyword = "20250122_PXL_"
old_files = list(Path(input_dir).glob(f"{keyword}*.jpg"))
print(len(old_files))

new_files = [file.parent.joinpath(file.stem.replace(keyword, "") + file.suffix) for file in old_files ]
print(new_files)

for old_file, new_file in zip(old_files, new_files):
    old_file.rename(new_file)