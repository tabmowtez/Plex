import unittest
from unittest.mock import patch, MagicMock
from summary import PlexLibrary, _update_resolution_counts


class TestPlexLibrary(unittest.TestCase):

    @patch('summary.PlexServer')
    def setUp(self, mock_plex_server):
        self.mock_plex_server = mock_plex_server.return_value
        self.mock_movie_section = MagicMock()
        self.mock_tv_section = MagicMock()
        self.mock_plex_server.library.sections.return_value = [self.mock_movie_section, self.mock_tv_section]
        self.mock_movie_section.type = "movie"
        self.mock_tv_section.type = "show"
        self.mock_movie_section.title = "Movies"
        self.mock_tv_section.title = "TV Shows"
        self.plex_library = PlexLibrary('http://mockurl', 'mock token')

    def test_init(self):
        self.assertEqual(self.plex_library.plex, self.mock_plex_server)
        self.assertIn("Movies", self.plex_library.libraries)
        self.assertIn("TV Shows", self.plex_library.libraries)
        self.assertEqual(self.plex_library.resolution_counts["Movies"], {})
        self.assertEqual(self.plex_library.resolution_counts["TV Shows"], {})
        self.assertEqual(self.plex_library.total_counts["Movies"], {'total_items': 0, 'total_shows': 0, 'total_seasons': 0})
        self.assertEqual(self.plex_library.total_counts["TV Shows"], {'total_items': 0, 'total_shows': 0, 'total_seasons': 0})

    @patch('summary._update_resolution_counts')
    def test_tally_resolutions_movies(self, mock_update_resolution_counts):
        mock_movie = MagicMock()
        self.mock_movie_section.all.return_value = [mock_movie]
        self.plex_library.tally_resolutions("Movies", self.mock_movie_section)
        self.assertEqual(self.plex_library.total_counts["Movies"]['total_items'], 1)
        mock_update_resolution_counts.assert_called_once_with(mock_movie, self.plex_library.resolution_counts["Movies"], "Movie")

    @patch('summary._update_resolution_counts')
    def test_tally_resolutions_tv_shows(self, mock_update_resolution_counts):
        mock_show = MagicMock()
        mock_season = MagicMock()
        mock_episode = MagicMock()
        mock_show.seasons.return_value = [mock_season]
        mock_show.episodes.return_value = [mock_episode]
        self.mock_tv_section.all.return_value = [mock_show]
        self.plex_library.tally_resolutions("TV Shows", self.mock_tv_section)
        self.assertEqual(self.plex_library.total_counts["TV Shows"]['total_shows'], 1)
        self.assertEqual(self.plex_library.total_counts["TV Shows"]['total_seasons'], 1)
        self.assertEqual(self.plex_library.total_counts["TV Shows"]['total_items'], 1)
        mock_update_resolution_counts.assert_called_once_with(mock_episode, self.plex_library.resolution_counts["TV Shows"], "TV Show", mock_show.title)

    @patch('builtins.print')
    def test_print_summary(self, mock_print):
        self.plex_library.total_counts = {
            "Movies": {'total_items': 999, 'total_shows': 0, 'total_seasons': 0},
            "TV Shows": {'total_items': 11323, 'total_shows': 129, 'total_seasons': 636}
        }
        self.plex_library.resolution_counts = {
            "Movies": {'1080': 570, '720': 177, '480': 112, '4k': 127, '576': 13},
            "TV Shows": {'720': 2398, '1080': 6089, 'sd': 2435, '576': 2, '480': 275, '4k': 122, None: 2}
        }
        self.plex_library.print_summary()
        self.assertTrue(mock_print.called)

    @patch('summary.PlexLibrary.tally_resolutions')
    @patch('summary.PlexLibrary.print_summary')
    def test_run(self, mock_print_summary, mock_tally_resolutions):
        self.plex_library.run()
        mock_tally_resolutions.assert_any_call("Movies", self.mock_movie_section)
        mock_tally_resolutions.assert_any_call("TV Shows", self.mock_tv_section)
        mock_print_summary.assert_called_once()

    def test_update_resolution_counts_with_movie(self):
        item = MagicMock()
        item.media = [MagicMock()]
        item.media[0].videoResolution = '1080'
        item.media[0].width = 1920
        item.media[0].height = 1080
        resolution_counts = {}
        _update_resolution_counts(item, resolution_counts, 'Movie')
        self.assertEqual(resolution_counts['1080'], 1)

    def test_update_resolution_counts_with_tv_show(self):
        item = MagicMock()
        item.media = [MagicMock()]
        item.media[0].videoResolution = '720'
        item.media[0].width = 1280
        item.media[0].height = 720
        resolution_counts = {}
        _update_resolution_counts(item, resolution_counts, 'TV Show', 'Example Show')
        self.assertEqual(resolution_counts['720'], 1)

    def test_update_resolution_counts_with_none_resolution(self):
        item = MagicMock()
        item.media = [MagicMock()]
        item.media[0].videoResolution = None
        item.media[0].width = 640
        item.media[0].height = 480
        resolution_counts = {}
        _update_resolution_counts(item, resolution_counts, 'Movie')
        self.assertEqual(resolution_counts[None], 1)

    def test_update_resolution_counts_with_existing_resolution(self):
        item = MagicMock()
        item.media = [MagicMock()]
        item.media[0].videoResolution = '1080'
        item.media[0].width = 1920
        item.media[0].height = 1080
        resolution_counts = {'1080': 1}
        _update_resolution_counts(item, resolution_counts, 'Movie')
        self.assertEqual(resolution_counts['1080'], 2)

if __name__ == '__main__':
    unittest.main()
