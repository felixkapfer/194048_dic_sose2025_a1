#!/bin/bash
# Autor: Group 50
# Datum: 2025-04-19

# ======== Setup & configure path variables ========
# Get path to the script directory
SCRIPT_DIR=$(dirname "$0")
ROOT_DIR=$(realpath "$SCRIPT_DIR/")
echo "Root directory: $ROOT_DIR"

# ======== Utilities & helper functions ========
# Helper function to print a header
source "$ROOT_DIR/utils/utils.sh"

# ======== Setup & configure parameters ========
# Set parameters based on user input
DEFAULT_USER=$(whoami)              # Set the current user
ENVIRONMENT=${ENVIRONMENT:-0}   # 0 = lokal, 1 = Cluster
DEBUG_MODE=${DEBUG_MODE:-0}         # Default to 0 (no extra debugging)
INPUT_DIR=${INPUT_DIR:-""}          # Default dataset directory
OUTPUT_DIR=${OUTPUT_DIR:-""}        # Default output directory

print_header "1. Parameters provided by the user"
echo "Default user: $DEFAULT_USER"
echo "ENVIRONMENT: $ENVIRONMENT"
echo "Debug mode: $DEBUG_MODE"
echo "Dataset directory: $(get_parameter_value "INPUT_DIR")"
echo "Output directory: $(get_parameter_value "OUTPUT_DIR")"

# ======== Setup & configure environment ========
STREAMING_JAR="/usr/lib/hadoop/tools/lib/hadoop-streaming-3.3.6.jar"    # Set the default path for the streaming jar
STOPWORDS_FILE="${ROOT_DIR}/data/stopwords.txt"                         # Set the default path for the stopwords file
echo "Streaming jar: $STREAMING_JAR"
echo "Stopwords file: $STOPWORDS_FILE"

# ----- Validating the stopwords path -----
if [[ ! -f "${ROOT_DIR}/data/stopwords.txt" ]]; then
    handle_error "Stopwords file '${ROOT_DIR}/data/stopwords.txt' not found!"
fi

# ----- Set the input path -----
if  [[ -z "$INPUT_DIR" && "$ENVIRONMENT" -eq 0 ]]; then                             # If no input directory is provided by the user and the environment is local
    INPUT="${ROOT_DIR}/data/reviews_devset.json"
elif [[ -z "$INPUT_DIR" && "$DEBUG_MODE" -eq 1 && "$ENVIRONMENT" -eq 1 ]]; then     # If no input directory is provided by the user, the debug mode is enabled and the environment is set to cluster
    INPUT="hdfs:///user/dic25_shared/amazon-reviews/full/reviews_devset.json"
elif [[ -z "$INPUT_DIR" && "$DEBUG_MODE" -eq 0 && "$ENVIRONMENT" -eq 1 ]]; then     # If no input directory is provided by the user, the debug mode is disabled and the environment is set to cluster
    INPUT="hdfs:///user/dic25_shared/amazon-reviews/full/reviewscombined.json"
else                                                                                # If an input directory is provided by the user
    INPUT="$INPUT_DIR"
fi

echo "Input-file: $INPUT"

# ----- Validating the input path -----
if [[ "$ENVIRONMENT" -eq 1 ]]; then                                         # If the environment is set to cluster
    if ! hdfs dfs -test -e "$INPUT"; then                                   # Check if the input file exists on HDFS    
        handle_error "Input-file '$INPUT' not found on HDFS!"               # If not, handle the error
    fi
else                                                                        # If the environment is set to local
    if [[ ! -f "$INPUT" ]]; then                                            # Check if the input file exists on the local filesystem         
        handle_error "Input-file '$INPUT' not found in local filesystem!"   # If not, handle the error
    fi
fi

# ----- Set the output path -----
if [[ -z "$OUTPUT_DIR" && "$ENVIRONMENT" -eq 1 ]]; then                     # If no output directory is provided by the user and the environment is set to cluster
    OUTPUT="hdfs:///user/$DEFAULT_USER/amazon_reviews_chiotp"               # Set the default output path to HDFS
elif [[ -z "$OUTPUT_DIR" && "$ENVIRONMENT" -eq 0 ]]; then                   # If no output directory is provided and environment is local
    OUTPUT="${ROOT_DIR}/output/amazon_reviews_chiotp"                       # Use default local path for output
else                                                                        # If an output directory is provided by the user            
    OUTPUT="$OUTPUT_DIR"                                                    # Use the user-provided output path
fi
echo "Output-path: $OUTPUT"


# ----- Set counters file path -----
COUNTERS_FILE="${ROOT_DIR}/data/counters.txt"                               # Set the default path for the counters file
echo "Counters file: $COUNTERS_FILE"

# ======= Main Program ========
print_header "2. Running main program"

# Capture the start time
start_epoch=$(date +%s)                                         # Get the current epoch time
start_human=$(date '+%Y-%m-%d %H:%M:%S')                        # Get the current human-readable time
echo "Starting program at time: $start_human"

