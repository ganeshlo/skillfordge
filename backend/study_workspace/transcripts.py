import hashlib
import re

from rest_framework.exceptions import ValidationError


TIMESTAMP = re.compile(
    r"(?P<start>\d{1,2}:\d{2}(?::\d{2})?[,.]\d{3})\s*-->\s*"
    r"(?P<end>\d{1,2}:\d{2}(?::\d{2})?[,.]\d{3})"
)


def _seconds(value):
    parts = value.replace(",", ".").split(":")
    if len(parts) == 2:
        minutes, seconds = parts
        return round(int(minutes) * 60 + float(seconds), 3)
    hours, minutes, seconds = parts
    return round(int(hours) * 3600 + int(minutes) * 60 + float(seconds), 3)


def parse_transcript(content, content_format="auto"):
    normalized = content.replace("\r\n", "\n").replace("\r", "\n").strip()
    detected = content_format
    if detected == "auto":
        detected = "vtt" if normalized.startswith("WEBVTT") else "srt" if "-->" in normalized else "plain"
    if detected == "plain":
        return normalized, []

    segments = []
    blocks = re.split(r"\n\s*\n", normalized.removeprefix("WEBVTT").strip())
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        timestamp_index = next((index for index, line in enumerate(lines) if TIMESTAMP.search(line)), None)
        if timestamp_index is None:
            continue
        match = TIMESTAMP.search(lines[timestamp_index])
        text = " ".join(lines[timestamp_index + 1 :]).strip()
        if not text:
            continue
        text = re.sub(r"<[^>]+>", "", text)
        segments.append({"start": _seconds(match.group("start")), "end": _seconds(match.group("end")), "text": text})
    if not segments:
        raise ValidationError({"content": "No valid timestamped captions were found. Use plain text or valid SRT/VTT."})
    return "\n".join(item["text"] for item in segments), segments


def checksum_for(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def transcript_text_for_range(transcript, start_seconds, end_seconds=None):
    if end_seconds is None:
        return transcript.full_text
    if not transcript.segments:
        raise ValidationError({"transcript": "Timestamp-range generation requires an SRT or VTT transcript."})
    matches = [
        item for item in transcript.segments
        if float(item["end"]) > start_seconds and float(item["start"]) < end_seconds
    ]
    if not matches:
        raise ValidationError({"transcript": "The transcript has no captions in this timestamp range."})
    return "\n".join(f'[{item["start"]:.3f}-{item["end"]:.3f}] {item["text"]}' for item in matches)
