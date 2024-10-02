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

    # Simplified and clearer prompt
    prompt = (
        "Extract all links from the artist's page, grouped into the following categories:"
        "\n- Articles (e.g., Biographies, Interviews, Histories, etc.)"
        "\n- Music (List of songs with titles and links)"
        "\n- Scores (Score links with title, type, year)"
        "\n- Obras (List of works with titles, type, year, link)"
        "\n- Discography"
        "\n- Other (Any links that do not fit into the above categories)"
        "\nReturn the data in a structured JSON format with appropriate groupings."
    )

    # Create the SmartScraperGraph instance
    smart_scraper_graph = SmartScraperGraph(
        prompt=prompt,
        source=url,
        config=graph_config
    )

    # Run the scraper and capture the result
    result = smart_scraper_graph.run()

    # Log the raw result for inspection
    logging.info(f"Raw result for {url}: {json.dumps(result, indent=4)}")

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
        # Adjust parsing logic based on actual result structure
        # For demonstration, let's assume result is a dictionary with keys matching our categories
        for category in ["Artist", "Article", "Music", "Scores", "Obras", "Discography", "Other"]:
            if category in result:
                if category == "Artist":
                    cleaned_data["Artist"] = {k: clean_text(v) for k, v in result["Artist"].items()}
                elif category == "Article":
                    cleaned_data["Article"] = result["Article"]  # Assuming it's already structured
                elif category in ["Music", "Scores", "Obras", "Discography", "Other"]:
                    cleaned_data[category] = result[category]  # Assuming lists of items
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

            artist_name = foundLinks["Artist"].get("name") or clean_text(url.split("/")[-1].replace("-", " ").title())
            logging.info(f"Processing artist: {artist_name}")
            print(f"Processing artist: {artist_name}")

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