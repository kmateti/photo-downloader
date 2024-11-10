from pathlib import Path
import argparse
from datetime import datetime

def main(folder: Path):
    print(folder)
    image_files = folder.rglob("*.jpg")
    for file in image_files:
        if (file.name.startswith("img")):
            new_name = file.parent.stem + "_" + file.name
            print(f"{file.name} --> {new_name}")
            file.rename(file.parent.joinpath(new_name))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Copy and rename images and videos based on folder naming convention.')
    parser.add_argument('folder',
                    help='the root of the source of images and videos')
    
    args = parser.parse_args()
    main(Path(args.folder))
    
