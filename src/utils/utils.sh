#!/bin/bash
# helpers.sh - Utility functions for run_job.sh

# Print a formatted header
print_header() {
  echo ""
  echo "============================================"
  echo "$1"
  echo "============================================"
}

# Helper to validate if a paramet is set
get_parameter_value() {
    local var_name="$1"
    local value="${!var_name}"

    if [ -z "$value" ]; then
        echo "not provided (default is used according to environment)"
    else
        echo "$value"
    fi
}


# Helper to check whether a file exists
check_file_exists() {
    local file_name="$1"
    local input_file="$2"
    if [[ ! -f "$input_file" ]]; then
        handle_error "$file_name File '$input_file' not found!"
    else
        echo "$file_name File: $input_file"
    fi 
}

# Helper to check whether a file exists on HDFS
check_hadoop_file_exists() {
    local file_name="$1"
    local input_file="$2"
    if ! hdfs dfs -test -e "$input_file"; then
        handle_error "$file_name HDFS file: '$input_file' not found ond HDFS!"
    else
        echo "$file_name HDFS file: $input_file"
    fi 
}



# Clean up temporary files
cleanup() {
  if [[ "$TU_CLUSTER" -eq 0 && -f "$TEMP_FILE" ]]; then
    rm -f "$TEMP_FILE"
    echo "Temporary files have been cleaned up."
  fi
}

# Handle errors
handle_error() {
  echo "Error: $1"
  cleanup
  exit 1
}

