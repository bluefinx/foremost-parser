#!/bin/bash

# This script reads in the options to start the tool
# it sets the environment variables for Docker Compose
# and then starts Docker Compose

# environment variables for Docker:
# - INPUT_PATH
# - OUTPUT_PATH
# - FLUSH
# - REPORT
# - WITH_IMAGES

# clear environment variables
> .env

# set flags
INPUT_PROVIDED=false
OUTPUT_PROVIDED=false
FLUSH=false
STORE=false

# show help for -h or --help
help(){
    echo "This tool reads in a Foremost input directory, parses its content and metadata and generates a report in the output directory."
    echo ""
    echo "If --store option is not included, all data is deleted from the database afterwards."
    echo ""
    echo "NOTE: The Foremost audit file must be named 'audit.txt'."
    echo ""
    echo "Usage: $0 [OPTIONS] -i <path_to_input> -o <path_to_output>"
    echo ""
    echo "Options:"
    echo "  -h, --help            Show this help message and exit"
    echo "  -i, --input           Foremost input directory (absolute path) [required]"
    echo "  -o, --output          Report output directory (absolute path) [required]"
    echo "  -f, --flush           Delete Docker persistent volumes and output directory contents before startup [default: false]"
    echo "  -r, --report          Report format (supported: json) [default: json]"
    echo "  -s, --store           Store all parsed images in the database [default: false]"
    echo "  --with-images         Include image files in the report (jpg, jpeg, png, gif, webp, svg) [default: false]"
    echo ""
}

# validate the provided input path to make sure it exists and is a dir
## based on @jimmij's code from https://unix.stackexchange.com/questions/256434/check-if-shell-variable-contains-an-absolute-path
validate_input_path(){
    # -n: String is not zero
    # -d: file exists and is a directory
    # -r: file is readable
    # ^/: path starts with / (absolute)
    if [ -n "$1" ] && [ -d "$1" ] && [ -r "$1" ] && [[ "$1" =~ ^/ ]]; then
        INPUT_PROVIDED=true
        export INPUT_PATH="$1"
        echo "INPUT_PATH=$1" >> .env
    else
        echo "Please include a valid absolute path for the input folder."
        exit 1
    fi
}

# validate the provided output path to make sure it exists and is a dir
## based on @jimmij's code from https://unix.stackexchange.com/questions/256434/check-if-shell-variable-contains-an-absolute-path
validate_output_path(){
    # -n: String is not zero
    # -d: file exists and is a directory
    # -r: file is readable
    # -w: file is writeable
    # ^/: path starts with / (absolute)
    if [ -n "$1" ] && [ -d "$1" ] && [ -r "$1" ] && [ -w "$1" ] && [[ "$1" =~ ^/ ]]; then
        OUTPUT_PROVIDED=true
        export OUTPUT_PATH="$1"
        echo "OUTPUT_PATH=$1" >> .env
    else
        echo "Please include a valid absolute path for the output folder that is writeable."
        exit 1
    fi
}

# so, long story short, deleting the data from the database with SQLAlchemy
# IS A MESS and corrupted my auto increment, that's why it is done here. 
flush_data(){
    if [ "$INPUT_PROVIDED" != "true" ] && [ "$OUTPUT_PROVIDED" != "true" ]; then
        echo "Please include valid absolute paths to the input and the output folders."
        exit 1
    else
        # Docker data
        docker compose down -v

        # output dir data
        if [ -d "$OUTPUT_PATH" ]; then
            echo "Clearing output folder: $OUTPUT_PATH"
            rm -rf "${OUTPUT_PATH:?}/"*
        fi
        echo "Database and files flushed."
    fi
}

# validate the provided report format (python script sets json as default)
validate_report_format(){
    local format="$1"
    # allowed formats
    local allowed=("json")

    # check if format is in allowed list
    for f in "${allowed[@]}"; do
        if [[ "$format" == "$f" ]]; then
            echo "REPORT=$format" >> .env
            return 0
        fi
    done

    echo "Invalid report format: $format. Allowed formats are: ${allowed[*]}"
    exit 1
}

