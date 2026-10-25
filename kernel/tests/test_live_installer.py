# SPDX-License-Identifier: GPL-2.0-or-later
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch, Mock
import uuid
import zlib

spec = importlib.util.spec_from_file_location('live_builder', Path(__file__).resolve().parent.parent / 'live-installer.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class LiveBuilderTests(unittest.TestCase):
    def test_reject_legacy_derivative_and_mismatched_target_inputs(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            tree = Path(directory)
            bundle = tree / 'sp12-kernel'
            bundle.mkdir()
            (bundle / 'linux-image.deb').write_bytes(b'kernel')
            (bundle / 'buildinfo.json').write_bytes(b'build-record')
            (bundle / 'inspection.json').write_text(json.dumps({'verified': True}))
            info = tree / 'sp12-buildinfo.txt'
            valid = 'ubuntu_version=26.10\nlive_boot=stock-ubuntu-with-frozen-bootstrap-dtb\n'
            def check():
                return builder.validate_first_stage(tree, bundle / 'linux-image.deb',
                                                    bundle / 'buildinfo.json', {'verified': True})
            info.write_text(valid)
            self.assertEqual(check()['ubuntu_version'], '26.10')
            for invalid in [valid.replace('26.10', '26.04'), valid.replace(
                    'stock-ubuntu-with-frozen-bootstrap-dtb', 'maintained-sp12')]:
                info.write_text(invalid)
                with self.assertRaises(RuntimeError):
                    check()
            info.write_text(valid)
            wrong_package = tree / 'different.deb'
            wrong_package.write_bytes(b'different-kernel')
            with self.assertRaisesRegex(RuntimeError, 'package differs'):
                builder.validate_first_stage(tree, wrong_package, bundle / 'buildinfo.json', {'verified': True})
            with self.assertRaisesRegex(RuntimeError, 'inspection differs'):
                builder.validate_first_stage(tree, bundle / 'linux-image.deb', bundle / 'buildinfo.json', {})

    def test_recursive_reverse_cleanup_and_physical_comparison_on_failure(self):
        mounts = [Path('/scratch/root'), Path('/scratch/root/sys')]
        for code in [0, 1]:
            with patch.object(builder.subprocess, 'run', return_value=Mock(returncode=code)) as run:
                with patch.object(builder, 'snapshot', return_value={'esp': 'same'}) as snapshot:
                    if code:
                        with self.assertRaisesRegex(RuntimeError, 'Unmount failed'):
                            builder.cleanup_mounts(mounts, {'esp': 'same'})
                    else:
                        builder.cleanup_mounts(mounts, {'esp': 'same'})
                    self.assertEqual([call.args[0] for call in run.call_args_list], [
                        ['umount', '--recursive', str(mounts[1])],
                        ['umount', '--recursive', str(mounts[0])]])
                    snapshot.assert_called_once()

    def test_exact_live_menu_and_required_arguments(self):
        original = ('menuentry "Try or Install Ubuntu" {\n'
                    ' linux /casper/vmlinuz quiet stubble.dtb_override=true\n'
                    ' initrd /casper/initrd\n'
                    ' devicetree /casper/x1p42100-microsoft-sp12in.dtb\n}\n')
        result = builder.grub_config(original, private_support=True)
        for fragment in ['boot=casper', 'layerfs-path=' + builder.LAYER,
                         'cma=128M', 'efi=noruntime', 'stubble.dtb_override=true',
                         'initrd /casper/initrd', 'devicetree /casper/', 'private live v2']:
            self.assertIn(fragment, result)
        self.assertEqual(result.count('layerfs-path='), 1)
        self.assertNotIn('private live v2', builder.grub_config(original))
        for bad in ['', original + original]:
            with self.assertRaises(RuntimeError):
                builder.grub_config(bad)

    def test_hybrid_esp_identity_and_corrupt_gpt_rejection(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            path = Path(directory) / 'synthetic.iso'
            data = bytearray(4096)
            entry = bytearray(128)
            entry[:16] = uuid.UUID('c12a7328-f81f-11d2-ba4b-00a0c93ec93b').bytes_le
            struct.pack_into('<QQ', entry, 32, 4, 5)
            data[1024:1152] = entry
            header = bytearray(512)
            header[:8] = b'EFI PART'
            struct.pack_into('<I', header, 12, 92)
            struct.pack_into('<Q', header, 72, 2)
            struct.pack_into('<III', header, 80, 1, 128, zlib.crc32(entry))
            struct.pack_into('<I', header, 16, zlib.crc32(header[:92]))
            data[512:1024] = header
            path.write_bytes(data)
            first = builder.esp_digest(path)
            data[2048] = 1
            path.write_bytes(data)
            self.assertNotEqual(first, builder.esp_digest(path))
            data[1024] ^= 1
            path.write_bytes(data)
            with self.assertRaisesRegex(RuntimeError, 'table CRC'):
                builder.esp_digest(path)
            data[512 + 20] ^= 1
            path.write_bytes(data)
            with self.assertRaisesRegex(RuntimeError, 'header CRC'):
                builder.esp_digest(path)


unittest.main()
