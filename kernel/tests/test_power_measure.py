# SPDX-License-Identifier: GPL-2.0-or-later
"""Synthetic sysfs and CSV fixtures; no target hardware or root needed."""
import copy
import csv
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

spec = spec_from_file_location('measure', Path(__file__).resolve().parents[1] / 'power-measure.py')
measure = module_from_spec(spec)
spec.loader.exec_module(measure)


class PowerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.battery = self.root / 'sys/class/power_supply/BAT0'
        for key, value in {'type': 'Battery', 'present': 1, 'scope': 'System',
                           'energy_now': 30000000, 'energy_full': 40000000,
                           'status': 'Discharging', 'voltage_now': 8000000,
                           'current_now': -500000}.items():
            self.put('sys/class/power_supply/BAT0/' + key, value)
        self.put('sys/class/power_supply/AC/type', 'Mains')
        self.put('sys/class/power_supply/AC/online', 0)
        self.metadata = {'schema': 1, 'kind': 'sample', 'complete': True,
                         'interval_s': 5, 'duration_s': 10, 'max_power_w': 100,
                         'workload': 'fixture-v1', 'conditions': {'brightness': 50}}
        self.rows = []
        for i in range(3):
            self.put('sys/class/power_supply/BAT0/energy_now', 30000000 - i * 10000)
            self.rows.append(measure.snapshot(self.root, self.battery, i * 5))

    def put(self, path, value):
        path = self.root / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(value))

    def evaluate(self):
        return measure.evaluate(self.metadata, self.rows)

    def test_units_and_estimate(self):
        self.assertEqual(30, self.rows[0]['energy_wh'])
        self.assertEqual(4, self.rows[0]['estimated_power_w'])
        self.assertIsNone(self.rows[0]['power_w'])
        self.assertAlmostEqual(.02, self.evaluate()['energy_wh'])
        self.assertTrue(self.evaluate()['valid'])

    def test_missing_or_unreadable_interfaces_are_explicit(self):
        self.assertEqual('unavailable', measure.read(self.root, 'missing')['status'])
        self.assertEqual('unavailable', measure.read(self.root, 'sys')['status'])
        self.assertEqual('missing', measure.groups(self.root, 'absent/*', ['value'])['status'])
        self.rows[1]['energy_wh'] = None
        self.assertFalse(self.evaluate()['valid'])

    def test_select_system_battery_over_hid(self):
        for name, attrs in {'hid-secret-address': {'type': 'Battery', 'present': 0, 'energy_now': 100},
                            'mouse': {'type': 'Battery', 'scope': 'Device', 'energy_now': 200}}.items():
            for key, value in attrs.items():
                self.put('sys/class/power_supply/' + name + '/' + key, value)
        self.assertEqual(self.battery, measure.select_battery(self.root))
        self.put('sys/class/power_supply/BAT1/type', 'Battery')
        self.put('sys/class/power_supply/BAT1/scope', 'System')
        self.put('sys/class/power_supply/BAT1/energy_now', 200)
        with self.assertRaises(ValueError):
            measure.select_battery(self.root)
        self.assertEqual(self.battery, measure.select_battery(self.root, 'BAT0'))

    def test_charging_transition_and_unknown_ac_invalidate(self):
        for field, value in [('status', 'Charging'), ('external_power', '1'), ('external_power', 'unknown')]:
            rows = copy.deepcopy(self.rows)
            rows[1][field] = value
            self.assertFalse(measure.evaluate(self.metadata, rows)['valid'])

    def test_resets_discontinuities_gaps_and_nonfinite(self):
        for field, value in [('energy_wh', 31), ('energy_wh', 1), ('energy_wh', 'nan'),
                             ('energy_full_wh', 42), ('elapsed_s', 50), ('elapsed_s', 0)]:
            rows = copy.deepcopy(self.rows)
            rows[1][field] = value
            self.assertFalse(measure.evaluate(self.metadata, rows)['valid'], (field, value))
        self.assertFalse(measure.evaluate(self.metadata, self.rows[1:])['valid'])
        self.metadata['complete'] = False
        self.assertFalse(self.evaluate()['valid'])

    def test_charge_only_never_becomes_measured_energy(self):
        (self.battery / 'energy_now').unlink()
        self.put('sys/class/power_supply/BAT0/charge_now', 5000000)
        row = measure.snapshot(self.root, self.battery, 0)
        self.assertIsNone(row['energy_wh'])
        self.assertEqual(4, row['estimated_power_w'])

    def test_privacy_allowlist(self):
        for path in ['sys/class/dmi/id/product_serial', 'proc/cmdline',
                     'sys/class/power_supply/BAT0/serial_number', 'lib/firmware/secret']:
            self.put(path, 'PRIVATE_SENTINEL')
        self.put('sys/bus/usb/devices/PRIVATE_DEVICE/power/control', 'auto')
        data = json.dumps(measure.inventory(self.root))
        self.assertNotIn('PRIVATE', data)
        self.assertIn('runtime_pm', data)

    def write_run(self, name, metadata=None):
        path = self.root / name
        path.mkdir()
        (path / 'metadata.json').write_text(json.dumps(metadata or self.metadata))
        with (path / 'samples.csv').open('w', newline='') as stream:
            writer = csv.DictWriter(stream, measure.FIELDS)
            writer.writeheader()
            writer.writerows(self.rows)
        return path

    def test_cli_comparison_validity_and_no_overwrite(self):
        base = self.write_run('baseline')
        candidate = self.write_run('candidate')
        output = self.root / 'report'
        command = ['python3', str(Path(measure.__file__)), 'compare', '--baseline', str(base),
                   '--candidate', str(candidate), '--output', str(output)]
        subprocess.run(command, check=True, capture_output=True)
        report = json.loads((output / 'comparison.json').read_text())
        self.assertTrue(report['valid'])
        self.assertIn('pending', report['disposition'])
        self.assertNotEqual(0, subprocess.run(command, capture_output=True).returncode)
        different = copy.deepcopy(self.metadata)
        different['conditions']['brightness'] = 100
        (candidate / 'metadata.json').write_text(json.dumps(different))
        command[-1] = str(self.root / 'mismatched')
        subprocess.run(command, check=True, capture_output=True)
        report = json.loads((self.root / 'mismatched/comparison.json').read_text())
        self.assertFalse(report['valid'])


if __name__ == '__main__':
    unittest.main()
