from django.test import TestCase
from unittest.mock import patch, call
from task_functions.tasks import execute_sequential_tasks, renew_token, fetch_datahub_data_task, filter_objects_task, process_datasets_task, download_and_extract_files_task, handle_task_failure

class ExecuteSequentialTasksTest(TestCase):

    @patch('task_functions.tasks.download_and_extract_files_task.s')
    @patch('task_functions.tasks.process_datasets_task.s')
    @patch('task_functions.tasks.filter_objects_task.s')
    @patch('task_functions.tasks.fetch_datahub_data_task.s')
    @patch('task_functions.tasks.renew_token.s')
    @patch('task_functions.tasks.chain')
    def test_execute_sequential_tasks(self, mock_chain, mock_renew_token, mock_fetch_datahub_data_task, mock_filter_objects_task, mock_process_datasets_task, mock_download_and_extract_files_task):
        arg = 20
        filter_names = [
            "Role Details",
            "Users",
            "Organizational Units",
            "Enrollments and Withdrawals",
        ]

        execute_sequential_tasks(arg)

        mock_renew_token.assert_called_once_with(arg)
        mock_fetch_datahub_data_task.assert_called_once_with()
        mock_filter_objects_task.assert_called_once_with(filter_names, 'Full')
        mock_process_datasets_task.assert_called_once_with('Full')
        mock_download_and_extract_files_task.assert_called_once_with()

        mock_chain.assert_called_once_with(
            mock_renew_token(),
            mock_fetch_datahub_data_task(),
            mock_filter_objects_task(),
            mock_process_datasets_task(),
            mock_download_and_extract_files_task()
        )

        mock_chain().apply_async.assert_called_once_with(link_error=handle_task_failure.s())