#!/bin/bash

# Check if a TIFF file is provided as an argument
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <tiff_file>"
    exit 1
fi

tiff_file=$1

# Check if the file exists
if [ ! -f "$tiff_file" ]; then
    echo "Error: File '$tiff_file' not found!"
    exit 1
fi

# Convert GeoTIFF to ERS Float32 format
output_file="${tiff_file%.tif}.dem"
gdal_translate -ot Float32 -of ERS "$tiff_file" "$output_file"

if [ $? -eq 0 ]; then
    echo "Conversion successful: $output_file"
else
    echo "Error during conversion."
    exit 1
fi
