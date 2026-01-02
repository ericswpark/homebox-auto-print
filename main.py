import argparse
import os
import subprocess
import time

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer


def process_image(src_path, font, asset_id, target_path):
    os.system(
        # Start
        f"magick '{src_path}' "
        # Crop image down to size
        "-crop 140x140+30+30 "
        # Extend bottom
        "-background white -gravity South -splice 0x40 +repage "
        # Set parameters for text on bottom
        f"-gravity South -pointsize 35 -fill black -font '{font}' "
        # Add text to bottom
        f"-annotate +0+0 '{asset_id}' "
        # Resize to fit label
        f"-interpolate Integer -filter point -resize x120 "
        # Output to target path
        f"{target_path}"
    )


def print_image(cable, cut, image_path):
    image_arg = f"--image={image_path}"
    args = [
        "ptouch-print",
    ]

    if not cut:
        args.append("--chain")

    args.append(image_arg)

    if cable:
        args.append("--pad=80")
        args.append(image_arg)

    try:
        subprocess.run(args, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"ptouch-print failed with error code {e.returncode}: {e.stderr}")
    except Exception as e:
        print(f"An error occurred while printing: {e}")


class EventHandler(FileSystemEventHandler):
    def __init__(self, font, remove, cable, cut):
        self.font = font
        self.remove = remove
        self.cable = cable
        self.cut = cut

    def on_any_event(self, event: FileSystemEvent) -> None:
        # Check if file being modified is a Homebox label image
        src_path = str(event.src_path)
        if (
            "label-" not in src_path
            or not src_path.endswith(".png")
            or event.is_directory
            or event.is_synthetic
        ):
            return

        # Ignore all events except for modified
        if event.event_type != "modified":
            return

        # Extract asset ID from string
        asset_id = src_path.split("label-")[1].split(".png")[0]
        # If repeated copy, remove the copy number
        if "(" in asset_id:
            asset_id = asset_id.split("(")[0]

        file_name = src_path.split("/")[-1]

        print(f"Detected asset {asset_id} at {file_name}")

        # Use Imagemagick to crop image, then append asset ID underneath
        target_path = os.path.join(
            os.path.dirname(src_path), f"{asset_id}-processed.png"
        )
        print("- Processing with Imagemagick...", end="")
        try:
            process_image(src_path, self.font, asset_id, target_path)
            print("done")
        except Exception as e:
            print("failed")
            print(f"Error: {e}")
            return

        # Print with ptouch-print
        print("- Printing with ptouch-print...", end="")
        try:
            print_image(self.cable, self.cut, target_path)
            print("done")
        except Exception as e:
            print("failed")
            print(f"Error: {e}")
            return

        # Remove processed image
        os.remove(target_path)
        if self.remove:
            os.remove(src_path)


def setup_parser():
    parser = argparse.ArgumentParser(description="Watch a directory for changes")
    parser.add_argument("directory", help="Directory to watch")
    parser.add_argument(
        "--recursive", action="store_true", help="Watch subdirectories recursively"
    )
    parser.add_argument(
        "--font", default="Noto-Sans-Bold", help="Font to use for asset ID"
    )
    parser.add_argument(
        "--remove", action="store_true", help="Remove original image after printing"
    )
    parser.add_argument(
        "--cable",
        action="store_true",
        help="Enable cable mode. Label will be printed twice to wrap around cable",
    )
    parser.add_argument(
        "--cut",
        action="store_true",
        help="Cuts immediately after printing. Will waste a bit of label tape",
    )
    return parser


def main():
    parser = setup_parser()
    args = parser.parse_args()

    event_handler = EventHandler(args.font, args.remove, args.cable, args.cut)
    observer = Observer()
    observer.schedule(event_handler, args.directory, recursive=args.recursive)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\rExiting")
    finally:
        observer.stop()
        observer.join()


if __name__ == "__main__":
    main()
