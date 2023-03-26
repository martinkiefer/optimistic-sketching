rm -rf wc98_keys.* wc98_values.*
wget https://blog.boxm.de/wc98_keys.bin.gz  -O ./wc98_keys.bin.gz
gunzip wc98_keys.bin.gz

wget https://blog.boxm.de/wc98_values.bin.gz  -O ./wc98_values.bin.gz
gunzip wc98_values.bin.gz

python rowify.py wc98_keys.bin wc98_values.bin wc98.bin
