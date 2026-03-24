from abc import ABC, abstractmethod
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential


class BaseExtractor(ABC):
    source_name: str = "base"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def extract(self, **kwargs) -> list[dict]:
        logger.info(f"[{self.source_name}] Starting extraction")
        try:
            data = self._fetch(**kwargs)
            logger.info(f"[{self.source_name}] Extracted {len(data)} records")
            return data
        except Exception as e:
            logger.error(f"[{self.source_name}] Failed: {e}")
            raise

    @abstractmethod
    def _fetch(self, **kwargs) -> list[dict]:
        pass