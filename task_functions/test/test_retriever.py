from django.test import TestCase
from unittest.mock import patch, call
from task_functions.tasks import execute_sequential_tasks

class ExecuteSequentialTasksTest(TestCase):

    @patch('task_functions.tasks.renew_token.s')
    @patch('task_functions.tasks.fetch_datahub_data_task.s')
    @patch('task_functions.tasks.filter_objects_task.s')
    @patch('task_functions.tasks.process_datasets_task.s')
    @patch('task_functions.tasks.download_and_extract_files_task.s')
    @patch('task_functions.tasks.chain')
    @patch('django.core.cache.cache.get')
    def test_execute_sequential_tasks(self, mock_cache_get, mock_chain, mock_download, mock_process, mock_filter, mock_fetch, mock_renew):
        # Arrange
        arg = 20
        mock_chain.return_value = mock_chain
        mock_renew.return_value = None
        mock_cache_get.return_value = "access_token"
        mock_fetch.return_value = {'Objects': [{'Full': {'Name': 'Role Details', 'ExtractsLink': 'http://example.com'}}]}
        mock_filter.return_value = [{'Full': {'Name': 'Role Details', 'ExtractsLink': 'http://example.com'}}]
        mock_process.return_value = [{'Name': 'RoleDetails', 'ExtractsLink': 'http://example.com'}]
        mock_download.return_value = None

        # Act
        execute_sequential_tasks(arg)
        
        # Assert
        mock_renew.assert_called_once_with(arg)
        mock_cache_get.assert_called_with('ACCESS_TOKEN')
        mock_fetch.assert_called_once_with("access_token")
        mock_filter.assert_called_once_with(mock_fetch.return_value, ['Role Details', 'Users', 'Organizational Units', 'Enrollments and Withdrawals'], 'Full')
        mock_process.assert_called_once_with(mock_filter.return_value, 'Full')
        mock_download.assert_called_once_with(mock_process.return_value)
        mock_chain.assert_called_once_with(
            mock_renew.return_value,
            mock_fetch.return_value,
            mock_filter.return_value,
            mock_process.return_value,
            mock_download.return_value
        )
        mock_chain().apply_async.assert_called_once_with(link_error=mock_chain().link_error)