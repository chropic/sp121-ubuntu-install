#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Read-only, allowlisted SP12 telemetry. Only the explicit output directory is written."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import time

SCHEMA = 1
FIELDS = ['timestamp_utc', 'elapsed_s', 'battery', 'status', 'external_power',
          'energy_wh', 'energy_full_wh', 'power_w', 'estimated_power_w', 'telemetry_json', 'errors']


def read(root, path):
    try:
        return {'status': 'ok', 'value': (root / path.lstrip('/')).read_text().strip()}
    except OSError as error:
        return {'status': 'unavailable', 'errno': error.errno}


def number(root, path, scale=1):
    result = read(root, path)
    try:
        value = float(result['value']) / scale
        return value if math.isfinite(value) else None
    except (KeyError, ValueError):
        return None


def digest(path):
    try:
        h = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                h.update(block)
        return {'status': 'ok', 'sha256': h.hexdigest()}
    except OSError as error:
        return {'status': 'unavailable', 'errno': error.errno}


def groups(root, pattern, attributes):
    # Device paths can contain identifiers. Export ordinal labels only.
    devices = sorted(root.glob(pattern))
    return {'status': 'ok' if devices else 'missing', 'devices': [
        {key: read(root, str((device / key).relative_to(root))) for key in attributes}
        for device in devices]}


def command(argv):
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=10, check=False)
        return {'status': 'ok' if result.returncode == 0 else 'failed',
                'value': result.stdout.strip()}
    except (OSError, subprocess.TimeoutExpired):
        return {'status': 'unavailable'}


def inventory(root):
    result = {'schema': SCHEMA, 'recorded_utc': now(), 'architecture': platform.machine(),
              'running_kernel': platform.release(), 'privacy': 'allowlisted; review before publication',
              'interfaces': {}}
    specs = {
        'cpufreq': ('sys/devices/system/cpu/cpufreq/policy*', ['scaling_driver', 'scaling_governor',
                    'scaling_available_governors', 'scaling_min_freq', 'scaling_max_freq', 'scaling_cur_freq']),
        'cpuidle': ('sys/devices/system/cpu/cpu[0-9]*/cpuidle/state*', ['name', 'usage', 'time', 'disable']),
        'thermal': ('sys/class/thermal/thermal_zone*', ['type', 'temp', 'policy']),
        'gpu': ('sys/class/devfreq/*', ['governor', 'min_freq', 'max_freq', 'cur_freq', 'available_frequencies']),
        'runtime_pm': ('sys/bus/*/devices/*/power', ['control', 'runtime_status', 'runtime_active_time', 'runtime_suspended_time']),
        'battery': ('sys/class/power_supply/*', ['type', 'scope', 'present', 'status', 'energy_now', 'energy_full', 'charge_now', 'voltage_now', 'current_now', 'power_now', 'online']),
        'usb': ('sys/bus/usb/devices/*/power', ['control', 'autosuspend', 'autosuspend_delay_ms']),
        'backlight': ('sys/class/backlight/*', ['brightness', 'max_brightness']),
        'firmware': ('sys/class/dmi/id', ['bios_version', 'bios_date']),
    }
    for name, (pattern, attributes) in specs.items():
        result['interfaces'][name] = groups(root, pattern, attributes)
    for path in ['sys/kernel/mm/lru_gen/enabled', 'sys/kernel/sched_ext/state',
                 'sys/kernel/sched_ext/root/ops', 'sys/module/pcie_aspm/parameters/policy',
                 'sys/devices/system/cpu/cpufreq/boost', 'sys/power/mem_sleep',
                 'sys/module/usbcore/parameters/autosuspend', 'proc/pressure/cpu',
                 'proc/pressure/memory', 'proc/pressure/io']:
        result['interfaces'][path] = read(root, path)
    swaps = read(root, 'proc/swaps')
    if swaps['status'] == 'ok':
        swaps['value'] = [line.split()[1:] for line in swaps['value'].splitlines()[1:]]
    result['swap_without_paths'] = swaps
    files = ['etc/systemd/system/sp12-power-tune.service', 'etc/udev/rules.d/80-sp12-power.rules',
             'usr/local/sbin/sp12-power-tune', 'usr/local/sbin/sp12-sync-boot',
             'etc/sp12-linux/boot.conf', 'etc/kernel/postinst.d/zzzz-sp12-sync',
             'etc/initramfs/post-update.d/zzzz-sp12-sync']
    result['policy_and_boot_hashes'] = {p: digest(root / p) for p in files}
    # No firmware contents, command lines, environment, journal, DMI serials or network data.
    result['boot_artifacts'] = {p.name: digest(p) for p in sorted((root / 'boot').glob('*'))
                                if p.is_file() and p.name.startswith(('vmlinuz-', 'initrd.img-', 'config-', 'dtb-'))}
    result['module_tree_present'] = (root / 'lib/modules' / platform.release()).is_dir()
    config = read(root, 'boot/config-' + platform.release())
    if config['status'] == 'ok':
        prefixes = ('CONFIG_HZ', 'CONFIG_NO_HZ', 'CONFIG_PREEMPT', 'CONFIG_BPF',
                    'CONFIG_DEBUG_INFO_BTF', 'CONFIG_SCHED_CLASS_EXT', 'CONFIG_LRU_GEN',
                    'CONFIG_ZRAM', 'CONFIG_LOCALVERSION')
        config['value'] = [line for line in config['value'].splitlines()
                           if line.removeprefix('# ').startswith(prefixes)]
    result['kernel_options'] = config
    result['zram'] = groups(root, 'sys/block/zram*', ['disksize', 'comp_algorithm', 'mm_stat'])
    if root == Path('/'):
        result['packages'] = command(['dpkg-query', '-W', '-f=${binary:Package}\t${Version}\n',
                                      'linux-image-*', 'linux-firmware*', 'libgl1-mesa-dri',
                                      'mesa-vulkan-drivers', 'power-profiles-daemon'])
        for unit in ['sp12-power-tune.service', 'power-profiles-daemon.service']:
            result[unit] = command(['systemctl', 'show', unit, '--property=ActiveState,UnitFileState,FragmentPath'])
        result['power_profile'] = command(['powerprofilesctl', 'get'])
    return result


