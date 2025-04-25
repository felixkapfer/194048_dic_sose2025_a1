#!/usr/bin/env python3
import json

from mrjob.job import MRJob
from mrjob.step import MRStep
from mrjob.protocol import RawProtocol

class ChiSquareJob(MRJob):
    """
    A MapReduce job that calculates Chi-Squared scores for words across categories,
    based on previously computed word count statistics. It identifies the top 75 words
    per category that are most representative of that category using the Chi-Squared statistic.
    """

    # Input: wordcount per category
    # Output: top 75 words per category depending on ChiSquared value
    OUTPUT_PROTOCOL = RawProtocol       # Output as raw strings instead of default JSON
    FILES = []                          # Files required for the job, passed via --file

    # Globals for review statistics loaded from counters.txt
    total_nr_reviews = 0
    counters = {}

    def configure_args(self):
        """
        Define custom command-line arguments.
        Registers the --file argument to specify the path to the counters.txt file.
        """
        super(ChiSquareJob, self).configure_args()

        # Add a command-line argument for the counters file
        self.add_file_arg(
            '--file',
            help='Path to counters.txt (passed via main.sh with --file)'
        )

    def read_in_counters(self):
        """
        Reads the counters file that contains:
        - the total number of reviews
        - the number of reviews per category

        This data is used in the mapper to compute the Chi-Squared statistic.
        """
        # Get the path to the counters file from command-line arguments
        counters_file_name = self.options.file

        # Read total review count and per-category counts
        with open(counters_file_name, "r") as reader:
            line = reader.readline().strip()
            if line:
                # Split the string into total reviews and the category count dictionary
                self.total_nr_reviews, counters_str = line.split(" ", 1)
                self.total_nr_reviews = int(self.total_nr_reviews)

                # Replace single quotes for valid JSON
                self.counters = json.loads(counters_str.replace("'", '"'))

    def chi_square_mapper(self, _, line):
        """
        Mapper function that:
        - Parses each line of word frequency data per category
        - Computes the Chi-Squared value for each (word, category) pair
        - Emits: category → (word, chi-squared value)
        """
        if not line:
            return
        try:
            # Split on tab to separate the word from the JSON dict
            word, category_dict_str = line.split('\t', 1)
            category_dict_str = category_dict_str.strip()

            # Parse the Python-dict style string into JSON
            category_dict = json.loads(category_dict_str.replace("'", '"'))

            # Clean up the word (remove surrounding quotes)
            word = word.strip().replace('"', '')

        except Exception:
            # Skip malformed lines
            return

        # For each category, compute the chi-squared statistic
        for category, wordcount in category_dict.items():
            A = wordcount
            B = sum(category_dict.values()) - A
            C = int(self.counters.get(category, 0)) - A
            D = int(self.total_nr_reviews) - A - B - C
            
            # Avoid division by zero
            if any(factor == 0 for factor in [(A+B), (A+C), (B+D), (C+D)]):
                continue
            chi_squared = (int(self.total_nr_reviews) * (A * D - B * C) ** 2) /((A+B) * (A+C) * (B+D) * (C+D))
            yield category, (word, chi_squared)

    def chi_square_sorted_reducer(self, category, word_chi_squared_list):
        """
        Reducer that:
        - Collects all (word, chi-squared value) pairs for each category
        - Sorts them by chi-squared value in descending order
        - Emits the top 75 words per category
        """

        # Take top 75 words by chi-squared value
        chi_squared_sorted = sorted(word_chi_squared_list, key=lambda x: x[1], reverse=True)[:75]

        # Emit a dictionary of top words for this category
        yield None, (category, dict(chi_squared_sorted))

    def output_reducer(self, _, category_sorted_words):
        """
        Final reducer that:
        - Outputs each category with its top chi-squared words
        - Outputs the union of all top words across all categories
        """
        # Final formatting
        category_sorted_words = list(category_sorted_words)

        # Gather all unique words across all categories
        words = list({word for _, cat_dict in category_sorted_words for word in cat_dict})

        # Emit each category with its top words
        for category, word_chi_squared_dict in sorted(category_sorted_words, key=lambda x: x[0]):
            yield category, str(word_chi_squared_dict)

        # Also output the combined set of all words
        yield None, str(sorted(words))

    def steps(self):
        """
        Defines the two-step MapReduce job:
        1. Compute chi-squared scores and extract top words per category
        2. Format the output and emit all categories and union of words
        """
        return [
            MRStep(mapper_init=self.read_in_counters,
                   mapper=self.chi_square_mapper,
                   reducer=self.chi_square_sorted_reducer),
            MRStep(reducer=self.output_reducer)
        ]

if __name__ == '__main__':
    ChiSquareJob.run()