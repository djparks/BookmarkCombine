"""
Bookmark Combiner for macOS
This script extracts bookmarks from an exported Safari HTML file and Chrome, 
merges them, deduplicates by URL, sorts them by title, and saves the result 
to 'combined_bookmarks.csv' and 'combined_bookmarks.html'.

How to execute:
1. Export your Safari bookmarks:
   - Open Safari.
   - Go to File > Export Bookmarks...
   - Save the file as 'safari_bookmarks.html' in the same folder as this script.
2. Open Terminal.
3. Navigate to the directory containing this script.
4. Run the script using Python 3:
   python3 combine_bookmarks.py
"""

import os
import re
import json
import csv

def get_bookmarks_from_html(path, source_name):
    bookmarks = []
    if not os.path.exists(path):
        print(f"HTML bookmarks file not found: {path}")
        print(f"Please export your Safari bookmarks to '{path}' and place it in this directory.")
        return bookmarks

    print(f"Extracting bookmarks from HTML file: {path}")
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Regex to find <A ... HREF="url" ...>Title</A>
        # Netscape Bookmark format used by most browsers for exports
        pattern = re.compile(r'<A\s+[^>]*HREF="([^"]*)"[^>]*>(.*?)</A>', re.IGNORECASE | re.DOTALL)
        
        for match in pattern.finditer(content):
            url = match.group(1)
            title = match.group(2)
            # Clean up title: remove HTML tags and extra whitespace
            title = re.sub(r'<[^>]+>', '', title).strip()
            if not title:
                title = url
            bookmarks.append({'Title': title, 'URL': url, 'Source': source_name})
    except Exception as e:
        print(f"Error parsing HTML bookmarks: {e}")
        
    return bookmarks

def get_chrome_bookmarks(chrome_base_path):
    all_chrome_bookmarks = []
    
    if not os.path.exists(chrome_base_path):
        print(f"Chrome directory not found: {chrome_base_path}")
        return all_chrome_bookmarks

    # List all directories that might be profiles
    profiles = [d for d in os.listdir(chrome_base_path) if d == 'Default' or d.startswith('Profile ')]
    
    for profile in profiles:
        path = os.path.join(chrome_base_path, profile, 'Bookmarks')
        if not os.path.exists(path):
            continue
            
        print(f"Extracting bookmarks from Chrome profile: {profile}")
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            def parse_children(children):
                for child in children:
                    if child.get('type') == 'url':
                        title = child.get('name')
                        url = child.get('url')
                        if title and url:
                            all_chrome_bookmarks.append({'Title': title, 'URL': url, 'Source': f'Chrome ({profile})'})
                    elif child.get('type') == 'folder':
                        if 'children' in child:
                            parse_children(child['children'])

            roots = data.get('roots', {})
            for root_key in roots:
                root = roots[root_key]
                if 'children' in root:
                    parse_children(root['children'])

        except Exception as e:
            print(f"Error parsing Chrome bookmarks for {profile}: {e}")

    return all_chrome_bookmarks

def main():
    home = os.path.expanduser('~')
    safari_html_path = 'safari_bookmarks.html'
    chrome_base_path = os.path.join(home, 'Library/Application Support/Google/Chrome')
    
    print("Extracting Safari bookmarks from HTML...")
    safari_bookmarks = get_bookmarks_from_html(safari_html_path, 'Safari (HTML)')
    print(f"Found {len(safari_bookmarks)} Safari bookmarks.")
    
    print("Extracting Chrome bookmarks...")
    chrome_bookmarks = get_chrome_bookmarks(chrome_base_path)
    print(f"Found {len(chrome_bookmarks)} Chrome bookmarks total across all profiles.")
    
    all_bookmarks = safari_bookmarks + chrome_bookmarks
    
    # Deduplicate by URL
    unique_bookmarks = {}
    for b in all_bookmarks:
        url = b['URL']
        if url not in unique_bookmarks:
            unique_bookmarks[url] = b
        else:
            # If it already exists, maybe append sources? 
            # The prompt says "make values unique", which usually means deduplicate.
            # We'll keep the first one found.
            pass
            
    final_list = list(unique_bookmarks.values())
    
    # Sort by Title (case-insensitive)
    final_list.sort(key=lambda x: x['Title'].lower())
    
    output_file = 'combined_bookmarks.csv'
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Title', 'URL', 'Source']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for b in final_list:
                writer.writerow(b)
        print(f"Successfully saved {len(final_list)} unique bookmarks to {output_file}")
    except Exception as e:
        print(f"Error writing CSV: {e}")

    # Save to HTML
    html_output = 'combined_bookmarks.html'
    save_to_html(final_list, html_output)

def save_to_html(bookmarks, output_file):
    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Combined Bookmarks</title>
    <style>
        :root {{
            --primary-color: #007aff;
            --bg-color: #f5f5f7;
            --card-bg: #ffffff;
            --text-main: #1d1d1f;
            --text-muted: #86868b;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            margin: 0;
            padding: 40px 20px;
            line-height: 1.5;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}
        header {{
            margin-bottom: 40px;
            text-align: center;
        }}
        h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 10px;
            letter-spacing: -0.015em;
        }}
        .stats {{
            color: var(--text-muted);
            font-size: 1.1rem;
        }}
        .bookmark-list {{
            list-style: none;
            padding: 0;
        }}
        .bookmark-item {{
            background: var(--card-bg);
            margin-bottom: 12px;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.02);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .bookmark-item:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 12px rgba(0,0,0,0.05);
        }}
        .bookmark-info {{
            flex: 1;
            min-width: 0;
            margin-right: 20px;
        }}
        .bookmark-title {{
            display: block;
            font-size: 1.2rem;
            font-weight: 600;
            color: var(--primary-color);
            text-decoration: none;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            margin-bottom: 4px;
        }}
        .bookmark-title:hover {{
            text-decoration: underline;
        }}
        .bookmark-url {{
            display: block;
            font-size: 0.9rem;
            color: var(--text-muted);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .source-badge {{
            font-size: 0.75rem;
            font-weight: 500;
            padding: 4px 10px;
            border-radius: 20px;
            background: #f0f0f2;
            color: #515154;
            white-space: nowrap;
        }}
        @media (max-width: 600px) {{
            .bookmark-item {{
                flex-direction: column;
                align-items: flex-start;
            }}
            .source-badge {{
                margin-top: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>My Bookmarks</h1>
            <p class="stats">{count} unique bookmarks combined from Safari and Chrome</p>
        </header>
        <ul class="bookmark-list">
            {items}
        </ul>
    </div>
</body>
</html>"""

    item_template = """
            <li class="bookmark-item">
                <div class="bookmark-info">
                    <a href="{url}" class="bookmark-title" target="_blank">{title}</a>
                    <span class="bookmark-url">{url}</span>
                </div>
                <span class="source-badge">{source}</span>
            </li>"""

    items_html = ""
    for b in bookmarks:
        items_html += item_template.format(
            title=b['Title'],
            url=b['URL'],
            source=b['Source']
        )

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_template.format(count=len(bookmarks), items=items_html))
        print(f"Successfully saved {len(bookmarks)} unique bookmarks to {output_file}")
    except Exception as e:
        print(f"Error writing HTML: {e}")

if __name__ == "__main__":
    main()
