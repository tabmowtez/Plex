import unittest
from unittest.mock import patch, MagicMock
from plex import PlexLibrary, _update_resolution_counts


class TestPlexLibrary(unittest.TestCase):

    @patch('plex.PlexServer')
    def setUp(self, mock_plex_server):
        self.mock_plex_server = mock_plex_server.return_value
        self.mock_movie_section = MagicMock()
        self.mock_tv_section = MagicMock()
        self.mock_plex_server.library.section.side_effect = [self.mock_movie_section, self.mock_tv_section]
        self.plex_library = PlexLibrary('http://mockurl', 'mocktoken')

    def test_init(self):
        self.assertEqual(self.plex_library.plex, self.mock_plex_server)
        self.assertEqual(self.plex_library.movie_library, self.mock_movie_section)
        self.assertEqual(self.plex_library.tv_library, self.mock_tv_section)
        self.assertEqual(self.plex_library.movie_resolution_counts, {})
        self.assertEqual(self.plex_library.tv_resolution_counts, {})
        self.assertEqual(self.plex_library.total_movie_count, 0)
        self.assertEqual(self.plex_library.total_tv_count, 0)
        self.assertEqual(self.plex_library.total_tv_shows, 0)
        self.assertEqual(self.plex_library.total_tv_seasons, 0)

    @patch('plex._update_resolution_counts')
    def test_tally_resolutions_movies(self, mock_update_resolution_counts):
        mock_movie = MagicMock()
        self.mock_movie_section.all.return_value = [mock_movie]
        self.plex_library.tally_resolutions(self.mock_movie_section, self.plex_library.movie_resolution_counts, "Movie")
        self.assertEqual(self.plex_library.total_movie_count, 0)
        mock_update_resolution_counts.assert_called_once_with(mock_movie, self.plex_library.movie_resolution_counts, "Movie")

    @patch('plex._update_resolution_counts')
    def test_tally_resolutions_tv_shows(self, mock_update_resolution_counts):
        mock_show = MagicMock()
        mock_season = MagicMock()
        mock_episode = MagicMock()
        mock_show.seasons.return_value = [mock_season]
        mock_show.episodes.return_value = [mock_episode]
        self.mock_tv_section.all.return_value = [mock_show]
        self.plex_library.tally_resolutions(self.mock_tv_section, self.plex_library.tv_resolution_counts, "TV Shows")
        self.assertEqual(self.plex_library.total_tv_shows, 1)
        self.assertEqual(self.plex_library.total_tv_seasons, 1)
        self.assertEqual(self.plex_library.total_tv_count, 0)
        mock_update_resolution_counts.assert_called_once_with(mock_episode, self.plex_library.tv_resolution_counts, "TV Shows", mock_show.title)

    @patch('builtins.print')
    def test_print_summary(self, mock_print):
        self.plex_library.total_movie_count = 999
        self.plex_library.movie_resolution_counts = {'1080': 570, '720': 177, '480': 112, '4k': 127, '576': 13}
        self.plex_library.total_tv_shows = 129
        self.plex_library.total_tv_seasons = 636
        self.plex_library.total_tv_count = 11323
        self.plex_library.tv_resolution_counts = {'720': 2398, '1080': 6089, 'sd': 2435, '576': 2, '480': 275, '4k': 122, None: 2}
        self.plex_library.print_summary()
        self.assertTrue(mock_print.called)

    @patch('plex.PlexLibrary.tally_resolutions')
    @patch('plex.PlexLibrary.print_summary')
    def test_run(self, mock_print_summary, mock_tally_resolutions):
        mock_tally_resolutions.side_effect = [999, 11323]
        self.plex_library.run()
        mock_tally_resolutions.assert_any_call(self.mock_movie_section, self.plex_library.movie_resolution_counts, "Movie")
        mock_tally_resolutions.assert_any_call(self.mock_tv_section, self.plex_library.tv_resolution_counts, "TV Shows")
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
