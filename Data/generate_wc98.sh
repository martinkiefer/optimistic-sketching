rm -rf wc98_keys.* wc98_values.*
wget https://tubcloud.tu-berlin.de/s/gP7YWtM4ZS8w4RB/download/wc98_keys.bin.gz  -O ./wc98_keys.bin.gz
gunzip wc98_keys.bin.gz

wget https://tubcloud.tu-berlin.de/s/YBoaRdHDnrMZ645/download/wc98_values.bin.gz  -O ./wc98_values.bin.gz
gunzip wc98_values.bin.gz

python rowify.py wc98_keys.bin wc98_values.bin wc98.bin