# if input is -h or --help, show help and exit
for arg in "$@"; do
    if [[ "$arg" == "-h" || "$arg" == "--help" ]]; then
        help
        exit 0
    fi
done

# the tool needs at least an input and output path, so now look if present
if [[ "$#" -eq 0 ]]; then
    echo "Please include valid absolute paths to the input and the output folders."
    exit 1
fi

# parse the options
while [[ "$#" -gt 0 ]]; do
    case "$1" in
        -i|--input)
            validate_input_path $2
            shift 2
            ;;
        -o|--output)  
            validate_output_path $2
            shift 2
            ;;
        -f|--flush)
            FLUSH=true
            shift
            ;;
        -r|--report)
            validate_report_format $2
            shift 2
            ;;
        -s|--store)
            STORE=true
            shift
            ;;
        --with-images)
            echo "IMAGES=true" >> .env
            shift
            ;;
        *)
            echo "Invalid options. Please provide at least an input and output path."
            exit 1
            ;;
    esac
done

# for now, make sure there is an audit.txt in the Foremost folder.
if [ ! -f "$INPUT_PATH/audit.txt" ]; then
    echo "Error: audit.txt not found in input directory '$INPUT_PATH'!" >&2
    exit 1
fi

# Flush only after parsing all paths
if [ "$FLUSH" = "true" ]; then
    flush_data
fi

# ask if .DS_Store files should be removed or kept
# this is not done automatically in Python since there could be one on purpose 
if [[ $(uname) == "Darwin" ]]; then
    printf "Do you want to remove .DS_Store files in the input folder? (Y/n)"
    read -r REMOVE_DS_STORE

    # default is "y"
    REMOVE_DS_STORE=${REMOVE_DS_STORE:-y}
    REMOVE_DS_STORE=$(echo "$REMOVE_DS_STORE" | tr -d '\r\n' | tr '[:upper:]' '[:lower:]')

    if [[ "$REMOVE_DS_STORE" = "y" ]]; then

        # first, check if dir is writeable
        if [ ! -w "$INPUT_PATH" ]; then
            printf "Warning: The folder '%s' is not writeable.\n" "$INPUT_PATH"
            printf "Do you want to continue anyway or abort? (C to continue / A to abort) [A]"

            read -r CONTINUE_CHOICE
            CONTINUE_CHOICE=${CONTINUE_CHOICE:-A}
            CONTINUE_CHOICE=$(echo "$CONTINUE_CHOICE" | tr -d '\r\n' | tr '[:upper:]' '[:lower:]')

            if [[ "$CONTINUE_CHOICE" == "a" ]]; then
                echo "Aborting script."
                exit 1
            else
                echo "Skipping .DS_Store removal and continuing..."
            fi
        else
            echo "Removing all .DS_Store files in $INPUT_PATH ..."
            find "$INPUT_PATH" -name ".DS_Store" -type f -exec rm -f {} +
            echo ".DS_Store files removed."
        fi
    else
        echo "Keeping .DS_Store files."
    fi
fi

# create the password file for the db
if [ ! -f "./db/password.txt" ]; then
    printf "No password file found. Please enter a password for the database:"
    read -s DB_PASSWORD
    echo ""
    mkdir -p ./db
    echo "$DB_PASSWORD" > ./db/password.txt
    echo "Password file created at ./db/password.txt"
fi

# set permissions
## Linux complicates everything and therefore, the password file needs to be less secure
## so the Docker container can access it
if [[ $(uname) == "Darwin" ]]; then
    chmod 600 ./db/password.txt
else
    chmod 644 ./db/password.txt
fi

# the tool needs at least an input and output path, so now look if present
if [ "$INPUT_PROVIDED" = "true" ] && [ "$OUTPUT_PROVIDED" = "true" ]; then
    echo "Starting Docker now..."
    docker compose run --build --rm backend

    if [ "$STORE" = "false" ]; then
        echo "Deleting Docker volumes."
        docker compose down -v
        echo "Cleanup finished."
    fi
else
    echo "Please include valid absolute paths to the input and the output folders."
    exit 1
fi