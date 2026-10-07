"""Audit sampled complex two-port CSV. Exit 0 means processing, not certification."""
import argparse
import bisect
import cmath
import csv
import json
import math
from pathlib import Path

PARAMETERS = ('S11', 'S21', 'S12', 'S22')
COLUMNS = ['frequency_MHz'] + [f'{s}_{p}' for s in PARAMETERS for p in ('real', 'imag')]


def load_csv(path):
    rows = []
    with Path(path).open(encoding='utf-8-sig', newline='') as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames or set(COLUMNS) - set(reader.fieldnames):
            raise ValueError('All frequency_MHz and complex S11/S21/S12/S22 columns are required.')
        for number, row in enumerate(reader, 2):
            try:
                values = {key: float(row[key]) for key in COLUMNS}
            except (TypeError, ValueError) as exc:
                raise ValueError(f'Invalid numeric data on CSV line {number}.') from exc
            if not all(math.isfinite(value) for value in values.values()):
                raise ValueError(f'Nonfinite data on CSV line {number}.')
            if values['frequency_MHz'] <= 0:
                raise ValueError('Frequencies must be positive.')
            if any(abs(values[k]) > 1e150 for k in COLUMNS[1:]):
                raise ValueError('S parameter magnitude exceeds the supported numerical range.')
            rows.append(values)
    if len(rows) < 3:
        raise ValueError('At least three frequency samples are required.')
    frequencies = [row['frequency_MHz'] for row in rows]
    if any(b <= a for a, b in zip(frequencies, frequencies[1:])):
        raise ValueError('Frequencies must be strictly increasing; duplicates are not allowed.')
    return frequencies, {s: [complex(r[f'{s}_real'], r[f'{s}_imag']) for r in rows] for s in PARAMETERS}


def db(value):
    return 20 * math.log10(max(abs(value), 1e-15))


def interpolate(frequencies, values, frequency):
    if not frequencies[0] <= frequency <= frequencies[-1]:
        raise ValueError('Requested frequency is outside the sampled coverage.')
    index = bisect.bisect_left(frequencies, frequency)
    if index < len(frequencies) and frequencies[index] == frequency:
        return values[index]
    left = index - 1
    fraction = (frequency - frequencies[left]) / (frequencies[index] - frequencies[left])
    return values[left] + fraction * (values[index] - values[left])


def crossing(f0, f1, d0, d1, threshold):
    if d0 == d1:
        raise ValueError('A flat segment cannot define a threshold crossing.')
    return f0 + (f1 - f0) * (threshold - d0) / (d1 - d0)


def local_peak(frequencies, values, center):
    minima = [i for i in range(1, len(values)-1)
              if values[i] <= values[i-1] and values[i] <= values[i+1]
              and (values[i] < values[i-1] or values[i] < values[i+1])]
    left = max((i for i in minima if frequencies[i] < center), default=0)
    right = min((i for i in minima if frequencies[i] > center), default=len(values)-1)
    index = max(range(left, right+1), key=lambda i: values[i])
    return index, [frequencies[left], frequencies[right]]


def band_edges(frequencies, values, center, threshold):
    if interpolate(frequencies, values, center) < threshold:
        return None
    left = bisect.bisect_right(frequencies, center) - 1
    while left >= 0 and values[left] >= threshold:
        left -= 1
    low = None if left < 0 else crossing(frequencies[left], frequencies[left+1], values[left], values[left+1], threshold)
    right = bisect.bisect_left(frequencies, center)
    while right < len(values) and values[right] >= threshold:
        right += 1
    high = None if right == len(values) else crossing(frequencies[right-1], frequencies[right], values[right-1], values[right], threshold)
    return low, high


def interval_stats(frequencies, curves, low, high):
    points = [low] + [f for f in frequencies if low < f < high] + [high]
    sampled = {name: [interpolate(frequencies, curve, f) for f in points] for name, curve in curves.items()}
    return {
        'range_mhz': [low, high], 'evaluated_points': len(points),
        'max_insertion_loss_db': -min(sampled['S21']),
        'min_insertion_loss_db': -max(sampled['S21']),
        's21_ripple_db': max(sampled['S21'])-min(sampled['S21']),
        'min_input_return_loss_db': -max(sampled['S11']),
        'min_output_return_loss_db': -max(sampled['S22']),
        'min_forward_power_estimate': 10**(min(sampled['S21'])/10),
    }


def group_delay(frequencies, values, low, high):
    indices = [i for i, f in enumerate(frequencies) if low <= f <= high]
    if len(indices) < 3 or any(abs(values[i]) <= 1e-15 for i in indices):
        return {'available': False, 'reason': 'Insufficient nonzero in-band phase samples.'}
    phases = [cmath.phase(values[indices[0]])]
    increments = []
    for previous, current in zip(indices, indices[1:]):
        delta = cmath.phase(values[current])-cmath.phase(values[previous])
        delta = math.atan2(math.sin(delta), math.cos(delta))
        increments.append(delta)
        phases.append(phases[-1]+delta)
    axis = [frequencies[i] for i in indices]
    delays = []
    for i in range(len(indices)):
        before, after = max(0, i-1), min(len(indices)-1, i+1)
        delays.append(-1000*(phases[after]-phases[before])/(2*math.pi*(axis[after]-axis[before])))
    return {'available': True, 'samples': len(indices), 'min_ns': min(delays), 'max_ns': max(delays),
            'ripple_ns': max(delays)-min(delays),
            'large_principal_phase_step': any(abs(d) >= math.pi/2 for d in increments),
            'phase_aliasing_not_excluded': True}


