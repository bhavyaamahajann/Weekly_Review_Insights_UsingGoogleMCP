import os
import sys
import time
import logging
from datetime import datetime, timedelta
import pandas as pd
from google_play_scraper import Sort, reviews
from dotenv import load_dotenv

# Add src to python path to import exceptions
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from src.utils.exceptions import PipelineAbortError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
APP_ID = "com.nextbillion.groww"
LANG = "en"
COUNTRY = "in"

def fetch_and_sync_reviews(app_id: str = APP_ID, window_weeks: int = 12, max_threshold: int = 5000) -> pd.DataFrame:
    """
    Fetches reviews from the Play Store and syncs them into a single master raw file.
    Only fetches new reviews by stopping when an existing review is encountered
    or the date threshold is reached.
    """
    raw_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/raw"))
    os.makedirs(raw_dir, exist_ok=True)
    output_csv = os.path.join(raw_dir, "reviews.csv")
    output_json = os.path.join(raw_dir, "reviews.json")

    # Load existing master reviews
    existing_df = None
    existing_texts = set()
    if os.path.exists(output_csv):
        try:
            existing_df = pd.read_csv(output_csv)
            if not existing_df.empty and "review_text" in existing_df.columns:
                # Store normalized text hashes or stripped texts to match duplicates
                existing_texts = set(existing_df["review_text"].astype(str).str.strip().tolist())
            logger.info(f"Loaded {len(existing_texts)} existing reviews from master file.")
        except Exception as e:
            logger.warning(f"Could not load existing master CSV: {e}. Starting fresh.")

    # Calculate window start date (naive UTC)
    start_date = datetime.utcnow() - timedelta(weeks=window_weeks)
    logger.info(f"Ingestion time window starts at (UTC): {start_date}")

    new_fetched = []
    continuation_token = None
    max_retries = 3
    page = 1
    stop_scraping = False

    while not stop_scraping:
        batch = None
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Fetching page {page} from Google Play (attempt {attempt})...")
                batch, continuation_token = reviews(
                    app_id,
                    lang=LANG,
                    country=COUNTRY,
                    sort=Sort.NEWEST,
                    count=200,
                    continuation_token=continuation_token
                )
                break
            except Exception as e:
                logger.warning(f"Error fetching reviews on attempt {attempt}: {e}")
                if attempt == max_retries:
                    raise PipelineAbortError(
                        "FETCH_TIMEOUT_OR_BLOCKED",
                        f"Review fetch failed after {max_retries} attempts: {e}"
                    )
                sleep_time = 10 if attempt == 1 else (30 if attempt == 2 else 60)
                logger.info(f"Sleeping for {sleep_time} seconds before retry...")
                time.sleep(sleep_time)

        if not batch:
            logger.info("No more reviews returned by Play Store.")
            break

        logger.info(f"Fetched batch of {len(batch)} reviews.")

        batch_kept = []
        for r in batch:
            review_at = r.get("at")
            if isinstance(review_at, str):
                review_at = datetime.fromisoformat(review_at.replace("Z", "+00:00")).replace(tzinfo=None)

            # Stop if the review is older than our rolling window
            if review_at < start_date:
                logger.info(f"Encountered review older than window date: {review_at}. Stopping scrape.")
                stop_scraping = True
                break

            review_text = r.get("content", "").strip()
            # Stop if we already have this review in our master file (incremental sync)
            if review_text in existing_texts:
                logger.info("Encountered a review already present in the master file. Stopping scrape.")
                stop_scraping = True
                break

            # Add to new fetched
            batch_kept.append({
                "review_text": review_text,
                "rating": r.get("score"),
                "thumbs_up_count": r.get("thumbsUpCount", 0),
                "app_version": r.get("appVersion"),
                "source": "google_play"
            })

        new_fetched.extend(batch_kept)
        logger.info(f"Kept {len(batch_kept)} new reviews from this batch. Total new so far: {len(new_fetched)}")

        # Hard safety cap to prevent infinite scraping if date/duplication checks miss
        if len(new_fetched) >= max_threshold:
            logger.info(f"New fetched reviews count ({len(new_fetched)}) reached target limit. Stopping.")
            break

        if not continuation_token:
            logger.info("No continuation token. End of reviews reached.")
            break

        page += 1
        time.sleep(1.0)

    # Convert new fetched to DataFrame
    new_df = pd.DataFrame(new_fetched)
    if not new_df.empty:
        new_df = new_df.dropna(subset=["review_text"])
        new_df["review_text"] = new_df["review_text"].astype(str).str.strip()
        new_df = new_df[new_df["review_text"] != ""]

    # Merge new with existing
    if existing_df is not None and not existing_df.empty:
        if not new_df.empty:
            # Combined and de-duplicated by review_text
            combined_df = pd.concat([new_df, existing_df], ignore_index=True)
            combined_df = combined_df.drop_duplicates(subset=["review_text"], keep="first")
        else:
            combined_df = existing_df
    else:
        if new_df.empty:
            raise PipelineAbortError(
                "FETCH_ZERO_REVIEWS",
                f"No reviews returned from Play Store for app {app_id}."
            )
        combined_df = new_df

    # Enforce schema columns
    schema_cols = ["review_text", "rating", "thumbs_up_count", "app_version", "source"]
    combined_df = combined_df[schema_cols]

    # Save to CSV and JSON
    combined_df.to_csv(output_csv, index=False)
    combined_df.to_json(output_json, orient="records", indent=2)
    logger.info(f"Master actual reviews saved. CSV: {output_csv}, JSON: {output_json}")
    logger.info(f"Total reviews in master actual file: {len(combined_df)}")

    return combined_df

def main():
    load_dotenv()
    window_weeks = int(os.getenv("REVIEW_WINDOW_WEEKS", 12))
    max_threshold = int(os.getenv("MAX_REVIEWS_THRESHOLD", 5000))

    try:
        fetch_and_sync_reviews(
            app_id=APP_ID,
            window_weeks=window_weeks,
            max_threshold=max_threshold
        )
    except PipelineAbortError as e:
        logger.error(f"Pipeline Aborted: {e.message}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected execution error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
