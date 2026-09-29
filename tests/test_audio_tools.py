from pathlib import Path
import subprocess
from app.core.audio_tools import (
    ffmpeg_exe, audio_duration_seconds, merge_audio,
    ensure_split_audio, split_output_dir,
)
from app.providers.gemini import ascii_upload_alias


def make_tone(path: Path, seconds=1):
    subprocess.run([
        ffmpeg_exe(), '-y', '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=16000',
        '-t', str(seconds), '-c:a', 'pcm_s16le', str(path)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def test_ffmpeg_duration_and_merge(tmp_path):
    a = tmp_path / 'a.wav'; b = tmp_path / 'b.wav'; out = tmp_path / 'merged.m4a'
    make_tone(a, 1); make_tone(b, 1)
    assert 0.7 <= audio_duration_seconds(str(a)) <= 1.3
    merge_audio([str(a), str(b)], str(out))
    assert out.exists() and out.stat().st_size > 100
    assert audio_duration_seconds(str(out)) >= 1.5


def test_unicode_filename_split_and_reuse(tmp_path):
    src = tmp_path / '20260917_(四)_效率評估與生產管理 林泰宇.wav'
    make_tone(src, 3)
    out_dir = split_output_dir(str(tmp_path / 'out'), str(src), 1)
    chunks = ensure_split_audio(str(src), out_dir, 1)
    assert chunks and all(Path(x).exists() for x in chunks)
    mtimes = [Path(x).stat().st_mtime_ns for x in chunks]
    chunks2 = ensure_split_audio(str(src), out_dir, 1)
    assert chunks2 == chunks
    assert [Path(x).stat().st_mtime_ns for x in chunks2] == mtimes


def test_gemini_ascii_upload_alias_for_unicode_filename(tmp_path):
    src = tmp_path / '20260917_(四)_效率評估.m4a'
    src.write_bytes(b'abc123')
    with ascii_upload_alias(str(src)) as alias:
        p = Path(alias)
        # This is the critical condition for multipart filename headers.
        p.name.encode('ascii')
        assert p.read_bytes() == b'abc123'
        assert p != src
    assert not p.exists()


def test_gemini_provider_uses_ascii_alias_without_network(tmp_path):
    from types import SimpleNamespace
    from app.providers.gemini import GeminiProvider

    src = tmp_path / '20260917_(四)_效率評估與生產管理.m4a'
    src.write_bytes(b'fake-audio')

    class FakeFiles:
        def upload(self, file):
            Path(file).name.encode('ascii')
            assert Path(file).read_bytes() == b'fake-audio'
            return SimpleNamespace(uri='files/fake', mime_type='audio/mp4', name='files/fake')
        def delete(self, name):
            assert name == 'files/fake'

    class FakeInteractions:
        def create(self, **kwargs):
            return SimpleNamespace(output_text='測試成功', steps=[])

    provider = GeminiProvider.__new__(GeminiProvider)
    provider.client = SimpleNamespace(files=FakeFiles(), interactions=FakeInteractions())
    provider.model = GeminiProvider.TRANSCRIBE_MODEL
    result = provider.transcribe(str(src), diarization=False, timestamps=False)
    assert result.text == '測試成功'
