from faster_whisper import WhisperModel

model = WhisperModel("distil-large-v3")

segments, info = model.transcribe("/Volumes/HezeSamsung/codes/tryaud.mp3", language="en", condition_on_previous_text=False)
for segment in segments:
    print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