# ----- Running on cluster environment -----
if [[ "$ENVIRONMENT" -eq 1 ]]; then
    echo "Starting main program on the cluster..."

    # Prepare the WordCount job
    echo "Deleting old output files..."
    hdfs dfs -rm -r -f "${OUTPUT}/wordcount"                    # Remove old output files from HDFS in the wordcount directory
    hdfs dfs -rm -r -f "${OUTPUT}/chisq"                        # Remove old output files from HDFS in the chisq directory
    mkdir -p "$ROOT_DIR/results"                                # Create a local results directory

    # Execute the wordCountWrapper.py script
    # The script runs the WordCount job on the input data
    # The script runs on the Hadoop cluster
    python3 wordCountWrapper.py \
    -r hadoop \
    --py-files utils/logger.py,utils/utils.py \
    --hadoop-streaming-jar "$STREAMING_JAR" \
    --no-conf \
    --jobconf yarn.app.mapreduce.am.resource.memory-mb=8192 \
    --jobconf mapreduce.map.memory.mb=4096 \
    --jobconf mapreduce.reduce.memory.mb=4096 \
    --stopwords "${STOPWORDS_FILE}" \
    --counters "$COUNTERS_FILE" \
    --output "${OUTPUT}/wordcount" \
    "$INPUT"

    # Execute the chiSquaredJob.py script
    # The script runs the Chi-Squared job on the output of the WordCount job
    # The script runs on the Hadoop cluster
    python3 chiSquaredJob.py \
    -r hadoop \
    --py-files utils/logger.py,utils/utils.py \
    --hadoop-streaming-jar "$STREAMING_JAR" \
    --no-conf \
    --file "$COUNTERS_FILE" \
    --output "${OUTPUT}/chisq" \
    "${OUTPUT}/wordcount/part-*"

    # Get the path to the output file on HDFS and copy it to the local results directory
    SOURCE_PATH="hdfs:///user/$DEFAULT_USER/amazon_reviews_chiotp/chisq/part-00000"

    # Get the current timestamp for naming the output file
    timestamp_output=$(date '+%Y_%m_%d_%H_%M')

    # Set the target path for the output file in the local results directory
    TARGET_PATH="$ROOT_DIR/results/${timestamp_output}_chisq_output.txt"    

    echo "$SOURCE_PATH"
    echo "$TARGET_PATH"

    # Copy the output file from HDFS to the local results directory
    hdfs dfs -get "$SOURCE_PATH" "$TARGET_PATH"

    # ======= Results ========
    print_header "3. Results"
    echo "Done! Results can be found on HDFS under: $OUTPUT/chisq"

# ----- Running on local environment -----
else
    echo "Executing script on local environment..."

    # Prepare the WordCount job
    echo "Deleting old output files..."
    rm -rf "${OUTPUT}/wordcount"
    rm -rf "${OUTPUT}/chisq"
    mkdir -p "$ROOT_DIR/results"

    # Execute the wordCountWrapper.py script
    # The script runs the WordCount job on the input data
    # The script is run in local mode
    python3 wordCountWrapper.py \
    --py-files utils/logger.py,utils/utils.py \
    --stopwords "${STOPWORDS_FILE}" \
    --counters "$COUNTERS_FILE" \
    --output "${OUTPUT}/wordcount" \
    "$INPUT"

    # Execute the chiSquaredJob.py script
    # The script runs the Chi-Squared job on the output of the WordCount job
    # The script is run in local mode
    python3 chiSquaredJob.py \
    --py-files utils/logger.py,utils/utils.py \
    --file "$COUNTERS_FILE" \
    --output "${OUTPUT}/chisq" \
    "${OUTPUT}/wordcount/part-*"

    # Get the path to the output file on the local filesystem and copy it to the local results directory
    SOURCE_PATH="${OUTPUT}/chisq/part-00000"

    # Get the current timestamp for naming the output file
    timestamp_output=$(date '+%Y_%m_%d_%H_%M')

    # Set the target path for the output file in the local results directory
    TARGET_PATH="$ROOT_DIR/results/${timestamp_output}_chisq_output.txt"

    echo "$SOURCE_PATH"
    echo "$TARGET_PATH"
    cp "$SOURCE_PATH" "$TARGET_PATH"

    # ======= Results ========
    print_header "3. Results"
    echo "The results can be found locally in: $TARGET_PATH"

fi

# ======== Summary ========
# Print the summary of the program execution
print_header "4. Summary"

# Capture the end time
end_epoch=$(date +%s)
end_human=$(date '+%Y-%m-%d %H:%M:%S')

# Print the start and end times
echo "Program started at: $start_human (Epoch: $start_epoch)"
echo "Program ended at: $end_human (Epoch: $end_epoch)"

# Calculate and print the total execution time
duration_sec=$(( end_epoch - start_epoch ))
duration_hms=$(date -u -d "@$duration_sec" '+%H:%M:%S')

# Print the total execution time
echo "Total time needed for execution: ${duration_sec} in seconds (around $duration_hms)"