def batteries(root):
    found = []
    for p in sorted(root.glob('sys/class/power_supply/*')):
        rel = str(p.relative_to(root))
        if read(root, rel + '/type').get('value') != 'Battery':
            continue
        if read(root, rel + '/present').get('value') == '0':
            continue
        if read(root, rel + '/scope').get('value') == 'Device':
            continue
        # Reject empty/disconnected HID batteries, prefer system batteries.
        if any((number(root, rel + '/' + key) or 0) > 0
               for key in ['energy_full', 'energy_now', 'charge_full', 'charge_now']):
            found.append(p)
    return found


def select_battery(root, requested=None):
    available = batteries(root)
    if requested:
        available = [p for p in available if p.name == requested]
    system = [p for p in available if read(root, str(p.relative_to(root)) + '/scope').get('value') == 'System']
    available = system or available
    if len(available) != 1:
        raise ValueError('No unambiguous system battery; use --battery with an eligible supply name')
    return available[0]


def snapshot(root, battery, elapsed):
    rel = str(battery.relative_to(root))
    row = dict.fromkeys(FIELDS, None)
    row.update(timestamp_utc=now(), elapsed_s=round(elapsed, 6), battery='system-battery',
               status=read(root, rel + '/status').get('value', 'Unknown'))
    online = []
    for p in sorted(root.glob('sys/class/power_supply/*')):
        base = str(p.relative_to(root))
        if read(root, base + '/type').get('value') != 'Battery' and (p / 'online').exists():
            online.append(number(root, base + '/online'))
    row['external_power'] = 'unknown' if not online or None in online else str(int(any(online)))
    for field, key in [('energy_wh', 'energy_now'), ('energy_full_wh', 'energy_full'), ('power_w', 'power_now')]:
        row[field] = number(root, rel + '/' + key, 1_000_000)
    current = number(root, rel + '/current_now', 1_000_000)
    voltage = number(root, rel + '/voltage_now', 1_000_000)
    if current is not None and voltage is not None:
        row['estimated_power_w'] = abs(current * voltage)
    missing = [key for key in ['energy_wh', 'energy_full_wh', 'power_w'] if row[key] is None]
    if row['status'] == 'Unknown':
        missing.append('status')
    if row['external_power'] == 'unknown':
        missing.append('external_power')
    row['errors'] = ','.join(missing)
    row['telemetry_json'] = json.dumps({
        'cpu_khz': groups(root, 'sys/devices/system/cpu/cpufreq/policy*', ['scaling_cur_freq']),
        'thermal_millicelsius': groups(root, 'sys/class/thermal/thermal_zone*', ['temp']),
        'gpu_hz': groups(root, 'sys/class/devfreq/*', ['cur_freq']),
        'cpuidle': groups(root, 'sys/devices/system/cpu/cpu[0-9]*/cpuidle/state*', ['usage', 'time']),
        'pressure': {key: read(root, 'proc/pressure/' + key) for key in ['cpu', 'memory', 'io']},
    }, separators=(',', ':'))
    return row


