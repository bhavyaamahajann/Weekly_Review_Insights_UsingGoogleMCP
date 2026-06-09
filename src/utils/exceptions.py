class PipelineAbortError(Exception):
    """Custom exception raised when the pipeline must abort due to a critical error or data quality issue."""
    def __init__(self, error_code: str, message: str):
        self.error_code = error_code
        self.message = message
        super().__init__(f"[{error_code}] {message}")
