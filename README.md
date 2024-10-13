# Plex Scripts

This project is a collection of Python scripts that connects to a Plex server. 

## Plex Library Resolution Summary
Tallies the resolutions of Movies and TV Shows in your library, and prints a summary.

### Features

- Connects to a Plex server using the `plexapi` library.
- Tallies the resolutions of Movies and TV Shows.
- Prints a summary of the resolution counts.

### Requirements

- Python 3.x
- `plexapi` library
- `python-dotenv` library

### Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/tabmowtez/Plex.git
    cd Plex
    ```

2. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

3. Create a `.env` file in the root directory of the project (or use environment variables) and add your Plex server URL and token:
    ```env
    PLEX_URL=http://your-plex-server:32400
    PLEX_TOKEN=your-plex-token
    ```

### Usage

Run the script:
```sh
python summary.py
