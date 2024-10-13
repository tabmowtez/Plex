#!/usr/bin/env python
import os
from dotenv import load_dotenv
from plexapi.server import PlexServer

# Load environment variables from .env file
load_dotenv()

def _update_resolution_counts(item, resolution_counts, item_type, show_title=None):
    """
    Update the resolution counts for a given media item.

    Args:
        item (plexapi.video.Video): The media item to update.
        resolution_counts (dict): Dictionary to store resolution counts.
        item_type (str): Type of the item (e.g., 'Movie', 'TV Show').
        show_title (str, optional): Title of the show if the item is an episode.
    """
    resolution = item.media[0].videoResolution
    resolution_info = f"{item.media[0].width}x{item.media[0].height}"
    if resolution not in resolution_counts:
        resolution_counts[resolution] = 0
    resolution_counts[resolution] += 1
    if show_title:
        print(f"{item_type}: {show_title} - {item.title} ({resolution} - {resolution_info})")
    else:
        print(f"{item_type}: {item.title} ({resolution} - {resolution_info})")


class PlexLibrary:
    def __init__(self, baseurl, token):
        """
        Initialize the PlexLibrary with the given base URL and token.

        Args:
            baseurl (str): The base URL of the Plex server.
            token (str): The authentication token for the Plex server.
        """
        self.plex = PlexServer(baseurl, token)
        self.movie_library = self.plex.library.section('Movies')
        self.tv_library = self.plex.library.section('TV Shows')
        self.movie_resolution_counts = {}
        self.tv_resolution_counts = {}
        self.total_movie_count = 0
        self.total_tv_count = 0
        self.total_tv_shows = 0
        self.total_tv_seasons = 0

    def tally_resolutions(self, library, resolution_counts, item_type):
        """
        Tally the resolutions of all items in the given library section.

        Args:
            library (plexapi.library.LibrarySection): The library section to tally.
            resolution_counts (dict): Dictionary to store resolution counts.
            item_type (str): Type of the items in the library (e.g., 'Movies', 'TV Shows').

        Returns:
            int: The total count of items in the library section.
        """
        total_count = 0
        for item in library.all():
            if item_type == "TV Shows":
                self.total_tv_shows += 1
                self.total_tv_seasons += len(item.seasons())
                for episode in item.episodes():
                    total_count += 1
                    _update_resolution_counts(episode, resolution_counts, item_type, item.title)
            else:
                total_count += 1
                _update_resolution_counts(item, resolution_counts, item_type)
        return total_count

    def print_summary(self):
        """
        Print a right aligned summary of the resolution counts for Movies and TV Shows.
        """
        def ctz(num):
            return f"{num:,}"

        # Create label strings for movies and TV shows
        movie_labels = [f"{resolution.upper() if resolution else 'None'} Movies" for resolution in
                        self.movie_resolution_counts]
        tv_labels = [f"{resolution.upper() if resolution else 'None'} TV Episodes" for resolution in
                     self.tv_resolution_counts]

        # Find the maximum label width across both movies and TV sections
        max_label_width = max(len("Total TV Episodes "), max(len(label) for label in movie_labels + tv_labels))

        # Convert counts to strings with commas and find the maximum width for counts
        movie_counts = list(map(ctz, [self.total_movie_count] + list(self.movie_resolution_counts.values())))
        tv_counts = list(map(ctz, [self.total_tv_shows, self.total_tv_seasons, self.total_tv_count] + list(
            self.tv_resolution_counts.values())))
        max_count_width = max(len(count) for count in movie_counts + tv_counts)

        # Print movie summary with aligned labels and counts
        print(f"\n{'Total Movies:':<{max_label_width}} {movie_counts[0].rjust(max_count_width)}")
        for label, count in zip(movie_labels, movie_counts[1:]):
            print(f"{label:<{max_label_width}} {count.rjust(max_count_width)}")

        # Print TV summary with aligned labels and counts
        print(f"\n{'Total TV Shows:':<{max_label_width}} {tv_counts[0].rjust(max_count_width)}")
        print(f"{'Total TV Seasons:':<{max_label_width}} {tv_counts[1].rjust(max_count_width)}")
        print(f"{'Total TV Episodes:':<{max_label_width}} {tv_counts[2].rjust(max_count_width)}")
        for label, count in zip(tv_labels, tv_counts[3:]):
            print(f"{label:<{max_label_width}} {count.rjust(max_count_width)}")

    def run(self):
        """
        Run the resolution tallying and print the summary.
        """
        self.total_movie_count = self.tally_resolutions(self.movie_library, self.movie_resolution_counts, "Movie")
        self.total_tv_count = self.tally_resolutions(self.tv_library, self.tv_resolution_counts, "TV Shows")
        self.print_summary()


if __name__ == "__main__":
    plex_url = os.getenv('PLEX_URL', 'http://localhost:32400')
    plex_token = os.getenv('PLEX_TOKEN', 'default-token')
    plex_library = PlexLibrary(plex_url, plex_token)
    plex_library.run()
