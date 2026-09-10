import threading

import cv2
import numpy as np
import pytest


def make_flash_video(path):
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*'MJPG'), 24, (96, 64))
    assert writer.isOpened()
    for index in range(48):
        writer.write(np.full((64, 96, 3), 255 if index == 5 else 0, np.uint8))
    writer.release()


def test_temporal_scan_captures_single_frame_effect_between_regular_samples(tmp_path):
    from app.media import scan_motion
    path = tmp_path / 'flash.avi'
    make_flash_video(path)
    result = scan_motion(path, threading.Event())
    assert result['decoded_frames'] == 48
    assert {5, 6}.issubset(result['visual_jump_frames'])
    assert {4, 5, 6, 7}.issubset(result['sample_frames'])
    assert result['sample_frames'] == sorted(set(result['sample_frames']))
    assert all(0 <= n < 48 for n in result['sample_frames'])


def test_temporal_scan_cancellation(tmp_path):
    from app.media import scan_motion
    from app.process import Cancelled
    path = tmp_path / 'flash.avi'
    make_flash_video(path)
    cancel = threading.Event()
    cancel.set()
    with pytest.raises(Cancelled):
        scan_motion(path, cancel)


def test_detailed_sampling_keeps_flash_neighbors_and_bounds(tmp_path):
    from app.media import scan_motion
    path=tmp_path/'detail.avi'
    make_flash_video(path)
    result=scan_motion(path,threading.Event(),budget=384)
    assert result['budget']==384
    assert {4,5,6,7}.issubset(result['sample_frames'])
    assert len(result['sample_frames'])<=min(384,result['decoded_frames'])
    with pytest.raises(ValueError):scan_motion(path,threading.Event(),budget=1000)


def test_review_preserves_observed_flash_even_when_plan_missed_it():
    from app.media import review_timestamps
    from app.models import Plan, Track
    plan = Plan(tracks=[Track(id='static', kind='rect', start=0, end=2)])
    times = review_timestamps({'duration': 2, 'fps': 24}, plan,
                             temporal={'visual_jump_frames': [5, 6]})
    assert {4/24, 5/24, 6/24, 7/24}.issubset(times)
