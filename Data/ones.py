import sys
one = 1
onea = one.to_bytes(4, 'little')
onea *= 1024*1024*512

with open(sys.argv[1], "wb") as binary_file:
    binary_file.write(onea)
