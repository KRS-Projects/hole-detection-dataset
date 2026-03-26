import csv
import os
import argparse
import logging
from pathlib import Path
import cadquery as cq
from step_importer import load_step

logger = logging.getLogger(__name__)

ACCENT_MAP = {
    "é": "e",
    "è": "e",
    "ê": "e",
    "à": "a",
    "á": "a",
    "î": "i",
    "ï": "i",
    "ô": "o",
    "ö": "o",
    "û": "u",
    "ü": "u",
    "ç": "c",
    "/": "____",
    "*": "___",
    "->": "_____",
}


def sanitise_name(the_str: str) -> str:
    """Remove accents and special characters for less processing issues.

    :param the_str: String to remove accents from.
    ...
    :returns: The string without accents.
    """
    for key, value in ACCENT_MAP.items():
        the_str = the_str.replace(key, value)
    return the_str


def extract_single_parts(input_folder: str, out_folder: str) -> None:
    """Extracts single CAD-parts from the assembly-files, based on the part_list.csv-file found in the repository.

    :param input_folder: The folder, where the assembly files are located.
    :param out_folder: The folder to save the Step-files of the extracted parts to.
    """
    input_folder = Path(input_folder)
    out_folder = Path(out_folder)
    out_folder.mkdir(parents=True, exist_ok=True)

    # load CSV into memory
    with open("part_list.csv", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

    # create starting variable, used to not reload if no necessary
    last_step_path = None

    # Iterate csv rows
    for n_file, row in enumerate(rows):
        logger.info(f"{n_file + 1} of {len(rows)}")

        file = row["assembly"]
        loc = row["Tree"]
        folder = row["assembly_folder"]

        # Due to the way it is unzipped, we have one subfolder, that we account for
        step_path = input_folder.joinpath(folder)
        step_path = step_path.joinpath(list(step_path.glob("*"))[0]).joinpath(file)

        # Load STEP file only if folder/file changed
        if step_path != last_step_path:
            if not step_path.exists():
                raise ValueError("Missing File")
            step_data = load_step(str(step_path))

            # update last step path
            last_step_path = step_path

        # iterate through parts to find the required.
        # This logic could be improved, but it seems fast enough.
        for item in step_data:
            # skip if location not the same as tree.
            if item.get("Tree") != loc:
                continue
            # skip parts with no name
            if not item.get("Name"):
                continue

            # replace special characters
            item_name = sanitise_name(item["Name"])

            # Create output path
            step_out_path = os.path.join(out_folder, f"{n_file}_{item_name}.step")

            # Add idx for file name and export part
            cq.exporters.export(cq.Shape.cast(item["Shape"]), step_out_path)
            break

        else:
            # raise an error, if no part was found
            raise ValueError(f"Part could not be found. File {file}, folder {folder}, Tree {loc}")


if __name__ == "__main__":
    # Create parser
    parser = argparse.ArgumentParser(description="Process STEP assembly folders")

    # Add arguments
    parser.add_argument("--folder", "-f", type=str, help="Path to the input folder containing STEP assemblies.")
    parser.add_argument(
        "--output_folder", "-o", type=str, help="Path to the folder where extracted files will be stored."
    )

    args = parser.parse_args()

    assembly_folder = args.folder
    output_folder = args.output_folder

    if not os.path.exists(assembly_folder):
        raise FileNotFoundError(f"Input folder '{assembly_folder}' does not exist.")

    extract_single_parts(assembly_folder, output_folder)
