import json
import logging

# Configure logging
logging.basicConfig(
    filename='analytics.log',  # Log file
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def count_items(data):
    counts = {
        "total_artists": 0,
        "total_articles": 0,
        "total_scores": 0,
        "total_music": 0,
        "total_obras": 0,
        "total_discography": 0,
        "total_other": 0
    }

    for artist, details in data.items():
        counts["total_artists"] += 1

        # Count articles
        if "Article" in details:
            for category, articles in details["Article"].items():
                counts["total_articles"] += len(articles)

        # Count scores
        if "Scores" in details:
            counts["total_scores"] += len(details["Scores"])

        # Count music
        if "Music" in details:
            counts["total_music"] += len(details["Music"])

        # Count obras
        if "Obras" in details:
            counts["total_obras"] += len(details["Obras"])

        # Count discography
        if "Discography" in details:
            counts["total_discography"] += len(details["Discography"])

        # Count other
        if "Other" in details:
            counts["total_other"] += len(details["Other"])

    return counts

def main():
    input_file = 'discoveredLinks.json'

    # Load the JSON data from the file
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        logging.error(f"Error reading {input_file}: {e}")
        print(f"Error reading {input_file}: {e}")
        return

    # Count the items in the JSON data
    counts = count_items(data)

    # Print the counts
    print("Analytics for discoveredLinks.json:")
    print(f"Total Artists: {counts['total_artists']}")
    print(f"Total Articles: {counts['total_articles']}")
    print(f"Total Scores: {counts['total_scores']}")
    print(f"Total Music: {counts['total_music']}")
    print(f"Total Obras: {counts['total_obras']}")
    print(f"Total Discography: {counts['total_discography']}")
    print(f"Total Other: {counts['total_other']}")

    # Log the counts
    logging.info("Analytics for discoveredLinks.json:")
    logging.info(f"Total Artists: {counts['total_artists']}")
    logging.info(f"Total Articles: {counts['total_articles']}")
    logging.info(f"Total Scores: {counts['total_scores']}")
    logging.info(f"Total Music: {counts['total_music']}")
    logging.info(f"Total Obras: {counts['total_obras']}")
    logging.info(f"Total Discography: {counts['total_discography']}")
    logging.info(f"Total Other: {counts['total_other']}")

if __name__ == "__main__":
    main()