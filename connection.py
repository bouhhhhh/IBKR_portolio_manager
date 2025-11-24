"""
Module for handling Interactive Brokers connection.
"""
from ib_insync import IB
from typing import Optional


class IBConnection:
    """Manages connection to Interactive Brokers."""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 4002, client_id: int = 1):
        """
        Initialize IB connection parameters.
        
        Args:
            host: IB Gateway/TWS host address
            port: Port number (4002 for paper trading, 4001 for live)
            client_id: Unique client ID for this connection
        """
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib: Optional[IB] = None
    
    def connect(self) -> IB:
        """
        Establish connection to Interactive Brokers.
        
        Returns:
            IB: Connected IB instance
        """
        if self.ib is None:
            self.ib = IB()
        
        if not self.ib.isConnected():
            self.ib.connect(self.host, self.port, clientId=self.client_id)
            print(f"Connected to IB at {self.host}:{self.port} with client ID {self.client_id}")
        
        return self.ib
    
    def disconnect(self):
        """Disconnect from Interactive Brokers."""
        if self.ib and self.ib.isConnected():
            self.ib.disconnect()
            print("Disconnected from IB")
    
    def is_connected(self) -> bool:
        """Check if currently connected to IB."""
        return self.ib is not None and self.ib.isConnected()
    
    def get_ib(self) -> IB:
        """
        Get the IB instance, connecting if necessary.
        
        Returns:
            IB: Connected IB instance
        """
        if not self.is_connected():
            return self.connect()
        return self.ib
