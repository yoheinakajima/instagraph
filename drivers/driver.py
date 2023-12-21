from abc import ABC, abstractmethod
from typing import Any


class Driver(ABC):
    @abstractmethod
    def get_graph_data(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Abstract method to get graph data.
        """
        pass

    @abstractmethod
    def get_graph_history(self, skip: int, per_page: int) -> dict[str, Any]:
        """
        Abstract method to get graph history.

        :param skip: The number of items to skip.
        :param per_page: The number of items per page.
        :return: The graph history data.
        """
        pass

    @abstractmethod
    def get_response_data(
        self, response_data: Any
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Abstract method to process response data.

        :param response_data: The response data to process.
        :return: The processed response data.
        """
        pass
