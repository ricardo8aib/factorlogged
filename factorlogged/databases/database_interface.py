from abc import ABC, abstractmethod

class DatabaseGateway(ABC):
    """
    Database interface for the factorlogged.
    """

    @abstractmethod
    def setup(self):
        """
        Setup database
        """
        pass
