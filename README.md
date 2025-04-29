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
├── LICENSE                       # Project license
├── README.md                     # Project documentation (this file)
├── requirements.txt              # Python dependencies (mrjob, etc.)
└── src                         # Source code and data
    ├── chiSquaredJob.py        # MRJob: Chi-Squared feature selection job
    ├── data                    # Input and intermediate data
    │   ├── counters.txt        # Output counters from word count step
    │   ├── reviews_devset.json # Sample Amazon review dataset for debug
    │   └── stopwords.txt       # Stopwords list for filtering
    ├── logs                    # YARN application logs fetched manually
    │   └── <APPLICATION_ID>.log
    ├── main.sh                 # Orchestration script for the full pipeline
    ├── output                  # Local-mode outputs (created only when ENVIRONMENT=0)
    │   └── amazon_reviews_chiotp
    │       ├── wordcount       # Word count step output files
    │       │   ├── part-00000
    │       │   └── ...
    │       └── chisq           # Chi-Squared step output files
    │           └── part-00000
    ├── report                  # Report
    │   └── report.pdf
    ├── results                 # Local copy of Chi-Squared results
    │   └── 2025_04_29_19_27_chisq_output.txt
    ├── utils                   # Shared utility modules and scripts
    │   ├── logger.py           # Logging helper class
    │   ├── utils.py            # Python helper functions
    │   └── utils.sh            # Shell helper functions
    ├── wordCountJob.py         # MRJob: word count per category
    └── wordCountWrapper.py     # Wrapper to extract counters before Chi-Squared
```

- **`src/main.sh`**: Orchestration script (single entrypoint to run both steps).
- **`src/data/`**: Input and intermediate data:
  - `reviews_devset.json`: sample review dataset for debug.
  - `stopwords.txt`: list of stopwords for filtering.
  - `counters.txt`: counters output from the word count step.
- **`src/wordCountJob.py`** & **`src/chiSquaredJob.py`**: Core MRJob implementations.
- **`src/wordCountWrapper.py`**: Wrapper to extract counters before Chi-Squared job.
- **`src/utils/`**: Shared helpers (shell & Python).

- The `logs/` folder is created when you fetch YARN logs per instructions below.
- The `output/` directory is only generated during a local run of the pipeline (`ENVIRONMENT=0`).
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

- **`$ROOT_DIR/data/counters.txt`**  
  - Contains two values: <total_reviews> <JSON-dict of category counts> produced by the Word Count step.
- **`$ROOT_DIR/output/amazon_reviews_chiotp/wordcount/`**  
  - `part-00000`, `part-00001`, … : Word count results.  

- **`$ROOT_DIR/output/amazon_reviews_chiotp/chisq/`**  
  - `part-00000` : Chi-Squared top words per category & combined word list.

- **`$ROOT_DIR/results/`**  
  - Timestamped `chisq_output.txt` local copy of cluster result.

---

## Retrieving YARN Application Logs

1. **Find your Application ID**  
   Run:

   ```bash
   yarn application -list
   ```

   This will list all running (or recently finished) YARN applications.  
   Locate the line where the **USER** column matches your username, and copy the **Application ID** (e.g. `application_1612345678901_0001`).

2. **Fetch and save your logs**  
   Create a `logs/` folder and download the consolidated logs into it:

   ```bash
   mkdir -p ./logs
   yarn logs -applicationId <APPLICATION_ID> > ./logs/<APPLICATION_ID>.log
   ```

   Replace `<APPLICATION_ID>` with the ID you found in step 1.

That’s it! You’ll now have a file at `./logs/<APPLICATION_ID>.log` containing all of your application’s logs.

---

## Important Notes

- **Ensure `stopwords.txt` exists** under `src/data/`, or the job increments a counter and continues without stopwords.
- **Memory settings** in `--jobconf` should match cluster resource availability.
- **Logging**: Adjust log levels in `utils/logger.py` to control verbosity.

---

Please refer to the inline docstrings and comments within each script for deeper implementation details.