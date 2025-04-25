import logging

class Logger:
    def __init__(self, name):
        """
        Initializes a logger for the class with the given name.
        
        Args:
            name (str): The name to be used for the logger. It is typically 
                        the name of the module or class.
        
        This method configures the logger to write log messages to the console
        using a StreamHandler and sets the log level to DEBUG. It ensures that 
        handlers are added only once to prevent duplicate log entries.
        """
        
        # Create a logger with the provided name
        self.logger = logging.getLogger(name)
        
        # Check if the logger already has any handlers to avoid duplicate logs
        if not self.logger.hasHandlers():
            # Create a stream handler to log messages to the console
            handler = logging.StreamHandler()
            
            # Set up a log message format: timestamp, logger name, log level, and message
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)  # Apply the formatter to the handler
            
            # Add the handler to the logger
            self.logger.addHandler(handler)
            
            # Set the log level to DEBUG, so all messages of level DEBUG and above are shown
            self.logger.setLevel(logging.DEBUG)


    def __getattr__(self, attr):
        """
        Delegates attribute access to the internal logger instance.
        
        This method is invoked when an attribute that doesn't exist in the 
        current object is accessed. It forwards the request to the logger 
        instance, allowing access to all logging-related attributes and methods 
        as if they were part of the object.

        Args:
            attr (str): The name of the attribute being accessed.

        Returns:
            The value of the attribute from the internal logger instance.
        """

        # Forward the attribute access to the logger object
        return getattr(self.logger, attr)