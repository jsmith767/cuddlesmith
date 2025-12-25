#!/bin/bash
# Extract and download images from mirrored HTML files

SNAPSHOT_DIR="$HOME/cuddlesmith-snapshot"
OUTPUT_DIR="images"

mkdir -p "$OUTPUT_DIR"

echo "Extracting image URLs from HTML files..."

# Extract all unique image URLs from all HTML files
# First extract with query params, then create clean versions
grep -rh -oE 'https://images\.squarespace-cdn\.com[^"'\'' ]+\.(jpg|jpeg|png|gif|webp)(\?[^"'\'' ]+)?' "$SNAPSHOT_DIR"/*.html "$SNAPSHOT_DIR"/* 2>/dev/null | \
    sort -u > /tmp/image_urls_full.txt

# Create clean URLs (without query params) for filenames, but keep originals for download
cat /tmp/image_urls_full.txt | sed 's/?.*$//' | sort -u > /tmp/image_urls.txt

TOTAL=$(wc -l < /tmp/image_urls.txt | tr -d ' ')
echo "Found $TOTAL unique images"

echo "Downloading images..."
COUNT=0

# Use the full URLs for downloading
while IFS= read -r url_full; do
    COUNT=$((COUNT + 1))
    
    # Get clean URL for filename
    url_clean=$(echo "$url_full" | sed 's/?.*$//')
    
    # Extract filename from clean URL
    filename=$(basename "$url_clean")
    # Clean up filename
    filename=$(echo "$filename" | sed 's/%20/_/g' | sed 's/+/_/g')
    
    # If no extension, add .jpg
    if [[ ! "$filename" =~ \.(jpg|jpeg|png|gif|webp)$ ]]; then
        filename="${filename}.jpg"
    fi
    
    output_path="$OUTPUT_DIR/$filename"
    
    # Skip if already exists
    if [ -f "$output_path" ]; then
        echo "[$COUNT/$TOTAL] Skipping $filename (already exists)"
        continue
    fi
    
    echo "[$COUNT/$TOTAL] Downloading $filename..."
    # Try with full URL first, then clean URL
    if curl -f -s -L -o "$output_path" "$url_full" 2>/dev/null; then
        echo "  ✓ Downloaded ($(du -h "$output_path" | cut -f1))"
    elif [ "$url_full" != "$url_clean" ] && curl -f -s -L -o "$output_path" "$url_clean" 2>/dev/null; then
        echo "  ✓ Downloaded (clean URL) ($(du -h "$output_path" | cut -f1))"
    else
        echo "  ✗ Failed to download"
        rm -f "$output_path"
    fi
done < /tmp/image_urls_full.txt

echo "Done! Images saved to $OUTPUT_DIR/"

