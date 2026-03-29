import os
import numpy as np
import argparse

from Tamaraw import Anoa, AnoaPad  # your pasted code lives in Tamaraw.py

IN_PATH = 'datasets/CW.npz'
DATASIZE = 800  # must match Tamaraw.py

def cw_trace_to_packets(trace):
    """
    trace: 1D array from CW.npz where each value = direction × timestamp.
    Returns list of [time, size] for Tamaraw-style input.
    """
    packets = []
    for v in trace:
        if v == 0:
            continue
        real_time = abs(v)
        size = DATASIZE if v > 0 else -DATASIZE
        packets.append([real_time, size])
    if not packets:
        packets.append([0.0, DATASIZE])
    # Sort by timestamp (they should already be sorted, but just in case)
    packets.sort(key=lambda x: x[0])
    return packets


def packets_to_cw_sequence(packets, seq_len=10000):
    """
    packets: defended [time, size] list from AnoaPad.
    Returns CW-style 1D array: position i = i-th packet,
    value = direction × timestamp. Zero-padded to seq_len.
    """
    packets = sorted(packets, key=lambda x: x[0])
    seq = np.zeros(seq_len, dtype=np.float64)
    for i, (t, sz) in enumerate(packets):
        if i >= seq_len:
            break
        direction = 1.0 if sz > 0 else -1.0
        seq[i] = direction * t
    return seq


def defend_all_traces(padl=100):
    d = np.load(IN_PATH)
    X = d['X']
    y = d['y']
    N, T = X.shape

    X_def = np.zeros_like(X, dtype=np.float64)

    total_orig = 0
    total_def = 0

    for i in range(N):
        trace = X[i]

        packets = cw_trace_to_packets(trace)
        total_orig += len(packets)

        list2 = []
        params = [""]
        Anoa(packets, list2, params)
        list2 = sorted(list2, key=lambda x: x[0])

        list3 = []
        AnoaPad(list2, list3, padL=padl, method=0)
        total_def += len(list3)

        X_def[i] = packets_to_cw_sequence(list3, seq_len=T)

        if (i + 1) % 1000 == 0:
            print(f'Processed {i+1}/{N} traces')

    bw_overhead = total_def / total_orig - 1.0
    print(f'Average bandwidth overhead: {bw_overhead*100:.2f}%')

    out_path = f'datasets/CW_tamaraw_padl{padl}.npz'
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    np.savez_compressed(out_path, X=X_def, y=y)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--padl', type=int, default=100)
    args = parser.parse_args()
    defend_all_traces(padl=args.padl)
