from dataclasses import replace
from pathlib import Path
import shutil
import subprocess

import pytest

from can_source import CanFrame, CanReader, SourceConfig
from serial_protocol import UpperFrame, encode_frame
from upper_can_protocol import (
    CAN_IDS, DATA_SIZE, FRAGMENT, PACKET_SIZE, UpperCanDecoder, build_can_snapshot,
)


def sample(sequence=7):
    slot = (123, 4, 5, 600, 700, 100, 200, 1,
            300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 2)
    return UpperFrame(sequence, (2, 35, 2.5, 123456789), (2000., 1000., .25),
                      (5000, 2000, *range(-12, 12)), (9, 8, 1, 0),
                      tuple((1, i, 3, 4, 5, 6, 7, 8, 9, 10) for i in range(12)),
                      (1, 1, 1), tuple((100+i, i % 4, 0) for i in range(12)),
                      tuple((i, 1200+i, -300-i, 2, 3, 4) for i in range(80)),
                      tuple((i+1, 1, 3, 100+i, 200, 300, 400, 500) for i in range(20)),
                      (2, 1, 1, 3), (slot,) * 6)


def fragments(frame):
    packet = encode_frame(frame)
    assert len(packet) == PACKET_SIZE
    return [(CAN_IDS[i % 20], FRAGMENT.pack(b'UC', 1, i, frame.sequence & 65535,
                                          len(packet))
             + packet[i*DATA_SIZE:(i+1)*DATA_SIZE].ljust(DATA_SIZE, b'\0'))
            for i in range((len(packet)+DATA_SIZE-1)//DATA_SIZE)]


def decode(rows, decoder=None):
    decoder = decoder or UpperCanDecoder()
    return [frame for can_id, data in rows if (frame := decoder.feed(can_id, data))]


def test_complete_snapshot_keeps_all_capacity_and_clears_empty_output():
    d = UpperCanDecoder()
    rows = fragments(sample())
    assert decode(rows[:20], d) == []
    assert decode(rows[20:], d) == [sample()]
    empty = replace(sample(8), points=((0,)*6,)*80, lines=((0,)*8,)*20,
                    slot_meta=(2, 0, 0, 3))
    snap = build_can_snapshot(decode(fragments(empty), d)[0])
    assert not any(p.is_valid for p in snap.frame[1])
    assert not any(s.is_valid for s in snap.frame[0])
    assert snap.frame[6] == []


def test_out_of_order_duplicate_and_idle_fragments_are_safe():
    d = UpperCanDecoder()
    rows = fragments(sample())
    assert decode(list(reversed(rows)) + rows, d) == [sample()]
    idle = FRAGMENT.pack(b'UC', 1, 255, 7, PACKET_SIZE) + bytes(56)
    assert d.feed(CAN_IDS[10], idle) is None
    assert d.decode_errors == 0


def test_loss_interleaved_sequences_crc_recovery_and_bounded_state():
    d = UpperCanDecoder()
    a, b = fragments(sample(7)), fragments(sample(8))
    assert decode(a[:12], d) == []
    assert decode(b[:10]+a[13:]+b[10:], d) == [sample(8)]
    corrupt = fragments(sample(9))
    payload = bytearray(corrupt[-1][1])
    payload[15] ^= 0x40
    corrupt[-1] = corrupt[-1][0], bytes(payload)
    assert decode(corrupt, d) == []
    assert d.decode_errors == 1
    assert decode(fragments(sample(10)), d) == [sample(10)]
    for i in range(20, 100):
        decode(fragments(sample(i))[:1], d)
    assert len(d.pending) <= 4 and len(d.completed) <= 4


def test_wrong_id_version_length_and_envelope_are_rejected():
    d = UpperCanDecoder()
    can_id, data = fragments(sample())[0]
    assert d.feed(CAN_IDS[1], data) is None
    assert d.feed(can_id, data[:-1]) is None
    invalid = bytearray(data)
    invalid[2] = 2
    assert d.feed(can_id, bytes(invalid)) is None
    assert d.decode_errors == 3
    assert not d.recognizes(0x6CD, data)
    assert not d.recognizes(can_id, bytes(64))


def test_sequence_wrap_and_reboot_reuse_do_not_replay_old_snapshot():
    d = UpperCanDecoder()
    for seq in (65535, 65536, 65537, 1):
        assert decode(fragments(sample(seq)), d) == [sample(seq)]
    changed = replace(sample(1), status=(2, 35, 3.5, 99))
    assert decode(fragments(changed), d) == [changed]


def test_complete_new_snapshot_cannot_be_overwritten_by_delayed_old_tail():
    d = UpperCanDecoder()
    old = fragments(sample(10))
    assert decode(old[:20], d) == []
    assert decode(fragments(sample(11)), d) == [sample(11)]
    assert decode(old[20:] + old[:20], d) == []


def test_vector_asc_reader_and_scan_publish_complete_new_protocol(tmp_path):
    from can_source import iter_asc, scan_recording
    path = tmp_path/'upper.asc'
    rows = fragments(sample())
    path.write_text('date Tue Nov 17 10:00:00.000 2026\n'
                    'base hex timestamps absolute\n'
                    + '\n'.join(f'{i*.001:.6f} CANFD 1 {cid:X} Rx 1 0 d 15 64 '
                                + data.hex(' ') for i, (cid, data) in enumerate(rows)))
    r = CanReader(config=SourceConfig(), backend='can_replay')
    for frame in iter_asc(path):
        r._consume(frame)
    assert r.refresh_total == 1
    assert r.read_snapshot().timestamp_us == 123456789
    assert r.read_snapshot().sample_timestamp_us > 0
    result = scan_recording(str(path))
    assert result['refreshes'] == 1 and result['decoded'] == 30


def test_uc_fragment_never_goes_through_legacy_dbc_geometry_decoder():
    from can_source import DbcDecoder
    can_id, payload = fragments(sample())[0]
    with pytest.raises(ValueError, match='禁止按旧 DBC'):
        DbcDecoder().decode(can_id, payload)


def test_supplied_s20_upper_recording_reproduces_and_fixes_wrong_display():
    from can_source import DbcDecoder, VisualizationModel, iter_asc
    recording = Path('D:/Cenww_work/SF26195_Geely_KX21/replay/Logs/Origin/S20_upper.asc')
    if not recording.exists():
        pytest.skip('Local field ASC is not available')
    r = CanReader(config=SourceConfig(), backend='can_replay')
    first_header = True
    upper = UpperCanDecoder()
    true_frames = 0
    legacy_wrong_speed = False
    # Bypass only the new DBC guard to reproduce the previous application's bug.
    legacy = DbcDecoder()
    old_model = VisualizationModel()
    for f in iter_asc(recording):
        r._consume(f)
        if upper.recognizes(f.arbitration_id, f.data):
            decoded = upper.feed(f.arbitration_id, f.data)
            if decoded:
                true_frames += 1
                assert decoded.status[2] == 0
                view = build_can_snapshot(decoded)
                assert view.frame[6] == []
                assert all(max(abs(p.x), abs(p.y)) < 4000
                           for p in view.frame[1] if p.is_valid)
            if first_header and f.arbitration_id == 0x640:
                cid = legacy.resolve_canonical(f.arbitration_id, len(f.data))
                msg = legacy._messages[cid]
                signals = msg.decode(f.data[:msg.length], decode_choices=False, scaling=False)
                old_model.feed(cid, signals, f.timestamp)
                legacy_wrong_speed = old_model.frame()[3] > 29
                first_header = False
    assert true_frames > 100 and r.refresh_total == true_frames
    assert upper.decode_errors == r.decode_errors == 0
    assert r._upper_can_active and legacy_wrong_speed
    assert 'UPPER CAN v1' in r.status_text()


def test_bundled_can_dbc_matches_real_fragment_headers():
    import cantools
    path = Path(__file__).resolve().parents[1]/'assets/dbc/S20_Upper_CAN_UC_v1_20261117.dbc'
    db = cantools.database.load_file(str(path))
    assert len(db.messages) == 20
    for cid, payload in fragments(sample()):
        msg = db.get_message_by_frame_id(cid)
        assert msg.is_fd and msg.length == 64
        signals = msg.decode(payload)
        assert (signals['MagicU'], signals['MagicC'], signals['ProtocolVersion']) == (85, 67, 1)
        assert signals['PacketLength'] == PACKET_SIZE
        assert signals['SequenceLow16'] == 7
        assert signals['PayloadByte00'] == payload[8]


def test_supplied_moving_cantest_log_preserves_speed_odometry_and_geometry():
    from can_source import iter_asc
    from map_view import pose_from_odometry
    path = Path('D:/Cenww_work/SF26195_Geely_KX21/replay/Logs/Origin/S20_CANTEST.asc')
    if not path.exists():
        pytest.skip('Local moving field ASC is not available')
    d = UpperCanDecoder()
    speeds, forward, gears = [], [], set()
    for record in iter_asc(path):
        frame = d.feed(record.arbitration_id, record.data)
        if frame is None:
            continue
        snap = build_can_snapshot(frame)
        speeds.append(frame.status[2])
        gears.add(frame.status[0])
        pose = pose_from_odometry(snap.data['odo'], snap.data['odo_convention'])
        forward.append(pose[0])
        assert pose[0] == frame.odo[1] and pose[1] == -frame.odo[0]
        assert snap.frame[3] == frame.status[2]
        assert all(max(abs(p.x), abs(p.y)) < 10000 for p in snap.frame[1] if p.is_valid)
        assert snap.frame[6] == []  # No slot entries actually published by this firmware recording.
    assert d.frames_total > 200 and d.decode_errors == 0
    assert 2 < max(speeds) < 2.2 and len(gears) >= 2
    assert 1900 < max(forward)-min(forward) < 2000


def test_s20_native_units_match_csplus_coordinates_without_1000x_odo_error():
    snap = build_can_snapshot(sample())
    from map_view import pose_from_odometry
    assert pose_from_odometry(snap.data['odo'], snap.data['odo_convention']) == (1000, -2000, .25)
    assert (snap.frame[1][0].x, snap.frame[1][0].y) == (1200, 300)
    assert (snap.frame[0][0].sx, snap.frame[0][0].sy) == (100, -200)
    assert snap.data['vehicle_demo']['probes']['RRS'] == (-11, 12)
    assert snap.frame[3] == 2.5
    assert snap.timestamp_us == 123456789
    assert snap.frame[6][0].pts[1] == (300, 400)  # Same values as CS+ slots.


def test_actual_can_reader_publishes_only_complete_snapshots_and_rejects_bad_crc():
    r = CanReader(config=SourceConfig())
    for i, (can_id, data) in enumerate(fragments(sample())):
        r._consume(CanFrame(i*.001, can_id, data))
        if i < 29:
            assert r.read_snapshot() is None
    snap = r.read_snapshot()
    assert snap.data['array_counts'] == (80, 20)
    assert snap.frame is r.read_latest()
    assert r.refresh_total == 1 and r.pdc_sample is not None
    # Once UC is active, other legacy payloads cannot mutate the completed UI.
    r._consume(CanFrame(1, 0x640, bytes(64)))
    assert r.read_snapshot() is snap


def test_production_c_encoder_python_interoperability_and_frozen_second_batch(tmp_path):
    gcc = shutil.which('gcc')
    if not gcc:
        pytest.skip('Host gcc is required for C/Python protocol interoperability')
    fw = Path(__file__).resolve().parents[1] / 'firmware/upper_can'
    source = r'''
#include "UpperCanTypes.h"
#include <stdio.h>
#include <string.h>
Upper_PointOutSignal sf_Upper_PointOutSignal[80];
Upper_LineOutSignal sf_Upper_LineOutSignal[20];
Upper_StatusOutSignal sf_Upper_StatusOutSignal;
Upper_OdoOutSignal sf_Upper_OdoOutSignal;
Upper_VehicleOutSignal sf_Upper_VehicleOutSignal;
Upper_RawDataOutSignal sf_Upper_RawDataOutSignal;
Upper_PDCOutSignal sf_Upper_PDCOutSignal;
Upper_SlotOutSignal sf_Upper_SlotOutSignal;
int main(int argc,char **argv) {
    unsigned int i,batch; unsigned char out[64]; FILE *f;
    if(argc!=2) return 1;
    f=fopen(argv[1],"wb"); if(!f) return 2;
    sf_Upper_StatusOutSignal.GearLever=2; sf_Upper_StatusOutSignal.Temp=35; sf_Upper_StatusOutSignal.Speed=2.5f;
    sf_Upper_OdoOutSignal.odo_x=2000.f; sf_Upper_OdoOutSignal.odo_y=1000.f; sf_Upper_OdoOutSignal.odo_ang=.25f;
    sf_Upper_VehicleOutSignal.CarLength=5000; sf_Upper_VehicleOutSignal.CarWidth=2000;
    for(i=0;i<80;i++) {
        sf_Upper_PointOutSignal[i].ObjID=(uint16_t)(1000+i);
        sf_Upper_PointOutSignal[i].x=(int16_t)(-32000+(int)i);
        sf_Upper_PointOutSignal[i].y=(int16_t)(32000-(int)i);
        sf_Upper_PointOutSignal[i].cHight=(uint8_t)(i%3);
        sf_Upper_PointOutSignal[i].SNS_Txindex=(uint8_t)(i%12);
        sf_Upper_PointOutSignal[i].SNS_Rxindex=(uint8_t)((i+1)%12);
    }
    sf_Upper_RawDataOutSignal.rawdata_info[11].ce_right_width=65535;
    sf_Upper_LineOutSignal[19].cNum=9; sf_Upper_LineOutSignal[19].cHight=2;
    sf_Upper_LineOutSignal[19].cObjType=3; sf_Upper_LineOutSignal[19].wStartx=-32768;
    sf_Upper_LineOutSignal[19].wStarty=32767; sf_Upper_LineOutSignal[19].wDist=65535;
    sf_Upper_SlotOutSignal.right_slot_num=3;
    sf_Upper_SlotOutSignal.right_slot_info[2].slot_F_y=-1234;
    sf_Upper_SlotOutSignal.right_slot_info[2].timestamp=1234567890123ULL;
    sf_Upper_SlotOutSignal.right_slot_info[2].slot_F_type=3;
    for(batch=0;batch<2;batch++) {
        OutputSignalCan_BeginBatch(123456789ULL);
        for(i=0;i<20;i++) { OutputSignalCan_GetFrame((uint8_t)i,out); if(fwrite(out,64,1,f)!=1) return 3; }
        memset(sf_Upper_PointOutSignal,0,sizeof(sf_Upper_PointOutSignal));
        memset(sf_Upper_LineOutSignal,0,sizeof(sf_Upper_LineOutSignal));
    }
    fclose(f); return 0;
}
'''
    (tmp_path/'main.c').write_text(source)
    exe = tmp_path/'encode.exe'
    subprocess.run([gcc, '-std=c99', '-Wall', '-Wextra', '-Werror',
                    '-I'+str(fw), str(tmp_path/'main.c'), str(fw/'UpperCanDebug.c'),
                    '-o', str(exe)], check=True, capture_output=True)
    out = tmp_path/'frames.bin'
    subprocess.run([str(exe), str(out)], check=True)
    data = out.read_bytes()
    assert len(data) == 40*64
    rows = [(CAN_IDS[i % 20], data[i*64:(i+1)*64]) for i in range(40)]
    frames = decode(rows)
    assert len(frames) == 1
    f = frames[0]
    assert f.status == (2, 35, 2.5, 123456789)
    assert f.odo == (2000., 1000., .25)
    assert f.points[79] == (1079, -31921, 31921, 1, 7, 8)
    assert f.lines[19] == (9, 2, 3, -32768, 32767, 0, 0, 65535)
    assert f.raw[11][-1] == 65535
    assert f.slots[5][0] == 1234567890123 and f.slots[5][-2:] == (-1234, 3)
    assert encode_frame(f) == b''.join(row[1][8:] for row in rows[:30])[:PACKET_SIZE]
