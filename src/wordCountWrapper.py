#!/usr/bin/env python3

# Import necessary libraries
import os
import sys

from utils.logger import Logger
from wordCountJob import WordCountJob

# Initialize module-level logger
logger = Logger(__name__)

if __name__ == "__main__":
    # Log the start of the job execution
    logger.info("Starting WordCount job...")

    # Use the provided command-line arguments as input files
    job = WordCountJob(args=sys.argv[1:])

    # Get the path for the counters file from the job options
    counters_path = job.options.counters

    # Ensure that the directory for the counters file exists
    os.makedirs(os.path.dirname(os.path.abspath(counters_path)) or ".", exist_ok=True)

    # Run the job with the provided runner
    with job.make_runner() as runner:
        logger.info("Running job with the runner...")
        runner.run()

        # Combine counters from all steps and calculate total review count
        all_counters = runner.counters()
        nr_reviews = sum(
            step.get("counter all reviews", {}).get("counter", 0)
            for step in all_counters
        )

        # Initialize dictionary to store counts per category
        nr_reviews_per_category = {}
        for step in all_counters:
            for cat, cnt in step.get("counter categories", {}).items():
                nr_reviews_per_category[cat] = nr_reviews_per_category.get(cat, 0) + cnt
        
        # Log the results of the counters
        logger.info(f"Total reviews: {nr_reviews}")
        logger.info(f"Reviews per category: {nr_reviews_per_category}")
        
        # Write the counter results to the counters file
        with open(counters_path, "w") as writer:
            writer.write(f"{nr_reviews} {nr_reviews_per_category}")

        # Output the word count to stdout, this is the output of the mapper/reducer
        for raw_line in runner.cat_output():
            if b'\t' not in raw_line:
                continue
            for word, counts in job.parse_output([raw_line]):
                print(word, counts, "\n", end="")

    # Log the completion of the job
    logger.info("WordCount job completed successfully.")
