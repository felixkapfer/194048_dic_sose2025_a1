# 194048_dic_sose2025_a1

Assignment 1 for course 194.048 Data-intensive Computing (SoSe 2025) – MapReduce-based text processing on Amazon Reviews with chi-square feature selection. Implemented with mrjob and executed on a Hadoop cluster.
Implementation performed by Group 50.

## Project Overview

This repository provides a two-step MapReduce pipeline for processing Amazon-style review data:

1. **Word Count** (`wordCountWrapper.py` / `WordCountJob`)  
   - Reads raw JSON reviews, tokenizes text, filters stopwords, and counts word occurrences per product category.
   - Accumulates MRJob counters:  
     - **Total reviews**  
     - **Reviews per category**  
   - Writes counter results to `counters.txt`, alongside the usual word-count output.

2. **Chi-Squared Analysis** (`chiSquaredJob.py`)  
   - Loads `counters.txt` to obtain global review stats.  
   - Computes Chi-Squared scores for each word/category pair.  
   - Emits the top 75 words per category (highest Chi-Squared) and a combined word set.

---

## Getting Started

### Clone the Repository

Clone the project from GitHub:

```bash
git clone https://github.com/felixkapfer/194048_dic_sose2025_a1.git
cd 194048_dic_sose2025_a1/src
```

### Prerequisites

- **Python 3.7+** with a virtual environment  
- **mrjob** library  
- **Hadoop** cluster (for production) or local execution

Install Python dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Folder Structure

```bash
/
├── LICENSE
├── README.md
├── requirements.txt         # Python deps (e.g. mrjob)
└── src
    ├── data
    │   ├── reviews_devset.json   # Sample review data
    │   └── stopwords.txt         # Stopwords list
    ├── main.sh                   # Orchestration script
    ├── wordCountWrapper.py       # Wrapper for WordCountJob
    ├── wordCountJob.py           # MRJob: word↔category count
    ├── chiSquaredJob.py          # MRJob: Chi-Squared analysis
    └── utils
        ├── logger.py             # Simple logging wrapper
        ├── utils.py              # get_arg_value, bash helpers
        └── utils.sh              # bash helper functions
```

- **`src/main.sh`**: Single-entrypoint script to run both steps.
- **`src/data/`**: Input JSON and stopwords.
- **`src/wordCountJob.py`** & **`src/chiSquaredJob.py`**: Core MRJob implementations.
- **`src/wordCountWrapper.py`**: Handles counters extraction before piping to Chi-Squared job.
- **`src/utils/`**: Shared helpers (shell & Python).

---

## Usage

Run the entire pipeline locally with debug output:

```bash
DEBUG_MODE=1 ENVIRONMENT=0 bash ./main.sh
```

Or on a Hadoop cluster:

```bash
DEBUG_MODE=0 ENVIRONMENT=1 bash ./main.sh
```

### Important Notes

When executing the script, make sure you execute it within the `project/src` directory! To do so, enter `cd 194048_dic_sose2025_a1/src` into your CLI before executing the pipeline script!

### Environment Variables

- **`DEBUG_MODE`**  
  - `1` = enable debug-specific code paths (e.g. use `reviews_devset.json` in HDFS).  
  - `0` = normal execution.

- **`ENVIRONMENT`**  
  - `0` = Local mode (reads/writes from local filesystem).  
  - `1` = Cluster mode (reads/writes from HDFS).

### `main.sh` Parameters

Within `main.sh`, the following MRJob flags are passed:

- **Word Count Step**

  ```bash
  python3 src/wordCountWrapper.py \
    -r hadoop \                       # Use Hadoop runner (cluster) or inline (local)
    --hadoop-streaming-jar "$STREAMING_JAR" \
    --no-conf \                       # Skip mrjob default config
    --jobconf yarn.app.mapreduce.am.resource.memory-mb=8192 \
    --jobconf mapreduce.map.memory.mb=4096 \
    --jobconf mapreduce.reduce.memory.mb=4096 \
    --stopwords "$STOPWORDS_FILE"     # Path to stopwords.txt
    --counters "$OUTPUT/wordcount/counters.txt"   # Output path for counters.txt
    --output "$OUTPUT/wordcount"      # WordCount output directory
    "$INPUT"                          # Input JSON file or HDFS path
  ```

- **Chi-Squared Step**

  ```bash
  python3 src/chiSquaredJob.py \
    -r hadoop \
    --hadoop-streaming-jar "$STREAMING_JAR" \
    --no-conf \
    --file "$OUTPUT/wordcount/counters.txt"   # Pass counters.txt to job
    --output "$OUTPUT/chisq"                  # ChiSquared output dir
    "$OUTPUT/wordcount/part-*"                # Input wordcount parts
  ```

---

## Outputs

- **`$ROOT_DIR/output/amazon_reviews_chiotp/wordcount/`**  
  - `part-00000`, `part-00001`, … : Word count results.  
  - `counters.txt` : Two values: `<total_reviews> <JSON-dict of category counts>`

- **`$ROOT_DIR/output/amazon_reviews_chiotp/chisq/`**  
  - `part-00000` : Chi-Squared top words per category & combined word list.

- **`$ROOT_DIR/results/`**  
  - Timestamped `chisq_output.txt` local copy of cluster result.

---

## Important Notes

- **Ensure `stopwords.txt` exists** under `src/data/`, or the job increments a counter and continues without stopwords.
- **Memory settings** in `--jobconf` should match cluster resource availability.
- **Logging**: Adjust log levels in `utils/logger.py` to control verbosity.

---

Please refer to the inline docstrings and comments within each script for deeper implementation details.