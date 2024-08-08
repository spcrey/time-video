import argparse
import time
import shutil

def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", type=str, required=True)
    parser.add_argument("--output_dir", type=str, required=True)
    args = parser.parse_args()
    return args

def main():
    args = get_args()
    time.sleep(5)
    input_dir = "RealBasicVSR-master/demo_video.mp4"
    shutil.copy(input_dir, args.output_dir)

if __name__ == "__main__":
    main()