def now():
    return datetime.now(timezone.utc).isoformat()


def elapsed_clock():
    # Include suspend time so a suspend interval is recognized as a sampling gap.
    return time.clock_gettime(time.CLOCK_BOOTTIME) if hasattr(time, 'CLOCK_BOOTTIME') else time.monotonic()


def new_output(path):
    path.mkdir(mode=0o700, parents=True, exist_ok=False)


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')


def sample(args):
    battery = select_battery(args.root, args.battery)
    conditions = json.loads(args.conditions.read_text())
    if not isinstance(conditions, dict) or not conditions:
        raise ValueError('Conditions must be a nonempty JSON object')
    new_output(args.output)
    metadata = {'schema': SCHEMA, 'kind': 'sample', 'workload': args.workload,
                'conditions': conditions, 'interval_s': args.interval, 'duration_s': args.duration,
                'max_power_w': args.max_power, 'complete': False,
                'units': {'energy': 'Wh', 'power': 'W', 'elapsed': 's'},
                'recovery': 'No settings changed by collector; restore candidate settings using its reviewed rollback record.',
                'disposition': 'unreviewed-private', 'inventory': inventory(args.root)}
    write_json(args.output / 'metadata.json', metadata)
    start = elapsed_clock()
    with (args.output / 'samples.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, FIELDS)
        writer.writeheader()
        while True:
            elapsed = elapsed_clock() - start
            writer.writerow(snapshot(args.root, battery, elapsed))
            stream.flush()
            if elapsed >= args.duration:
                break
            time.sleep(min(args.interval, args.duration - elapsed))
    metadata['complete'] = True
    write_json(args.output / 'metadata.json', metadata)


def evaluate(metadata, rows):
    issues = []
    if metadata.get('schema') != SCHEMA or metadata.get('kind') != 'sample' or not metadata.get('complete'):
        issues.append('unsupported schema or incomplete capture')
    if len(rows) < 2:
        return {'valid': False, 'issues': issues + ['fewer than two samples']}
    try:
        interval = float(metadata['interval_s'])
        duration = float(metadata['duration_s'])
        limit = float(metadata['max_power_w'])
        if not all(math.isfinite(x) and x > 0 for x in [interval, duration, limit]):
            raise ValueError()
        times = [float(r['elapsed_s']) for r in rows]
        energy = [float(r['energy_wh']) for r in rows]
        full = [float(r['energy_full_wh']) for r in rows]
        if not all(math.isfinite(x) for x in times + energy + full):
            raise ValueError()
        if any(r['status'] != 'Discharging' or r['external_power'] != '0' for r in rows):
            issues.append('charging, non-discharging or unknown external power state')
        if len({r['battery'] for r in rows}) != 1:
            issues.append('battery changed')
        if any(e < 0 or f <= 0 or e > f for e, f in zip(energy, full)):
            issues.append('battery values outside valid range')
        if max(full) - min(full) > min(full) * .01:
            issues.append('full-energy gauge changed by more than 1%')
        if times[0] > interval * .5 or times[-1] < duration - interval * .5:
            issues.append('capture does not cover requested duration')
        for i in range(1, len(rows)):
            dt = times[i] - times[i-1]
            de = energy[i-1] - energy[i]
            if dt <= 0 or dt > interval * 1.5:
                issues.append('missing, delayed or unordered samples')
            if de < 0 or (dt > 0 and de * 3600 / dt > limit):
                issues.append('energy counter reset or discontinuity')
        elapsed = times[-1] - times[0]
        used = energy[0] - energy[-1]
        if used <= 0 or elapsed <= 0:
            issues.append('no measurable energy delta')
        return {'valid': not issues, 'issues': sorted(set(issues)), 'energy_wh': used,
                'elapsed_s': elapsed, 'average_w': used * 3600 / elapsed if elapsed > 0 else None}
    except (KeyError, TypeError, ValueError):
        return {'valid': False, 'issues': issues + ['missing or invalid energy telemetry/metadata']}


def load_run(path):
    metadata = json.loads((path / 'metadata.json').read_text())
    with (path / 'samples.csv').open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    return metadata, evaluate(metadata, rows)


def compare(args):
    baseline, b = load_run(args.baseline)
    candidate, c = load_run(args.candidate)
    issues = []
    for field in ['workload', 'conditions']:
        if not baseline.get(field) or baseline.get(field) != candidate.get(field):
            issues.append('mismatched or absent ' + field)
    valid = b['valid'] and c['valid'] and not issues
    result = {'schema': SCHEMA, 'valid': valid, 'baseline': b, 'candidate': c,
              'workload': baseline.get('workload'), 'conditions': baseline.get('conditions'),
              'units': {'energy': 'Wh', 'elapsed': 's', 'average_power': 'W'},
              'issues': issues, 'disposition': 'pending repeated trials and hardware/latency review'}
    if valid:
        result['energy_reduction_percent'] = 100 * (1 - c['energy_wh'] / b['energy_wh'])
        result['elapsed_increase_percent'] = 100 * (c['elapsed_s'] / b['elapsed_s'] - 1)
    new_output(args.output)
    write_json(args.output / 'comparison.json', result)
    lines = ['# SP12 energy comparison', '', 'Energy comparison: ' + ('valid' if valid else 'INVALID'), '',
             'Workload: ' + str(baseline.get('workload')), '',
             'Conditions: ' + json.dumps(baseline.get('conditions'), sort_keys=True), '',
             'Units: Wh, W, seconds. Recovery: follow each candidate settings/rollback record.', '']
    for label, run in [('Baseline', b), ('Candidate', c)]:
        lines += [f"{label}: {json.dumps(run, sort_keys=True)}", '']
    if valid:
        lines += [f"Energy reduction: {result['energy_reduction_percent']:.2f}%.",
                  f"Elapsed-time increase: {result['elapsed_increase_percent']:.2f}%.", '']
    lines += [*issues, '', 'Disposition: pending. One pair cannot establish acceptance.',
              'Require ≥3 interleaved pairs per scenario, ≥10% energy reduction above noise,',
              '≤10% completion-time increase and ≤5% p95 latency regression.',
              'Any storage error, watchdog, resume failure or functional regression rejects the candidate.',
              'Review equivalent work, latency evidence and all hardware gates separately.',
              'Current × voltage estimates are labeled separately and never substituted for gauge energy.',
              'Keep captures private until manually sanitized and reviewed.']
    (args.output / 'comparison.md').write_text('\n'.join(lines) + '\n')


def positive(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError('must be finite and positive')
    return number


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ['inventory', 'sample', 'compare']:
        sub = commands.add_parser(name)
        sub.add_argument('--output', type=Path, required=True)
        if name != 'compare':
            sub.add_argument('--root', type=Path, default=Path('/'), help='fixture filesystem root')
        if name == 'sample':
            sub.add_argument('--duration', type=positive, required=True)
            sub.add_argument('--interval', type=positive, default=5)
            sub.add_argument('--max-power', type=positive, default=100, help='gauge discontinuity ceiling in W')
            sub.add_argument('--battery')
            sub.add_argument('--workload', required=True, help='frozen workload ID, never a command line')
            sub.add_argument('--conditions', type=Path, required=True)
        if name == 'compare':
            sub.add_argument('--baseline', type=Path, required=True)
            sub.add_argument('--candidate', type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    try:
        if args.command == 'inventory':
            result = inventory(args.root)
            new_output(args.output)
            write_json(args.output / 'inventory.json', result)
        elif args.command == 'sample':
            sample(args)
        else:
            compare(args)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f'Collection failed: {error}\n')


if __name__ == '__main__':
    main()
