#!/bin/bash

# This script reads in the options to start the tool
# it sets the environment variables for Docker Compose
# and then starts Docker Compose

# environment variables:
# - INPUT_PATH
# - OUTPUT_PATH
# - OVERWRITE
# - FLUSH
# - REGENERATE

# clear environment variables
> .env

# set flag for path
INPUT_PROVIDED=false
OUTPUT_PROVIDED=false

# show help for -h or --help
help(){
    echo "This tool reads in a foremost input dir, parses its content, stores it in a database and generates an HTML report in the output dir."
    echo ""
    echo "Usage: $0 [OPTIONS] -i <path_to_input> -o <path_to_output>"
    echo ""
    echo "Options:"
    echo "  -h, --help          shows the help info"
    echo "  -i, --input         the foremost input directory"
    echo "  -o, --output        the HTML report output directory"
    echo "  -f, --flush         deletes the docker persistent volumes before startup"
    echo "  --with-images       includes image files in report (supported formats: jpg, jpeg, png, gif, webp, svg)"
    echo ""
}

# validate the provided input path to make sure it exists and is a dir
## based on @jimmij's code from https://unix.stackexchange.com/questions/256434/check-if-shell-variable-contains-an-absolute-path
validate_input_path(){
    # -n: String is not zero; -d: file exists and is a dir; make sure it starts with / (absolute)
    if [ -n "$1" ] && [ -d "$1" ] && [[ "$1" =~ ^/ ]]; then
        INPUT_PROVIDED=true
        export INPUT_PATH="$1"
        echo "INPUT_PATH=\"$1\"" >> .env
    else
        echo "Please include a valid absolute path for the input folder."
        exit 1
    fi
}

# validate the provided output path to make sure it exists and is a dir
## based on @jimmij's code from https://unix.stackexchange.com/questions/256434/check-if-shell-variable-contains-an-absolute-path
validate_output_path(){
    # -n: String is not zero; -d: file exists and is a dir; make sure it starts with / (absolute) and make sure it's writeable
    if [ -n "$1" ] && [ -d "$1" ] && [[ "$1" =~ ^/ ]] && [ -w "$1" ]; then
        OUTPUT_PROVIDED=true
        echo "OUTPUT_PATH=\"$1\"" >> .env
    else
        echo "Please include a valid absolute path for the output folder that is writeable."
        exit 1
    fi
}

# so, long story short, deleting the data from the database with SQLAlchemy
# IS A MESS and corrupted my auto increment, that's why it is done here. 
flush_database(){
    if [ "$INPUT_PROVIDED" != "true" ] && [ "$OUTPUT_PROVIDED" != "true" ]; then
        echo "Please include valid absolute paths to the input and the output folders."
        exit 1
    else
        docker compose down -v
        echo "Database and files flushed."
    fi
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
            flush_database
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

# ask if .DS_Store files should be removed or kept
echo "Do you want to remove .DS_Store files in the input folder? (y/n)"
read -r REMOVE_DS_STORE

if [ "$REMOVE_DS_STORE" == "y" ]; then
    echo "Removing all .DS_Store files in $INPUT_PATH ..."
    find "$INPUT_PATH" -name ".DS_Store" -type f -delete
    echo ".DS_Store files removed."
else
    echo "Keeping .DS_Store files."
fi

# create the password file for the db
if [ ! -f "./db/password.txt" ]; then
    echo "No password file found. Please enter a password for the database:"
    read -s DB_PASSWORD
    echo ""
    mkdir -p ./db
    echo "$DB_PASSWORD" > ./db/password.txt
    chmod 600 ./db/password.txt
    echo "Password file created at ./db/password.txt"
fi

# the tool needs at least an input and output path, so now look if present
if [ "$INPUT_PROVIDED" == "true" ] && [ "$OUTPUT_PROVIDED" == "true" ]; then
    echo "Starting Docker now..."
    docker compose run --build --rm backend
else 
    echo "Please include valid absolute paths to the input and the output folders."
    exit 1
fi