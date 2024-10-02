import os
import logging
import json
from dotenv import load_dotenv
from scrapegraphai.graphs import SmartScraperGraph
from unidecode import unidecode

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv("SCRAPEGRAPH_API_KEY")  # Ensure this variable is set in your .env file

# Configure logging
logging.basicConfig(
    filename='scraping.log',  # Log file
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Configuration for ScrapeGraphAI
graph_config = {
    "llm": {
        "api_key": API_KEY,
        "model": "openai/gpt-4o-mini",
        "temperature": 0,
    },
    "verbose": True,
    "headless": True,
}

# Clean the text using unidecode to remove accents
def clean_text(text):
    """Clean the input text by removing accents and non-text markings."""
    if text is None:
        return None
    return unidecode(text)

def scrape_artist_links(url):
    logging.info(f"Starting scraping for {url}")

    # Create the SmartScraperGraph instance
    smart_scraper_graph = SmartScraperGraph(
        prompt=(
            "We have a list for a given artist Each on 1 link, the goal is to get"
            "an inventory of all the links from the links and what grouping they are in."
            "for Example, the https://www.todotango.com/english/artists/info/104/Rodolfo-Biagi"
            "link has links for Article, Boiography, Las entraevistas, Discography, Obras"
            "scores, Los Historria, Ltics and more."
            "your goal is to parese each site find links and group them according this"
            "list below (and add more if you see them.)"
            "Artist : some facts name, DOB,Nicknames, Place of birth, Date of death"
            "Article: Biographies,"
            "Article: Las entrevistas,"
            "Article: La Historia,"
            "Article: Los tangos,"
            "Article: El baile,"
            "Article: Las orquestas,"
            "Article: Tango en el mundo,"
            "Article: Buenos Aires,"
            "Scores: score links name (with the Title of the soong, type and year)"
            "Scores: Link to the song"
            "Obras : list of songs titles, tpye (tango, vals, milonga, etc) and year recorded"
            "Obras : Link to the song"
            "Music : List of songs titles (that have a recording on the site)"
            "Music : the link to the recording on the site"
            "Music : Possible the Type, year, and duration - E.G. (Tango (1941) 02'30) "
            "Music : Lyrics in spanish or engish"
            "Other : any other links that do not fit into the above categories"
            "--"
            "This next point is important ...  the capturing of the all the availbile presetned links is"
            " more important that the groupng and categorization. Use the other category when you are not sure"
        ),
        source=url,
        config=graph_config
    )

    # Run the scraper and capture the result
    result = smart_scraper_graph.run()

    # Clean and organize the data
    cleaned_data = {
        "Artist": {},
        "Article": {},
        "Music": [],
        "Scores": [],
        "Obras": [],
        "Discography": [],
        "Other": []
    }

    errors = []

    try:
        if 'Artist' in result and isinstance(result['Artist'], dict):
            cleaned_data["Artist"] = {k: clean_text(v) for k, v in result['Artist'].items()}

        if 'Article' in result and isinstance(result['Article'], dict):
            for category, articles in result['Article'].items():
                if isinstance(articles, list):
                    cleaned_data["Article"][category] = [
                        {"title": clean_text(article["title"]), "link": clean_text(article["link"])}
                        for article in articles if isinstance(article, dict) and "title" in article and "link" in article
                    ]

        if 'Music' in result and isinstance(result['Music'], dict):
            if 'list of songs' in result['Music'] and isinstance(result['Music']['list of songs'], list):
                cleaned_data["Music"] = [
                    {"title": clean_text(song["title"]), "link": clean_text(song["link"])}
                    for song in result['Music']['list of songs'] if isinstance(song, dict) and "title" in song and "link" in song
                ]

        if 'Scores' in result and isinstance(result['Scores'], dict):
            if 'score links' in result['Scores'] and isinstance(result['Scores']['score links'], list):
                cleaned_data["Scores"] = [
                    {
                        "title": clean_text(score["title"]),
                        "type": clean_text(score["type"]),
                        "year": score.get("year"),
                        "link": clean_text(score["link"])
                    }
                    for score in result['Scores']['score links'] if isinstance(score, dict) and "title" in score and "link" in score
                ]

        if 'Obras' in result and isinstance(result['Obras'], dict):
            if 'list of songs' in result['Obras'] and isinstance(result['Obras']['list of songs'], list):
                cleaned_data["Obras"] = [
                    {
                        "title": clean_text(obras["title"]),
                        "type": clean_text(obras["type"]),
                        "year": obras.get("year"),
                        "link": clean_text(obras["link"])
                    }
                    for obras in result['Obras']['list of songs'] if isinstance(obras, dict) and "title" in obras and "link" in obras
                ]

        if 'Discography' in result and isinstance(result['Discography'], list):
            cleaned_data["Discography"] = [
                {"title": clean_text(disc["title"]), "link": clean_text(disc["link"])}
                for disc in result['Discography'] if isinstance(disc, dict) and "title" in disc and "link" in disc
            ]

        if 'Other' in result and isinstance(result['Other'], list):
            cleaned_data["Other"] = [
                {"title": clean_text(other["title"]), "link": clean_text(other["link"])}
                for other in result['Other'] if isinstance(other, dict) and "title" in other and "link" in other
            ]

    except Exception as e:
        error_message = f"Error cleaning data for {url}: {e}"
        logging.error(error_message)
        errors.append(error_message)
        with open("failedURL.txt", "a") as f:
            f.write(f"{url}\n")
        return None

    if errors:
        for error in errors:
            print(error)

    return cleaned_data


def main():
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

    # Load existing discographies from JSON file, if it exists
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
                logging.error(f"Skipping URL due to data cleaning error: {url}")
                print(f"Skipping URL due to data cleaning error: {url}")
                with open("failedURL.txt", "a") as f:
                    f.write(f"{url}\n")
                continue

            artist_name = clean_text(url.split("/")[-1].replace("-", " ").title())
            logging.info(f"Processing artist: {artist_name}")
            print(f"Processing artist: {artist_name}")

            if artist_name not in all_artists:
                all_artists[artist_name] = {"name": artist_name, "discography": {"Article": {}, "Scores": [], "Music": [], "Obras": []}}

            all_artists[artist_name]["discography"]["Article"].update(foundLinks["Article"])
            all_artists[artist_name]["discography"]["Scores"].extend(foundLinks["Scores"])
            all_artists[artist_name]["discography"]["Music"].extend(foundLinks["Music"])
            all_artists[artist_name]["discography"]["Obras"].extend(foundLinks["Obras"])

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

    logging.info("All foundLinks entries have been written to discoveredLinks.json.")
    print("All foundLinks entries have been written to discoveredLinks.json.")

    if len(completed_urls) == len(urls):
        logging.info("Program completed successfully without errors.")
        print("Program completed successfully without errors.")
    else:
        logging.info("Program completed with some errors.")
        print("Program completed with some errors.")

if __name__ == "__main__":
    main()