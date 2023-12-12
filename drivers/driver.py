from abc import ABC, abstractmethod


class Driver(ABC):

    @abstractmethod
    def get_graph_data(self):
        pass

    @abstractmethod
    def get_graph_history(self, skip, per_page):
        pass

    @abstractmethod
    def get_response_data(self, response_data):
        pass
    