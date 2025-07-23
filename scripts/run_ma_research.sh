#!/bin/bash

# run_ma_research.sh - Run M&A deep research with organized output structure
# Usage: ./run_ma_research.sh [company_name] [options]

set -e  # Exit on error

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_BASE_DIR="${SCRIPT_DIR}/../output/ma_deep_research"
CACHE_DIR="${SCRIPT_DIR}/../cache/ma_deep_research"
API_URL="http://127.0.0.1:2024"
RESEARCH_MODE="balanced"
ANGLES="all"
COMPANY=""
SAMPLE_INDEX=""
FORCE_REFRESH=""
CREATE_INTEGRATION=""

# Function to print colored output
print_color() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if API is running
check_api() {
    # Use Python to check API availability (more reliable than curl)
    if ! python -c "import requests; requests.get('${API_URL}/assistants', timeout=5)" > /dev/null 2>&1; then
        print_color $RED "❌ Error: Deep Research API is not running at ${API_URL}"
        print_color $YELLOW "Please start the API server first:"
        print_color $BLUE "uvx --refresh --from 'langgraph-cli[inmem]' --with-editable . --python 3.11 langgraph dev --allow-blocking"
        exit 1
    fi
    print_color $GREEN "✓ API server is running at ${API_URL}"
}

# Function to show usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Run M&A-focused deep research using the local Open Deep Research API.

OPTIONS:
    -c, --company NAME      Company name to research (use quotes for multi-word names)
    -s, --sample N          Use company N from sample_companies.txt
    -l, --list-samples      List all sample companies
    -a, --angles ANGLES     Research angles (comma-separated or "all")
                           Available: external_risk_summary,risk_landscape_matrix,
                                     watch_factors,red_flag_detection,company_context
    -m, --mode MODE         Research mode: fast, balanced, comprehensive (default: balanced)
    -f, --force-refresh     Ignore cache and re-research
    -i, --integration       Create system_context.md for VDR integration
    -o, --output DIR        Output directory (default: output/ma_deep_research)
    -u, --api-url URL       API URL (default: http://127.0.0.1:2024)
    -h, --help              Show this help message

EXAMPLES:
    # Research Tesla with all angles
    $0 --company "Tesla Inc." --angles all

    # Research sample company #3 with fast mode
    $0 --sample 3 --mode fast

    # Research specific angles for Apple
    $0 --company "Apple Inc." --angles external_risk_summary,red_flag_detection

    # Force refresh and create integration file
    $0 --company "Microsoft" --force-refresh --integration

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--company)
            COMPANY="$2"
            shift 2
            ;;
        -s|--sample)
            SAMPLE_INDEX="$2"
            shift 2
            ;;
        -l|--list-samples)
            echo "Sample companies available:"
            if [ -f "${SCRIPT_DIR}/sample_companies.txt" ]; then
                grep -v "^#" "${SCRIPT_DIR}/sample_companies.txt" | grep -v "^$" | nl -nln -w2 -s". "
            else
                print_color $RED "sample_companies.txt not found!"
            fi
            exit 0
            ;;
        -a|--angles)
            ANGLES="$2"
            shift 2
            ;;
        -m|--mode)
            RESEARCH_MODE="$2"
            shift 2
            ;;
        -f|--force-refresh)
            FORCE_REFRESH="--force-refresh"
            shift
            ;;
        -i|--integration)
            CREATE_INTEGRATION="--create-integration"
            shift
            ;;
        -o|--output)
            OUTPUT_BASE_DIR="$2"
            shift 2
            ;;
        -u|--api-url)
            API_URL="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            print_color $RED "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate inputs
if [ -z "$COMPANY" ] && [ -z "$SAMPLE_INDEX" ]; then
    print_color $RED "Error: Must specify either --company or --sample"
    usage
    exit 1
fi

# Create necessary directories
mkdir -p "$OUTPUT_BASE_DIR"
mkdir -p "$CACHE_DIR"

# Check if API is running
check_api

# Build the Python command
PYTHON_CMD="python ${SCRIPT_DIR}/1-ma_risk_deep_research.py"

