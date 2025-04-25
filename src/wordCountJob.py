#!/usr/bin/env python3
import json
from mrjob.job import MRJob
from mrjob.step import MRStep

class WordCountJob(MRJob):
    """
    A MapReduce job that counts the frequency of words in text reviews,
    grouped by product category, while ignoring stopwords.
    """
    FILES = []

    def configure_args(self):
        """
        Add command-line arguments to the job:
        - --stopwords: Path to the stopwords file.
        - --counters: Path where counters.txt will be written.
        """
        super(WordCountJob, self).configure_args()

        # Add the argument for the stopwords file
        self.add_file_arg(
            '--stopwords',
            help='Path to stopwords file'
        )

        # Add the argument for the counters file, with a default value
        self.add_passthru_arg(
            '--counters',
            default='counters.txt',
            help='Pfad, wohin counters.txt geschrieben wird'
        )

    def mapper_init(self):
        """
        Initializes the mapper by loading stopwords from file and
        setting up a translation table for cleaning tokens.
        """

        # Load stopwords once for the mapper
        try:
            with open(self.options.stopwords) as f:
                self.stopwords = set(line.strip() for line in f)

        # If loading fails, continue with an empty stopwords list
        except Exception:
            self.stopwords = set()
            self.increment_counter('init', 'stopwords_load_fail', 1)

        # Define characters that should be treated as spaces
        tokens = '()[]{}.!?,;:+=-_"~#@&*%€$§/\\1234567890\t' + "'"
        self.token_to_space = {ord(t): ' ' for t in tokens}

    def mapper(self, _, line):
        """
        Tokenizes each review line into words, filters out stopwords,
        and emits (word, category) -> 1.
        """

        try:
            # Parse each line as JSON and extract category and review text
            review = json.loads(line)
            category = review.get('category', 'Unknown')
            text = review.get('reviewText', '').lower()
            
            # Increment counters for total reviews and per category
            self.increment_counter('counter all reviews', 'counter', 1)
            self.increment_counter('counter categories', category, 1)
        
        # Skip malformed or invalid lines
        except:
            return

        # Tokenize and clean the review text
        words = set(text.translate(self.token_to_space).split())
        for word in words:
            if word and word not in self.stopwords:
                # Emit each word with its category and count of 1
                yield (word, category), 1

    def combiner(self, key, counts):
        """
        Combines intermediate values locally for efficiency,
        summing all counts for (word, category) keys.
        """

        # Local aggregation to reduce data transfer
        word, category = key
        yield (word, category), sum(counts)

    def reducer(self, key, counts):
        """
        Aggregates the global count of words per category.
        Emits: word -> (category, total count)
        """

        # Global aggregation of word-category pairs
        word, category = key
        yield word, (category, sum(counts))

    def steps(self):
        """
        Defines the job flow consisting of two MRSteps:
        1. Word/category counting
        2. Aggregation per word over all categories
        """

        # Define the two-step MapReduce process
        return [
            MRStep(
                mapper_init=self.mapper_init,
                mapper=self.mapper,
                combiner=self.combiner,
                reducer=self.reducer
            ),
            MRStep(
                reducer=self.final_reducer
            )
        ]

    def final_reducer(self, word, category_counts):
        """
        Collects all categories for each word and aggregates their counts
        into a dictionary. Emits: word -> {category: count, ...}
        """

        # Aggregate all category counts for each word
        totals = {}
        for category, count in category_counts:
            totals[category] = totals.get(category, 0) + count
        
        # Emit the final output
        yield word, totals

if __name__ == '__main__':
    WordCountJob.run()