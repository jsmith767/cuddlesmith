#!/usr/bin/env python3
"""
Extract and download images from mirrored HTML files
"""
import os
import re
import sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

def extract_image_urls(html_file):
    """Extract all image URLs from an HTML file"""
    with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    image_urls = set()
    
    # Find all img tags
    for img in soup.find_all('img'):
        for attr in ['src', 'data-src', 'data-image']:
            url = img.get(attr)
            if url and url.startswith('http'):
                # Remove query parameters for cleaner filenames
                clean_url = url.split('?')[0]
                image_urls.add(clean_url)
    
    # Also check for background images in style attributes
    for tag in soup.find_all(style=True):
        style = tag.get('style', '')
        bg_matches = re.findall(r'url\(["\']?([^"\']+)["\']?\)', style)
        for match in bg_matches:
            if match.startswith('http'):
                clean_url = match.split('?')[0]
                image_urls.add(clean_url)
    
    return image_urls

def download_image(url, output_path):
    """Download an image from URL to local path"""
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def get_filename_from_url(url):
    """Extract a reasonable filename from URL"""
    parsed = urlparse(url)
    path = parsed.path
    
    # Get the last part of the path
    filename = os.path.basename(path)
    
    # If no extension, try to infer from URL or use .jpg
    if not os.path.splitext(filename)[1]:
        filename += '.jpg'
    
    # Clean up the filename
    filename = filename.replace('%20', '_').replace('+', '_')
    
    return filename

def main():
    snapshot_dir = Path(os.path.expanduser('~/cuddlesmith-snapshot'))
    output_dir = Path('images')
    
    if not snapshot_dir.exists():
        print(f"Snapshot directory not found: {snapshot_dir}")
        sys.exit(1)
    
    output_dir.mkdir(exist_ok=True)
    
    # Find all HTML files in snapshot
    html_files = list(snapshot_dir.glob('*.html')) + list(snapshot_dir.glob('*'))
    html_files = [f for f in html_files if f.is_file() and f.suffix == '.html']
    
    if not html_files:
        html_files = [f for f in snapshot_dir.iterdir() if f.is_file()]
    
    all_image_urls = set()
    
    print("Extracting image URLs from HTML files...")
    for html_file in html_files:
        print(f"Processing {html_file.name}...")
        urls = extract_image_urls(html_file)
        all_image_urls.update(urls)
        print(f"  Found {len(urls)} unique images")
    
    print(f"\nTotal unique images found: {len(all_image_urls)}")
    print("\nDownloading images...")
    
    downloaded = 0
    for i, url in enumerate(sorted(all_image_urls), 1):
        filename = get_filename_from_url(url)
        output_path = output_dir / filename
        
        # Skip if already exists
        if output_path.exists():
            print(f"[{i}/{len(all_image_urls)}] Skipping {filename} (already exists)")
            continue
        
        print(f"[{i}/{len(all_image_urls)}] Downloading {filename}...")
        if download_image(url, output_path):
            downloaded += 1
    
    print(f"\nDownloaded {downloaded} new images to {output_dir}/")

if __name__ == '__main__':
    main()

