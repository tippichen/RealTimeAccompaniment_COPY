import csv
import sys
import os

def process_file(input_file, output_file):
    try:
        with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
            reader = csv.reader(infile)

            results = []
            index = 0
            for row in reader:
                if len(row) < 4:
                    continue  # Skip rows with insufficient data

                note = int(row[0])
                time = float(row[1])
                duration = float(row[2])
                velocity = int(row[3])

                # Append note on
                results.append([index, 144, note, '', time, velocity])
                index += 1

                # Append note off
                results.append([index, 128, note, '', time + duration, velocity])
                index += 1

            # Write the results as a single-line Python list
            outfile.write(str(results))

        print(f"Processing complete. Output written to {output_file}")

    except Exception as e:
        print(f"An error occurred while processing {input_file}: {e}")

def process_multiple_files(input_files):
    for input_file in input_files:
        if not os.path.isfile(input_file):
            print(f"File not found: {input_file}")
            continue

        # Generate output filename
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}_new.txt"

        process_file(input_file, output_file)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python process_notes.py <input_file1> <input_file2> ...")
    else:
        input_files = sys.argv[1:]
        process_multiple_files(input_files)