def audit(frequencies, parameters, center, reference, drop, target_width=None):
    if not math.isfinite(center) or center <= 0 or not math.isfinite(drop) or drop <= 0:
        raise ValueError('Center frequency and drop must be positive and finite.')
    if reference not in ('absolute', 'peak'):
        raise ValueError('Reference must be absolute or peak.')
    if target_width is not None and (not math.isfinite(target_width) or target_width <= 0):
        raise ValueError('Target bandwidth must be positive and finite.')
    curves = {s: [db(value) for value in parameters[s]] for s in PARAMETERS}
    center_db = interpolate(frequencies, curves['S21'], center)
    peak_index, lobe_bounds = local_peak(frequencies, curves['S21'], center)
    if reference == 'peak' and abs(parameters['S21'][peak_index]) <= 1e-15:
        raise ValueError('No measurable lobe peak exists for a relative bandwidth reference.')
    threshold = -drop if reference == 'absolute' else curves['S21'][peak_index]-drop
    edges = band_edges(frequencies, curves['S21'], center, threshold)
    max_singular = []
    residuals_in, residuals_out = [], []
    reciprocity = []
    for s11, s21, s12, s22 in zip(*(parameters[s] for s in PARAMETERS)):
        a = abs(s11)**2 + abs(s21)**2
        d = abs(s12)**2 + abs(s22)**2
        b = s11.conjugate()*s12 + s21.conjugate()*s22
        # hypot avoids squaring very large matrix norms.
        eigenvalue = .5*(a+d+math.hypot(a-d,2*abs(b)))
        max_singular.append(math.sqrt(max(0, eigenvalue)))
        residuals_in.append(1-a)
        residuals_out.append(1-d)
        reciprocity.append(abs(s21-s12))
    result = {
        'sampled_curve_audit_only': True, 'samples': len(frequencies),
        'frequency_coverage_mhz': [frequencies[0], frequencies[-1]],
        'requested_center_mhz': center, 'reference': reference, 'drop_db': drop,
        'threshold_s21_db': threshold, 'center_s21_db_estimate': center_db,
        'center_is_a_sample': center in frequencies,
        'selected_lobe_peak_mhz': frequencies[peak_index], 'selected_lobe_peak_db': curves['S21'][peak_index],
        'peak_search_bounds_mhz': lobe_bounds,
        'requested_center_above_threshold': edges is not None,
        'max_singular_value': max(max_singular),
        'apparent_gain_above_1e_minus_4': max(max_singular) > 1.0001,
        'unaccounted_input_power_range': [min(residuals_in), max(residuals_in)],
        'unaccounted_output_power_range': [min(residuals_out), max(residuals_out)],
        'max_complex_reciprocity_error': max(reciprocity),
        'power_metrics_require_equal_real_reference_impedances': True,
        'db_zero_magnitude_floor': -300,
        'band': None,
    }
    if edges is not None:
        low, high = edges
        complete = low is not None and high is not None
        result['band'] = {'low_mhz': low, 'high_mhz': high, 'both_edges_bracketed': complete}
        effective_low = frequencies[0] if low is None else low
        effective_high = frequencies[-1] if high is None else high
        result['band']['observed_interval_metrics'] = interval_stats(frequencies, curves, effective_low, effective_high)
        result['band']['group_delay_sample_estimate'] = group_delay(frequencies, parameters['S21'], effective_low, effective_high)
        if complete:
            width, arithmetic, geometric = high-low, .5*(high+low), math.sqrt(low*high)
            result['band'].update(bandwidth_mhz=width, arithmetic_center_mhz=arithmetic, geometric_center_mhz=geometric,
                                  fbw_using_requested_center=width/center, fbw_using_geometric_center=width/geometric)
            if target_width is not None:
                result['band']['bandwidth_deviation_from_target_mhz'] = width-target_width
    if target_width is not None:
        low, high = center-target_width/2, center+target_width/2
        result['target_interval'] = {'range_mhz': [low, high], 'covered': frequencies[0] <= low <= high <= frequencies[-1]}
        if result['target_interval']['covered']:
            result['target_interval'].update(interval_stats(frequencies, curves, low, high))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv', type=Path)
    parser.add_argument('--center-mhz', type=float, required=True)
    parser.add_argument('--reference', choices=('absolute', 'peak'), required=True)
    parser.add_argument('--drop-db', type=float, default=3)
    parser.add_argument('--target-bandwidth-mhz', type=float)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        if args.output and args.output.resolve() == args.csv.resolve():
            raise ValueError('Output must not overwrite input CSV.')
        frequencies, parameters = load_csv(args.csv)
        result = audit(frequencies, parameters, args.center_mhz, args.reference, args.drop_db, args.target_bandwidth_mhz)
        text = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
        if args.output:
            args.output.write_text(text+'\n', encoding='utf-8')
        print(text)
    except (ValueError, OSError, OverflowError) as exc:
        parser.exit(2, f'Error: {exc}\n')


if __name__ == '__main__':
    main()
