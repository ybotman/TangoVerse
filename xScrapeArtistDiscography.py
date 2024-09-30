import os
import logging
import json
from dotenv import load_dotenv
from scrapegraphai.graphs import SmartScraperGraph
from unidecode import unidecode  # Importing unidecode


# Load environment variables from .env file
load_dotenv()

# Retrieve the API key from environment variables
API_KEY = os.getenv("SCRAPEGRAPH_API_KEY")  # Ensure this variable is set in your .env file

# Check if API_KEY was successfully loaded
if API_KEY is None:
    logging.error("API key not found. Please set SCRAPEGRAPH_API_KEY in your .env file.")
    raise ValueError("API key not found.")

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


def clean_text(text):
    """Clean the input text by removing accents and non-text markings."""
    return unidecode(text)  # Convert accented characters to their ASCII equivalents



def scrape_artist_discography(url):
    # Create the SmartScraperGraph instance
    smart_scraper_graph = SmartScraperGraph(
        prompt=("I will give you a numbered list of what to parse. Please parse the following: "
                "1) the song title, 2) song style (tango, vals, milonga), "
                "3) the canta as (singer or instrumental), 4) the orchestra, "
                "5) the Singer (null if none, and name if canta not instrumental), "
                "6) the year recorded, 7) the recording studio (RCA, TC, etc), "
                "8) location recorded (Buenos Aires, New York, etc), "
                "9) the recording number code for the song. "
                "To help you parse the list of songs in the links, "
                "the first line of each has the above parsing data for 1 and 2, title and style. "
                "The second line has 3, 4, and 5 (with canta as instrumental or singer's name). "
                "The / separates the canta and orchestra. "
                "The last line has the 6, 5, 8, and 9 for year/date, place recorded, studio, and code."),
        source=url,
        config=graph_config
    )
    
    # Run the scraper and return the result
    return smart_scraper_graph.run()

def main():
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

    # Initialize all_artists here
    all_artists = {}

    # Load existing discographies from JSON file, if it exists
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r') as f:
                all_artists = json.load(f)  # Load existing artists
        except Exception as e:
            logging.error(f"Error reading {output_file}: {e}")

    for url in urls:
        if url in completed_urls:
            logging.info(f"Skipping already processed URL: {url}")
            continue  # Skip processed URLs

        if not url:  # Check if the URL is empty
            logging.warning("Empty URL found, skipping.")
            continue

        try:
            logging.info(f"Processing link: {url}")
            discography = scrape_artist_discography(url)  # Call your scraping function

            # Extract artist name from the URL
            artist_name = url.split("/")[-1].replace("-", " ").title()  # Example: convert "Anibal-Troilo" to "Aníbal Troilo"
            
            # Initialize artist entry if it doesn't exist
            if artist_name not in all_artists:
                all_artists[artist_name] = {"name": artist_name, "discography": []}

            # Add parsed discography data to the artist entry
            if discography:
                all_artists[artist_name]["discography"].extend(discography)  # Add new entries

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

    logging.info(f"All discography entries have been written to {output_file}.")


if __name__ == "__main__":
    main()
