import time
from typing import Dict, List
from ..agents.parser import ParserAgent
from ..agents.validator import ValidatorAgent
from ..tools.ocr_tool import OCRTool
from ..tools.image_preprocessor import ImagePreprocessor
from ..tools.calendar_tool import GoogleCalendarTool
from ..utils.logger import logger


class SchedulePipeline:
    def __init__(self):
        self.parser = ParserAgent()
        self.validator = ValidatorAgent()
        self.ocr = OCRTool()
        self.preprocessor = ImagePreprocessor()
        self.calendar = GoogleCalendarTool()

    async def process(
        self,
        image_bytes: bytes,
        reminder_minutes: int = 30,
        calendar_id: str = "primary",
    ) -> Dict:
        start_time = time.perf_counter()

        processed_image = self.preprocessor.preprocess(image_bytes)
        ocr_text, ocr_confidence = self.ocr.extract_text(processed_image)

        if not ocr_text:
            return {
                "status": "error",
                "events_created": 0,
                "events": [],
                "duplicates_skipped": 0,
                "ocr_confidence": 0.0,
                "processing_time_ms": int((time.perf_counter() - start_time) * 1000),
            }

        parsed_events = await self.parser.parse_schedule(ocr_text)
        validation = await self.validator.validate(parsed_events)
        events = (
            validation.get("corrected_events", parsed_events)
            if not validation.get("valid", True)
            else parsed_events
        )

        created_events = []
        for event in events:
            event_id = self.calendar.create_event(calendar_id, event, reminder_minutes)
            created_events.append(
                {
                    **event,
                    "calendar_event_id": event_id,
                    "reminder_set": f"{reminder_minutes} minutes before",
                }
            )

        return {
            "status": "success",
            "events_created": len(created_events),
            "events": created_events,
            "duplicates_skipped": 0,
            "ocr_confidence": ocr_confidence,
            "processing_time_ms": int((time.perf_counter() - start_time) * 1000),
        }
