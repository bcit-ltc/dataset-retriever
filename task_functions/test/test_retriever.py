from django.test import TestCase
from unittest.mock import patch, MagicMock
from task_functions.tasks import execute_sequential_tasks

class ExecuteSequentialTasksTest(TestCase):

    @patch('task_functions.tasks.renew_token.s')
    @patch('task_functions.tasks.fetch_datahub_data_task.s')
    @patch('task_functions.tasks.filter_objects_task.s')
    @patch('task_functions.tasks.process_datasets_task.s')
    @patch('task_functions.tasks.download_and_extract_files_task.s')
    @patch('task_functions.tasks.chain')
    def test_execute_sequential_tasks(self, mock_chain, mock_download, mock_process, mock_filter, mock_fetch, mock_renew):
        # Arrange
        arg = 20
        mock_chain.return_value = MagicMock()
        mock_fetch.return_value = MagicMock()
        mock_filter.return_value = MagicMock()
        mock_process.return_value = MagicMock()
        mock_download.return_value = MagicMock()
        
        # Act
        execute_sequential_tasks(arg)
        
        # Assert
        mock_renew.assert_called_once_with(arg)
        mock_fetch.assert_called_once()
        mock_filter.assert_called_once_with(['Role Details', 'Users', 'Organizational Units', 'Enrollments and Withdrawals'], 'Full')
        mock_process.assert_called_once_with(mock_filter.return_value, 'Full')
        mock_download.assert_called_once_with(mock_process.return_value)
        mock_chain.assert_called_once_with(
            mock_renew.return_value,
            mock_fetch.return_value,
            mock_filter.return_value,
            mock_process.return_value,
            mock_download.return_value
        )
        mock_chain().apply_async.assert_called_once_with(link_error=MagicMock())