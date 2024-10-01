import os
import logging
import json
from dotenv import load_dotenv
from scrapegraphai.graphs import SmartScraperGraph
from unidecode import unidecode  # Importing unidecode

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

def scrape_artist_discography(url):
    logging.info(f"Starting scraping for {url}")  # Combine scraping start and URL log

    # Create the SmartScraperGraph instance
    smart_scraper_graph = SmartScraperGraph(
        prompt= "We are gathering for a given artist, the invoentory of all his Songs/Music/Obras found within the links provided. "
                "please find all songs you see. The only manditory field is song title, but the year and style are also important. "
                "Parse all songs from the page. For each song, provide the following: "
                "1) Song title, 2) Song style (most will be tango, vals, milonga), "
                "1a) but some might be Corrido, pReioconm Ranchera, Vidalita, shimmy or more)"
                "3) The canta as (singer or instrumental), 4) The orchestra, "
                "5) The singer (null if none, and name if canta is not instrumental), "
                "6) The year recorded, 7) The recording studio (RCA, TC, etc), "
                "8) Location recorded (Buenos Aires, New York, etc), "
                "9) The recording number code for the song."
                "These might be found in sections labeled Discography, Obras, Music, Lyrics, or scores."
                "Find as much as you can about the songs (and they might be spanish) as possible",
        source=url,
        config=graph_config
    )

    # Run the scraper and capture the result
    result = smart_scraper_graph.run()

    # Log the raw output for inspection
    # logging.info(f"Raw output from GenerateAnswer node: {result}")


    # Assume result is always a list of songs
    if isinstance(result, dict) and 'songs' in result:
        discography_data = []
        for song in result['songs']:
            cleaned_song = {
                "title": clean_text(song.get("title", "Unknown")),
                "style": clean_text(song.get("style",None)),
                "canta": clean_text(song.get("canta_as", None)),
                "orchestra": clean_text(song.get("orchestra", None)),
                "singer": clean_text(song.get("singer", None)),
                "year": song.get("year_recorded", None),
                "studio": clean_text(song.get("recording_studio", None)),
                "location": clean_text(song.get("location_recorded", None)),
                "record_number": song.get("recording_number_code",None),
            }
            discography_data.append(cleaned_song)
        return discography_data
    else:
        logging.error(f"Unexpected result format or missing 'songs' key: {result}")
        return []  # Return an empty list if there is an error


def main():
    logging.info("Program started.")  # Log the start of the program

    links_file = 'urls.txt'  # Input file with artist links
    processed_file = 'processedUrls.txt'  # File to keep track of processed links
    output_file = 'artist_discography.json'  # Output JSON file

    # Read URLs from the links file
    try:
        with open(links_file, 'r') as f:
            urls = [line.strip() for line in f.readlines() if line.strip()]  # Remove empty lines
    except Exception as e:
        logging.error(f"Error reading {links_file}: {e}")
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
                all_artists = json.load(f)  # Load existing artists
        except Exception as e:
            logging.error(f"Error reading {output_file}: {e}")
            backup_file = f"{output_file}.bak"
            os.rename(output_file, backup_file)  # Create a backup if JSON is malformed
            logging.warning(f"Backing up malformed JSON to {backup_file}")
            all_artists = {}  # Reinitialize the artist dictionary

    for url in urls:
        if url in completed_urls:
            logging.info(f"Skipping already processed URL: {url}")
            print(f"Skipping already processed URL: {url}")
            continue  # Skip processed URLs

        if not url:  # Check if the URL is empty
            logging.warning("Empty URL found, skipping.")
            continue

        try:
            logging.info(f"Processing link: {url}")
            print(f"Processing link: {url}")
            discography = scrape_artist_discography(url)  # Call your scraping function

            # Log the type and content of the discography result
            # logging.info(f"Discography content for {url}: {discography}")

            # Extract artist name from the URL and clean it up
            artist_name = clean_text(url.split("/")[-1].replace("-", " ").title())  # Example: "Anibal-Troilo" to "Anibal Troilo"
            logging.info(f"Processing artist:, {artist_name}")
            print('Processing artist:', artist_name)

            # Initialize artist entry if it doesn't exist
            if artist_name not in all_artists:
                all_artists[artist_name] = {"name": artist_name, "discography": []}

            # Append the songs to the artist's discography
            all_artists[artist_name]["discography"].extend(discography)

            # Append the processed URL to the processed file
            with open(processed_file, 'a') as f:
                f.write(url + '\n')
            logging.info(f"Successfully processed and recorded URL: {url}")

            # Write the updated artist dictionary to the JSON file after each URL is processed
            with open(output_file, 'w') as f:
                json.dump(all_artists, f, indent=4)  # Save as formatted JSON

        except Exception as e:
            logging.error(f"Error processing {url}: {e}")
            print(e)

    logging.info("All discography entries have been written to artist_discography.json.")

    if len(completed_urls) == len(urls):
        logging.info("Program completed successfully without errors.")
    else:
        logging.info("Program completed with some errors.")


if __name__ == "__main__":
    main()
