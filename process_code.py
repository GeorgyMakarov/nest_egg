def convert_indentation(input_file, output_file):
  """
  Reads a python file with 4-space indentation and writes a new file
  with 2-space indentation.
  """
  with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
    for line in infile:
      stripped_line = line.lstrip()
      line_len  = len(line)
      strip_len = len(stripped_line)
      diff_len  = line_len - strip_len
      if diff_len > 0:
        n_delete = int(diff_len / 2)
        new_line = line[n_delete:]
      else:
        new_line = line
      outfile.write(new_line)

input_file  = 'mac.txt'
output_file = 'mac.py'
convert_indentation(input_file, output_file)
print(f"Converted from {input_file} to {output_file}")