rm -rf nyt_keys.* nyt_values.*
wget https://blog.boxm.de/nyt_keys.bin.gz  -O ./nyt_keys.bin.gz
gunzip nyt_keys.bin.gz

wget https://blog.boxm.de/nyt_values.bin.gz  -O ./nyt_values.bin.gz
gunzip nyt_values.bin.gz

python rowify.py nyt_keys.bin nyt_values.bin nyt.bin
