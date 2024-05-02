import glob
import os

DATA_FOLDER = "temp/"

def add_prefix_to_lines(filepath):
    with open(filepath, 'r+', encoding='UTF-8') as f:
        lines = f.readlines()
        f.seek(0)
        for line in lines:
            if line.strip() and not line.startswith("0|"):
                f.write("0|" + line)
            else:
                f.write(line)
        f.truncate()
        
def main():
    filepaths_list = glob.glob(os.path.join(DATA_FOLDER, "*.txt"))
    for filepath in filepaths_list:
        add_prefix_to_lines(filepath)

if __name__ == "__main__":
    main()