import sys

chunk_size=1024*1024
with open(sys.argv[1], "rb") as kfile, open(sys.argv[2], "rb") as vfile, open(sys.argv[3], "wb") as out_file:
   while True:
        kchunk = kfile.read(chunk_size)
        vchunk = vfile.read(chunk_size)


        if len(vchunk) != len(kchunk) or len(vchunk) % 4 != 0:
            print("Filesize error.")
            sys.exit(1)

        if kchunk == b'':
            sys.exit(0)

        for i in range(len(vchunk)//4):
            out_file.write(kchunk[i*4:(i+1)*4])
            out_file.write(vchunk[i*4:(i+1)*4])
