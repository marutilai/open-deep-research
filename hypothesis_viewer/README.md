# M&A Hypothesis Research Viewer

Executive-level visualization dashboard for viewing AI-generated hypotheses from deep research.

## Running the App

From the project root directory:

```bash
# Make sure you're in the virtual environment
source .venv/bin/activate  # or however you activate your environment

# Run the streamlit app
streamlit run hypothesis_viewer/app.py
```

The app will open in your browser at `http://localhost:8501`

## Features

- **Company Selection**: Dropdown to select from companies with hypothesis data
- **Section Tabs**: View hypotheses organized by research sections
- **Executive Presentation**: Clean, professional styling suitable for senior executives
- **Hypothesis Cards**: Each hypothesis shows:
  - Title and detailed statement
  - Rationale for M&A relevance
  - Impact level (High/Medium/Low)
  - Priority ranking (1-5)
  - Testable research questions
- **Statistics Dashboard**: Overview of total hypotheses and section breakdown

## Data Source

The app reads hypothesis data from: `output/hypothesis_research/`

Make sure you've run the hypothesis generation scripts before using the viewer.