if [ -n "$COMPANY" ]; then
    PYTHON_CMD="$PYTHON_CMD --company \"$COMPANY\""
else
    PYTHON_CMD="$PYTHON_CMD --sample $SAMPLE_INDEX"
fi

# Convert comma-separated angles to space-separated for Python argparse
if [ "$ANGLES" != "all" ]; then
    ANGLES_ARGS=$(echo "$ANGLES" | tr ',' ' ')
    PYTHON_CMD="$PYTHON_CMD --angles $ANGLES_ARGS"
else
    PYTHON_CMD="$PYTHON_CMD --angles all"
fi

PYTHON_CMD="$PYTHON_CMD --mode $RESEARCH_MODE"
PYTHON_CMD="$PYTHON_CMD --output-dir \"$OUTPUT_BASE_DIR\""
PYTHON_CMD="$PYTHON_CMD --cache-dir \"$CACHE_DIR\""
PYTHON_CMD="$PYTHON_CMD --api-url $API_URL"

if [ -n "$FORCE_REFRESH" ]; then
    PYTHON_CMD="$PYTHON_CMD $FORCE_REFRESH"
fi

if [ -n "$CREATE_INTEGRATION" ]; then
    PYTHON_CMD="$PYTHON_CMD $CREATE_INTEGRATION"
fi

# Display research configuration
echo ""
print_color $BLUE "========================================"
print_color $BLUE "M&A Deep Research Configuration"
print_color $BLUE "========================================"
if [ -n "$COMPANY" ]; then
    echo "Company: $COMPANY"
else
    echo "Sample: #$SAMPLE_INDEX"
fi
echo "Research Mode: $RESEARCH_MODE"
echo "Angles: $ANGLES"
echo "Output Dir: $OUTPUT_BASE_DIR"
echo "API URL: $API_URL"
[ -n "$FORCE_REFRESH" ] && echo "Force Refresh: Yes"
[ -n "$CREATE_INTEGRATION" ] && echo "Create Integration: Yes"
print_color $BLUE "========================================"
echo ""

# Run the test script first (optional)
if [ "${RUN_TEST:-0}" -eq 1 ]; then
    print_color $YELLOW "Running API test first..."
    python "${SCRIPT_DIR}/test_local_api.py"
    echo ""
fi

# Execute the research
print_color $GREEN "Starting M&A deep research..."
echo ""

# Use eval to properly handle quoted arguments
eval "$PYTHON_CMD"

# Check if output was created
TIMESTAMP=$(date +%Y%m%d)
if [ -n "$COMPANY" ]; then
    COMPANY_SLUG=$(echo "$COMPANY" | tr '[:upper:]' '[:lower:]' | tr ' ' '_' | tr -d '.')
else
    # Get company name from sample file
    COMPANY_LINE=$(sed -n "${SAMPLE_INDEX}p" "${SCRIPT_DIR}/sample_companies.txt" | grep -v "^#")
    COMPANY_SLUG=$(echo "$COMPANY_LINE" | cut -d'(' -f1 | tr '[:upper:]' '[:lower:]' | tr ' ' '_' | tr -d '.')
fi

OUTPUT_DIR="${OUTPUT_BASE_DIR}/${COMPANY_SLUG}"

if [ -d "$OUTPUT_DIR" ]; then
    echo ""
    print_color $GREEN "✓ Research completed successfully!"
    print_color $BLUE "Output files:"
    
    # List recent files (created today)
    find "$OUTPUT_DIR" -name "*${TIMESTAMP}*" -type f | while read -r file; do
        echo "  - $(basename "$file")"
    done
    
    echo ""
    print_color $YELLOW "View results:"
    echo "cd \"$OUTPUT_DIR\""
    
    # Find the most recent summary file
    LATEST_SUMMARY=$(find "$OUTPUT_DIR" -name "ma_research_summary_*.md" -type f | sort -r | head -1)
    if [ -n "$LATEST_SUMMARY" ]; then
        echo "cat \"$(basename "$LATEST_SUMMARY")\""
    fi
else
    print_color $RED "❌ No output directory created. Research may have failed."
fi

echo ""