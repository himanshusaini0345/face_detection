import pytest
from unittest.mock import MagicMock, patch


from repository.employee_repository import EmployeeRepository

CONN_STR = "Server=...;Database=EMS_WEB_2023;..."


@pytest.fixture
def mock_pyodbc_connect():
    with patch("pyodbc.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        yield mock_connect, mock_conn, mock_cursor


def test_get_face_photo_path_found(mock_pyodbc_connect):
    _, _, mock_cursor = mock_pyodbc_connect
    mock_cursor.fetchone.return_value = ("uploads/photos/emp_42.jpg",)

    repo = EmployeeRepository(CONN_STR)
    result = repo.get_face_photo_path("42")

    mock_cursor.execute.assert_called_once_with(
        "SELECT FacePhoto FROM emp.employees WHERE Id = ?", ("42",)
    )
    assert result == "uploads/photos/emp_42.jpg"


def test_get_face_photo_path_not_found(mock_pyodbc_connect):
    _, _, mock_cursor = mock_pyodbc_connect
    mock_cursor.fetchone.return_value = None

    repo = EmployeeRepository(CONN_STR)
    result = repo.get_face_photo_path("999")

    assert result is None


def test_connection_is_closed_after_query(mock_pyodbc_connect):
    _, mock_conn, mock_cursor = mock_pyodbc_connect
    mock_cursor.fetchone.return_value = ("some/path.jpg",)

    repo = EmployeeRepository(CONN_STR)
    repo.get_face_photo_path("1")

    mock_conn.close.assert_called_once()


def test_connection_closed_even_on_exception(mock_pyodbc_connect):
    _, mock_conn, mock_cursor = mock_pyodbc_connect
    mock_cursor.execute.side_effect = Exception("DB error")

    repo = EmployeeRepository(CONN_STR)
    with pytest.raises(Exception, match="DB error"):
        repo.get_face_photo_path("1")

    mock_conn.close.assert_called_once()  # finally block must run
