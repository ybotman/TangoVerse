import requests
from bs4 import BeautifulSoup
import json
import logging
import os
from unidecode import unidecode

def clean_text(text):
    """Clean the input text by removing accents and stripping whitespace."""
    if text is None:
        return None
    return unidecode(text.strip())

def scrape_artist_links(url):
    logging.info(f"Starting scraping for {url}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        html_content = response.content
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract artist name
        artist_name_tag = soup.find('h3')
        artist_name = artist_name_tag.get_text(strip=True) if artist_name_tag else None
        if not artist_name:
            # Extract from URL if not found in page
            artist_name = url.split("/")[-1].replace("-", " ").title()
        artist_name = clean_text(artist_name)
        
        cleaned_data = {
            "Artist": {
                "name": artist_name
            },
            "Article": {},
            "Music": [],
            "Scores": [],
            "Obras": [],
            "Discography": [],
            "Other": []
        }
        
        # Find the tab-content
        tab_content = soup.find('div', {'class': 'tab-content'})
        if not tab_content:
            logging.warning("No tab content found.")
            return cleaned_data
        
        # Process each tab-pane
        tab_panes = tab_content.find_all('div', {'class': 'tab-pane'})
        for pane in tab_panes:
            pane_id = pane.get('id')
            if pane_id == 'articulos':
                # Process Articles
                articles = {}
                h3_tags = pane.find_all('h3')
                current_category = ''
                for h3 in h3_tags:
                    category = clean_text(h3.get_text(strip=True))
                    if category:
                        current_category = category
                        articles[current_category] = []
                    next_sibling = h3.find_next_sibling()
                    while next_sibling and next_sibling.name != 'h3':
                        if next_sibling.name == 'div' and 'itemlista' in next_sibling.get('class', []):
                            a_tag = next_sibling.find('a')
                            if a_tag:
                                title = clean_text(a_tag.get_text(strip=True))
                                link = a_tag['href']
                                articles[current_category].append({
                                    'title': title,
                                    'link': link
                                })
                        next_sibling = next_sibling.find_next_sibling()
                cleaned_data['Article'] = articles
            elif pane_id == 'musica':
                # Process Music
                playlist_div = pane.find('div', {'id': 'jp_playlist_2'})
                if playlist_div:
                    ul = playlist_div.find('ul')
                    if ul:
                        li_tags = ul.find_all('li')
                        for li in li_tags:
                            a_tag = li.find('a')
                            if a_tag:
                                title = clean_text(a_tag.get_text(strip=True))
                                link = a_tag.get('href', '#')
                                cleaned_data['Music'].append({
                                    'title': title,
                                    'link': link
                                })
            elif pane_id == 'partituras':
                # Process Scores
                table = pane.find('table', {'id': 'main_fichacreador1_DL_Partituras'})
                if table:
                    rows = table.find_all('tr')
                    for row in rows:
                        tds = row.find_all('td')
                        for td in tds:
                            a_tag = td.find('a', id=lambda x: x and 'hl_Partitura' in x)
                            if a_tag:
                                title = clean_text(a_tag.get_text(strip=True))
                                link = a_tag['href']
                                span_rhythm = td.find('span', id=lambda x: x and 'lbl_Ritmo' in x)
                                type = clean_text(span_rhythm.get_text(strip=True)) if span_rhythm else ''
                                span_year = td.find('span', id=lambda x: x and 'lbl_Fecha' in x)
                                year = clean_text(span_year.get_text(strip=True)) if span_year else ''
                                cleaned_data['Scores'].append({
                                    'title': title,
                                    'type': type,
                                    'year': year,
                                    'link': link
                                })
            elif pane_id == 'obras':
                # Process Obras
                table = pane.find('table', {'id': 'main_fichacreador1_DL_Temas'})
                if table:
                    rows = table.find_all('tr')
                    for row in rows:
                        tds = row.find_all('td')
                        for td in tds:
                            a_tag = td.find('a', id=lambda x: x and 'hl_Letra' in x)
                            if a_tag:
                                title = clean_text(a_tag.get_text(strip=True))
                                link = a_tag['href']
                                span_rhythm = td.find('span', {'class': 'text-muted'})
                                type_year_text = clean_text(span_rhythm.get_text(strip=True)) if span_rhythm else ''
                                type_year = type_year_text.split('(')
                                type = clean_text(type_year[0]) if type_year else ''
                                year = type_year[1][:-1] if len(type_year) > 1 else ''
                                cleaned_data['Obras'].append({
                                    'title': title,
                                    'type': type,
                                    'year': year,
                                    'link': link
                                })
            elif pane_id == 'discografia':
                # Process Discography
                table = pane.find('table', {'id': 'main_fichacreador1_RP_Discografia'})
                if table:
                    a_tags = table.find_all('a', id=lambda x: x and 'hl_Tema_' in x)
                    for a_tag in a_tags:
                        title = clean_text(a_tag.get_text(strip=True))
                        link = a_tag['href']
                        cleaned_data['Music'].append({
                            'title': title,
                            'link': link
                        })
            elif pane_id == 'video':
                # Process Videos
                table = pane.find('table', {'id': 'main_fichacreador1_DL_Videos'})
                if table:
                    iframe_tags = table.find_all('iframe')
                    for iframe in iframe_tags:
                        src = iframe.get('src')
                        cleaned_data['Other'].append({
                            'title': 'Video',
                            'link': src
                        })
            else:
                # Other sections
                pass
            
            # Apply clean_text to all extracted text
            for key in ['Article', 'Music', 'Scores', 'Obras', 'Discography', 'Other']:
                if isinstance(cleaned_data[key], dict):
                    for subkey in cleaned_data[key]:
                        for item in cleaned_data[key][subkey]:
                            item['title'] = clean_text(item['title'])
                            item['link'] = clean_text(item['link'])
                elif isinstance(cleaned_data[key], list):
                    for item in cleaned_data[key]:
                        item['title'] = clean_text(item['title'])
                        item['link'] = clean_text(item['link'])
        
        return cleaned_data
            
    except Exception as e:
        logging.error(f"Error scraping {url}: {e}")
        return None

def main():
    logging.basicConfig(
        filename='scraping.log',  # Log file
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logging.info("Program started.")
    print("Program started.")

    links_file = 'urls.txt'  # Input file with artist links
    processed_file = 'processedUrls.txt'  # File to keep track of processed links
    output_file = 'discoveredLinks.json'  # Output JSON file

    # Read URLs from the links file
    try:
        with open(links_file, 'r') as f:
            urls = [line.strip() for line in f.readlines() if line.strip()]
    except Exception as e:
        logging.error(f"Error reading {links_file}: {e}")
        print(f"Error reading {links_file}: {e}")
        return

    completed_urls = set()

    # Load processed URLs from the processed file
    if os.path.exists(processed_file):
        with open(processed_file, 'r') as f:
            completed_urls = set(line.strip() for line in f.readlines())

    # Initialize all_artists dictionary
    all_artists = {}

    # Load existing data from JSON file, if it exists
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r') as f:
                all_artists = json.load(f)
        except Exception as e:
            logging.error(f"Error reading {output_file}: {e}")
            print(f"Error reading {output_file}: {e}")
            backup_file = f"{output_file}.bak"
            os.rename(output_file, backup_file)
            logging.warning(f"Backing up malformed JSON to {backup_file}")
            print(f"Backing up malformed JSON to {backup_file}")
            all_artists = {}

    for url in urls:
        if url in completed_urls:
            logging.info(f"Skipping already processed URL: {url}")
            print(f"Skipping already processed URL: {url}")
            continue

        if not url:
            logging.warning("Empty URL found, skipping.")
            print("Empty URL found, skipping.")
            continue

        try:
            logging.info(f"Processing link: {url}")
            print(f"Processing link: {url}")
            foundLinks = scrape_artist_links(url)

            if foundLinks is None:
                logging.error(f"Skipping URL due to data scraping error: {url}")
                print(f"Skipping URL due to data scraping error: {url}")
                with open("failedURL.txt", "a") as f:
                    f.write(f"{url}\n")
                continue

            artist_name = foundLinks["Artist"].get("name") or clean_text(url.split("/")[-1].replace("-", " ").title())
            logging.info(f"Processing artist: {artist_name}")
            print(f"Processing artist: {artist_name}")

            # Ensure we don't overwrite existing data
            if artist_name in all_artists:
                # Merge the new data with existing data
                existing_data = all_artists[artist_name]
                for key in ['Article', 'Music', 'Scores', 'Obras', 'Discography', 'Other']:
                    if isinstance(existing_data[key], dict):
                        for subkey in foundLinks[key]:
                            if subkey in existing_data[key]:
                                existing_data[key][subkey].extend(foundLinks[key][subkey])
                            else:
                                existing_data[key][subkey] = foundLinks[key][subkey]
                    elif isinstance(existing_data[key], list):
                        existing_data[key].extend(foundLinks[key])
            else:
                all_artists[artist_name] = foundLinks

            with open(processed_file, 'a') as f:
                f.write(url + '\n')
            logging.info(f"Successfully processed and recorded URL: {url}")
            print(f"Successfully processed and recorded URL: {url}")

            with open(output_file, 'w') as f:
                json.dump(all_artists, f, indent=4)

        except Exception as e:
            logging.error(f"Error processing {url}: {e}")
            print(f"Error processing {url}: {e}")
            with open("failedURL.txt", "a") as f:
                f.write(f"{url}\n")

    logging.info("All entries have been written to discoveredLinks.json.")
    print("All entries have been written to discoveredLinks.json.")

    if len(completed_urls) == len(urls):
        logging.info("Program completed successfully without errors.")
        print("Program completed successfully without errors.")
    else:
        logging.info("Program completed with some errors.")
        print("Program completed with some errors.")

if __name__ == "__main__":
    main()