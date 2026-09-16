from app.services.lipsync import build_track, oculus_for_phone, phones_for_text, phones_from_ipa, pose_for_phone


def test_cat_track_uses_oculus_visemes() -> None:
    phones = phones_for_text("cat")
    assert phones == ["k", "æ", "t"]
    track = build_track(phones, focus=["æ"])
    spoken = [frame.phoneme for frame in track.frames if frame.phoneme]
    assert spoken == ["k", "æ", "t"]
    visemes = [frame.viseme for frame in track.frames if frame.phoneme]
    assert visemes == ["kk", "aa", "DD"]
    focus = next(frame for frame in track.frames if frame.phoneme == "æ")
    assert focus.focus
    assert focus.pose.open > 0.7
    assert focus.pose.tongue_front > 0.6


def test_think_maps_to_th_viseme() -> None:
    assert oculus_for_phone("θ") == "TH"
    assert oculus_for_phone("ð") == "TH"
    assert oculus_for_phone("v") == "FF"
    assert oculus_for_phone("ʃ") == "CH"


def test_ipa_tongue_overrides_shared_viseme() -> None:
    ae = pose_for_phone("æ")
    ah = pose_for_phone("ɑ")
    assert ae.tongue_front > ah.tongue_front
    assert pose_for_phone("θ").tongue_tip > 0.8
    assert pose_for_phone("k").tongue_high > 0.9


def test_build_track_scales_to_audio_duration() -> None:
    track = build_track(["k", "æ", "t"], duration_ms=1000)
    assert track.duration_ms == 1000
    spoken = [frame for frame in track.frames if frame.phoneme]
    assert spoken[0].start_ms < spoken[1].start_ms < spoken[2].start_ms


def test_phones_from_ipa_and_unknown_lesson_text() -> None:
    assert phones_from_ipa("/ðə kæt/") == ["ð", "ə", "k", "æ", "t"]
    assert phones_from_ipa("/laɪt/") == ["l", "aɪ", "t"]
    assert phones_for_text("hat", "/hæt/") == ["h", "æ", "t"]
    assert phones_for_text("fat") == ["f", "æ", "t"]
