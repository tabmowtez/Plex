#!/usr/bin/env python
import logging
import os

from dotenv import load_dotenv
from plexapi.server import PlexServer

# Load environment variables from .env file
load_dotenv()

# Set the logging level based on the environment variable
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=getattr(logging, log_level, logging.INFO))


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
    if logging.getLogger().isEnabledFor(logging.DEBUG):
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
        self.libraries = {}
        self.resolution_counts = {}
        self.total_counts = {}
        self.get_libraries()

    def get_libraries(self):
        """
        Retrieve and categorize all libraries from the Plex server.
        """
        for library in self.plex.library.sections():
            if library.type in ["movie", "show"]:
                self.libraries[library.title] = library
                self.resolution_counts[library.title] = {}
                self.total_counts[library.title] = {
                    'total_items': 0,
                    'total_shows': 0,
                    'total_seasons': 0
                }

    def tally_resolutions(self, library_name, library):
        """
        Tally the resolutions of all items in the given library.

        Args:
            library_name (str): The name of the library.
            library (plexapi.library.LibrarySection): The library section to tally.

        Returns:
            int: The total count of items in the library.
        """
        total_count = 0
        for item in library.all():
            if library.type == "show":
                self.total_counts[library_name]['total_shows'] += 1
                self.total_counts[library_name]['total_seasons'] += len(item.seasons())
                for episode in item.episodes():
                    total_count += 1
                    _update_resolution_counts(episode, self.resolution_counts[library_name], "TV Show", item.title)
            else:
                total_count += 1
                _update_resolution_counts(item, self.resolution_counts[library_name], "Movie")
        self.total_counts[library_name]['total_items'] = total_count
        return total_count

    def print_summary(self):
        """
        Print a right-aligned summary of the resolution counts for all libraries,
        ensuring that Series and Seasons come directly after the Total line in the summary.
        """

        def ctz(num):
            return f"{num:,}"

        def resolution_sort_key(resolution):
            if resolution is None:
                return -1
            if 'k' in resolution.lower():
                return int(resolution.lower().replace('k', '')) * 1000
            try:
                return int(resolution)
            except ValueError:
                return {
                    'sd': 0,
                    'hd': 1,
                    'uhd': 2
                }.get(resolution.lower(), -1)

        def print_library_summary(sum_library_name, sum_labels, sum_counts):
            # Print the library name and resolution summary with aligned labels and counts
            print(f"\n{'Library:':<{max_label_width}} {sum_library_name.rjust(max_count_width)}")
            for label, count in zip(sum_labels, sum_counts):
                print(f"{label:<{max_label_width}} {count.rjust(max_count_width)}")

        for library_name, resolution_counts in self.resolution_counts.items():
            # Create label strings for the resolutions
            labels = ["Total:"]  # Start with "Total:"
            counts = [ctz(self.total_counts[library_name]['total_items'])]  # Start with total item count

            # Add "Series" and "Seasons" right after "Total" if the library is a TV show library
            if self.libraries[library_name].type == "show":
                labels.extend(["Series:", "Seasons:"])
                counts.extend([
                    ctz(self.total_counts[library_name]['total_shows']),
                    ctz(self.total_counts[library_name]['total_seasons'])
                ])

            # Sort resolutions by highest to lowest
            sorted_resolutions = sorted(resolution_counts.keys(), key=resolution_sort_key, reverse=True)

            # Add resolution labels
            resolution_labels = [f"{resolution.upper() + 'P' if resolution and resolution.isdigit() else resolution.upper()
                if resolution else 'None'}:" for resolution in sorted_resolutions]
            labels.extend(resolution_labels)

            # Add resolution counts
            resolution_counts_list = [ctz(resolution_counts[resolution]) for resolution in sorted_resolutions]
            counts.extend(resolution_counts_list)

            # Find the maximum label width
            max_label_width = max(len("Library: "), max(len(label) for label in labels))

            # Find the maximum width for counts (including library name)
            max_count_width = max(len(library_name), max(len(count) for count in counts))

            # Print library summary with aligned labels and counts
            print_library_summary(library_name, labels, counts)


    def run(self):
        """
        Run the resolution tallying and print the summary.
        """
        for library_name, library in self.libraries.items():
            self.tally_resolutions(library_name, library)
        self.print_summary()


if __name__ == "__main__":
    plex_url = os.getenv('PLEX_URL', 'http://localhost:32400')
    plex_token = os.getenv('PLEX_TOKEN', 'default-token')
    plex_library = PlexLibrary(plex_url, plex_token)
    print(f"Retrieving Library data from Plex instance at: {plex_url}")
    plex_library.run()
