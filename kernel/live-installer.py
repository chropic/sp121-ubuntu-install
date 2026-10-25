#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Build an experimental Ubuntu 26.10 live ISO with the maintained SP12 kernel.

Private machine support is optional and must be explicitly selected. No image
with that support may be published by this project. See docs/developer/README.md.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import struct
import sys
import tarfile
import tempfile
import uuid
import zlib

ROOT = Path(__file__).resolve().parent.parent
RELEASE = '7.3.0-sp12-v7.3-platform'
SUPPORT_COMMIT = 'ea0f07e66beea95898d96fbeb6daa472f4735af3'
LAYER = 'minimal.standard.live.sp12.squashfs'
MODULES = ['overlay', 'isofs', 'usb_storage', 'uas', 'xhci_plat_hcd',
           'phy_qcom_qmp_combo', 'phy_qcom_snps_femto_v2', 'ufs_qcom',
           'phy_qcom_qmp_ufs', 'pinctrl_x1e80100', 'gcc_x1e80100',
           'qnoc_x1e80100', 'qcom_rpmh_regulator', 'msm', 'panel_edp',
           'ath12k', 'ath12k_wifi7', 'snd_soc_x1e80100', 'qcom_q6v5_pas']
PERSONAL_FILES = {
    'usr/lib/firmware/ath12k/WCN7850/hw2.0/board.bin':
        '0ef5f6f3cb124f33c6de52371819ccd7c13763ceb86d476a178fd56e4cdc26a3',
    'usr/lib/firmware/qcom/x1e80100/X1P42100-Microsoft-Surface-Pro-12in-tplg.bin':
        '89b731f3f98fc2b84699bca39a56e390925a44a26d5aea80382cf617e00c08d8',
    'usr/share/alsa/ucm2/Qualcomm/x1e80100/MICROSOFT-Surface-Pro-12in.conf':
        '171acda75bba76cc47bd258de7cfabe9474382c76e994e8c8164496b00bb50d1',
    'usr/share/alsa/ucm2/Qualcomm/x1e80100/Surface12in-HiFi.conf':
        '76eec2a1f34b9bea9c36c76a75de24c83d8840f73c57dadf1ed397bb5063edaa',
}


def run(*args, **kwargs):
    return subprocess.run([str(a) for a in args], check=True, **kwargs)


def output(*args):
    return subprocess.check_output([str(a) for a in args], text=True)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def grub_config(text, private_support=False):
    require(len(re.findall(r'^\s*linux\s+/casper/vmlinuz\s', text, re.M)) == 1,
            'Unexpected live kernel menu layout')
    text = re.sub(r'(^\s*linux\s+.*)$',
                  r'\1 boot=casper layerfs-path=' + LAYER + ' cma=128M efi=noruntime',
                  text, flags=re.M)
    label = ('Try SP12 Ubuntu 26.10 (private live v2)' if private_support
             else 'Try SP12 Ubuntu 26.10 (experimental live)')
    return text.replace('Try or Install Ubuntu', label)


def esp_digest(image):
    with image.open('rb') as stream:
        stream.seek(512)
        header = bytearray(stream.read(512))
        require(header[:8] == b'EFI PART', 'Missing GPT header')
        size, crc = struct.unpack_from('<II', header, 12)
        require(92 <= size <= 512, 'Invalid GPT header size')
        struct.pack_into('<I', header, 16, 0)
        require(zlib.crc32(header[:size]) == crc, 'GPT header CRC mismatch')
        lba = struct.unpack_from('<Q', header, 72)[0]
        count, entry_size, crc = struct.unpack_from('<III', header, 80)
        require(count <= 4096 and 128 <= entry_size <= 1024, 'Invalid GPT table geometry')
        stream.seek(lba * 512)
        entries = stream.read(count * entry_size)
        require(zlib.crc32(entries) == crc, 'GPT table CRC mismatch')
        hashes = []
        for n in range(count):
            entry = entries[n * entry_size:(n + 1) * entry_size]
            if uuid.UUID(bytes_le=entry[:16]) != uuid.UUID('c12a7328-f81f-11d2-ba4b-00a0c93ec93b'):
                continue
            first, last = struct.unpack_from('<QQ', entry, 32)
            require(first <= last and (last + 1) * 512 <= image.stat().st_size, 'ESP outside image')
            stream.seek(first * 512)
            hashes.append(hashlib.sha256(stream.read((last - first + 1) * 512)).hexdigest())
        require(len(hashes) == 1, 'Expected exactly one ESP')
        return hashes[0]


def snapshot():
    files = sorted(p for p in Path('/boot/efi').rglob('*') if p.is_file())
    require(files, 'Physical ESP is unavailable for comparison')
    return {'esp': {str(p): sha(p) for p in files},
            'nvram': output('efibootmgr', '-v'),
            'mount': output('findmnt', '-n', '-o', 'SOURCE,TARGET,FSTYPE,OPTIONS', '/boot/efi')}


def cleanup_mounts(mounts, before):
    errors = []
    for destination in reversed(mounts):
        # Chroot initramfs hooks can create nested mounts below /sys.
        # Every destination is a mount we created inside the private scratch tree.
        result = subprocess.run(['umount', '--recursive', str(destination)])
        if result.returncode:
            errors.append(str(destination))
    # Always compare physical state, even when an unmount failed.
    require(snapshot() == before, 'Physical-device comparison failed')
    require(not errors, 'Unmount failed: ' + ', '.join(errors))


def validate_first_stage(tree, package, build_info, report):
    info = dict(line.split('=', 1) for line in (tree / 'sp12-buildinfo.txt').read_text().splitlines())
    require(info.get('ubuntu_version') == '26.10', 'Live builder requires Ubuntu 26.10')
    require(info.get('live_boot') == 'stock-ubuntu-with-frozen-bootstrap-dtb',
            'Expected a first-stage stock-live ISO; do not rebuild a private/live derivative')
    require(not (tree / 'casper' / LAYER).exists(), 'SP12 live layer already exists')
    require(sha(tree / 'sp12-kernel/linux-image.deb') == sha(package),
            'First-stage target package differs from the live package')
    require(sha(tree / 'sp12-kernel/buildinfo.json') == sha(build_info),
            'First-stage target build record differs')
    require(json.loads((tree / 'sp12-kernel/inspection.json').read_text()) == report,
            'First-stage target inspection differs')
    return info


def build(args):
    original = args.iso.resolve(strict=True)
    final = args.output.resolve()
    source_sha = args.iso_sha256.lower()
    require(re.fullmatch('[0-9a-f]{64}', source_sha) is not None, 'Invalid ISO SHA-256')
    require(sha(original) == source_sha, 'Base ISO checksum differs')
    require(final.parent.is_dir(), 'Output directory must exist')
    require(not final.exists(), 'Refusing to overwrite output')
    package = args.kernel_package.resolve(strict=True)
    build_info = args.kernel_build_info.resolve(strict=True)
    if not args.apply:
        print('DRY RUN: Ubuntu 26.10 live kernel:', RELEASE)
        print('Base ISO:', original)
        print('Output:', final)
        print('Private machine support:', args.private_machine_support)
        print('No mounts or output files created. Add --apply to build.')
        return
    require(os.geteuid() == 0 and os.uname().machine == 'aarch64', 'Native ARM64 root required')
    require(Path('/proc/self/ns/mnt').readlink() != Path('/proc/1/ns/mnt').readlink(),
            'Private mount namespace required')
    require(Path('/proc/self/ns/net').readlink() != Path('/proc/1/ns/net').readlink(),
            'Private network namespace required')
    partial = final.with_suffix('.iso.partial')
    for path in [final, partial, Path(str(final) + '.sha256'), Path(str(final) + '.buildinfo')]:
        require(not path.exists() and not path.is_symlink(), 'Refusing to overwrite ' + str(path))
    require(shutil.disk_usage(final.parent).free > 24 * 1024**3, 'Need 24 GiB scratch space')
    support = args.support_source.resolve()
    if args.private_machine_support:
        require(output('git', '-C', support, 'rev-parse', 'HEAD').strip() == SUPPORT_COMMIT,
                'Unexpected support checkout revision')
        for relative, expected in PERSONAL_FILES.items():
            require(sha(args.machine_root / relative) == expected, 'Support file differs: ' + relative)
    before = snapshot()
    work = Path(tempfile.mkdtemp(prefix='private-live-v2.', dir=final.parent))
    mounts = []
    success = False

    def mount(destination, *args):
        destination.mkdir(parents=True, exist_ok=True)
        run('mount', *args, destination)
        mounts.append(destination)

    def copy(source, destination):
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        destination.chmod(0o644)

    try:
        print('Scratch directory:', work, flush=True)
        xorriso = args.xorriso
        tree = work / 'original'
        with (work / 'extract.log').open('w') as log:
            run(xorriso, '-osirrox', 'on', '-indev', original, '-extract', '/', tree,
                stdout=log, stderr=subprocess.STDOUT)
        run('md5sum', '--quiet', '-c', 'md5sum.txt', cwd=tree)
        run('python3', ROOT / 'kernel/installer-kernel.py', 'bundle',
            '--package', package, '--build-info', build_info,
            '--output', work / 'verified-kernel')
        report = json.loads((work / 'verified-kernel/inspection.json').read_text())
        validate_first_stage(tree, package, build_info, report)
        kernel = work / 'kernel'
        run('dpkg-deb', '-x', package, kernel)
        stage = work / 'stage'
        (stage / 'usr/lib').mkdir(parents=True)
        (stage / 'lib').symlink_to('usr/lib')
        shutil.copytree(kernel / 'lib/modules', stage / 'usr/lib/modules', symlinks=True)
        shutil.copytree(kernel / 'usr', stage / 'usr', dirs_exist_ok=True, symlinks=True)
        shutil.copytree(kernel / 'boot', stage / 'boot', symlinks=True)
        require(sha(stage / ('boot/vmlinuz-' + RELEASE)) == report['image_sha256'], 'Kernel mismatch')
        dtb = stage / ('usr/lib/linux-image-' + RELEASE) / 'qcom/x1p42100-microsoft-sp12in.dtb'
        require(sha(dtb) == report['dtb_sha256'], 'Maintained DTB mismatch')

        if args.private_machine_support:
            # Explicit personal-use allowlist; no home, network profiles, or machine credentials.
            archive = work / 'personal-platform.tar'
            run('git', '-C', support, 'archive', '--format=tar', '--output=' + str(archive),
                SUPPORT_COMMIT, 'lib/firmware/qcom', 'usr/share/qcom')
            extracted = work / 'personal-platform'
            with tarfile.open(archive) as bundle:
                bundle.extractall(extracted, filter='data')
            shutil.copytree(extracted / 'lib/firmware/qcom', stage / 'usr/lib/firmware/qcom',
                            dirs_exist_ok=True, symlinks=True)
            shutil.copytree(extracted / 'usr/share/qcom', stage / 'usr/share/qcom', symlinks=True)
            for relative, expected in PERSONAL_FILES.items():
                copy(args.machine_root / relative, stage / relative)
                require(sha(stage / relative) == expected, 'Copied support file mismatch')
        run('depmod', '-b', stage, RELEASE)

        layers = []
        for name in ['minimal', 'minimal.standard', 'minimal.standard.live']:
            layer = work / name
            mount(layer, '-t', 'squashfs', '-o', 'loop,ro,nodev,nosuid', tree / ('casper/' + name + '.squashfs'))
            layers.append(layer)
        root = work / 'root'
        upper, overlay_work = work / 'upper', work / 'overlay-work'
        upper.mkdir()
        overlay_work.mkdir()
        lower = ':'.join(str(p) for p in [stage] + list(reversed(layers)))
        mount(root, '-t', 'overlay', '-o', f'lowerdir={lower},upperdir={upper},workdir={overlay_work}', 'overlay')
        require('VERSION_ID="26.10"' in (root / 'etc/os-release').read_text(), 'Wrong live root version')
        # Empty dev plus two character devices: no physical block devices in the chroot.
        mount(root / 'dev', '-t', 'tmpfs', '-o', 'nosuid,mode=755', 'tmpfs')
        for name in ['null', 'zero', 'random', 'urandom']:
            (root / 'dev' / name).touch()
            run('mount', '--bind', '/dev/' + name, root / 'dev' / name)
            mounts.append(root / 'dev' / name)
        mount(root / 'proc', '-t', 'proc', '-o', 'nosuid,nodev,noexec', 'proc')
        mount(root / 'sys', '--bind', '/sys')
        run('mount', '-o', 'remount,bind,ro,nosuid,nodev,noexec', root / 'sys')
        generated = work / 'generated'
        generated.mkdir()
        mount(root / 'tmp/sp12-live-build', '--bind', generated)
        config = root / 'etc/initramfs-tools/conf.d/sp12-live'
        config.write_text('MODULES=most\nCOMPRESS=zstd\nBOOT=casper\n')
        with (root / 'etc/initramfs-tools/modules').open('a') as stream:
            stream.write('\n# SP12 live boot and hardware dependencies\n' + '\n'.join(MODULES) + '\n')
        old_initrd = work / 'original-initrd'
        run('unmkinitramfs', tree / 'casper/initrd', old_initrd)
        old_uuid_files = list(old_initrd.rglob('conf/uuid.conf'))
        require(len(old_uuid_files) == 1, 'Expected one casper media UUID')
        uuid = old_uuid_files[0].read_text().strip()
        require(re.fullmatch(r'[0-9a-f-]{36}', uuid) is not None, 'Unexpected original casper UUID')
        hook = root / 'etc/initramfs-tools/hooks/zzzz-sp12-live'
        hook.write_text('#!/bin/sh\nset -eu\n'
                        'if [ "${1:-}" = prereqs ]; then exit 0; fi\n'
                        'mkdir -p "$DESTDIR/conf/conf.d"\n'
                        f"printf '%s\\n' '{uuid}' > \"$DESTDIR/conf/uuid.conf\"\n"
                        f"printf '%s\\n' 'LAYERFS_PATH={LAYER}' > \"$DESTDIR/conf/conf.d/default-layer.conf\"\n"
                        "printf '%s\\n' 'BOOT=casper' > \"$DESTDIR/conf/conf.d/default-boot-to-casper.conf\"\n")
        hook.chmod(0o755)
        print('Generating casper initramfs with the maintained SP12 modules...', flush=True)
        with (work / 'mkinitramfs.log').open('w') as log:
            run('chroot', root, '/usr/sbin/mkinitramfs', '-o', '/tmp/sp12-live-build/initrd', RELEASE,
                stdout=log, stderr=subprocess.STDOUT, env={**os.environ, 'LC_ALL': 'C', 'SYSTEMD_OFFLINE': '1'})
        listing = output('lsinitramfs', generated / 'initrd')
        names = {p.removeprefix('./').removeprefix('usr/').rstrip('/') for p in listing.splitlines()}
        releases = {p.split('/')[2] for p in names if p.startswith('lib/modules/') and len(p.split('/')) > 2}
        require(releases == {RELEASE}, 'Wrong initramfs module release set: ' + str(releases))
        require('scripts/casper' in names and 'scripts/casper-bottom/25adduser' in names,
                'Missing casper live-session scripts')
        for module in MODULES:
            vermagic = output('modinfo', '-b', stage, '-k', RELEASE, '-F', 'vermagic', module).split()[0]
            require(vermagic == RELEASE, 'Wrong module vermagic: ' + module)
            dependencies = output('modprobe', '-d', stage, '-S', RELEASE, '--show-depends', module)
            for line in dependencies.splitlines():
                if line.startswith('insmod '):
                    path = Path(line.split()[1])
                    relative = str(path.relative_to(stage)) if path.is_relative_to(stage) else str(path).lstrip('/')
                    require(relative.removeprefix('usr/') in names, 'Missing initramfs dependency: ' + relative)
        initrd_tree = work / 'new-initrd'
        run('unmkinitramfs', generated / 'initrd', initrd_tree)
        candidates = list(initrd_tree.rglob('conf/uuid.conf'))
        require(len(candidates) == 1 and candidates[0].read_text().strip() == uuid, 'Casper UUID mismatch')
        layer_confs = list(initrd_tree.rglob('conf/conf.d/default-layer.conf'))
        require(len(layer_confs) == 1 and LAYER in layer_confs[0].read_text(), 'Wrong initramfs default layer')

        # Only intentional stage files become a live-only layer. Chroot build state is excluded.
        overlay = generated / LAYER
        run('mksquashfs', stage, overlay, '-noappend', '-comp', 'zstd', '-processors', '4', '-no-progress')
        overlay_manifest = {str(p.relative_to(stage)): sha(p) for p in sorted(stage.rglob('*'))
                            if p.is_file() and not p.is_symlink()}
        (generated / 'live-overlay-manifest.json').write_text(json.dumps(overlay_manifest, indent=2) + '\n')
        info = dict(line.split('=', 1) for line in (tree / 'sp12-buildinfo.txt').read_text().splitlines())
        info.update(live_boot='maintained-sp12',
                    distribution='private-local-testing-only-do-not-publish',
                    live_kernel_release=RELEASE, live_kernel_sha256=report['image_sha256'],
                    dtb_sha256=report['dtb_sha256'], dtb_name='maintained-platform-dtb',
                    live_initrd_sha256=sha(generated / 'initrd'), live_overlay_sha256=sha(overlay),
                    rebuild_script_sha256=sha(__file__), previous_candidate_sha256=source_sha)
        info['private_machine_support'] = str(args.private_machine_support).lower()
        (generated / 'sp12-buildinfo.txt').write_text(''.join(f'{k}={v}\n' for k, v in info.items()))
        (generated / 'grub.cfg').write_text(grub_config(
            (tree / 'boot/grub/grub.cfg').read_text(), args.private_machine_support))
        replacements = {
            'casper/vmlinuz': stage / ('boot/vmlinuz-' + RELEASE),
            'casper/initrd': generated / 'initrd',
            'casper/x1p42100-microsoft-sp12in.dtb': dtb,
            'casper/' + LAYER: overlay,
            'boot/grub/grub.cfg': generated / 'grub.cfg',
            'sp12-buildinfo.txt': generated / 'sp12-buildinfo.txt',
            'sp12-live-overlay-manifest.json': generated / 'live-overlay-manifest.json',
            'sp12-private-live-rebuild.py': Path(__file__),
        }
        md5 = [line for line in (tree / 'md5sum.txt').read_text().splitlines()
               if line.split(maxsplit=1)[1].removeprefix('./') not in replacements]
        for name, path in replacements.items():
            with path.open('rb') as stream:
                digest = hashlib.file_digest(stream, 'md5').hexdigest()
            md5.append(f'{digest}  ./{name}')
        (generated / 'md5sum.txt').write_text('\n'.join(md5) + '\n')
        replacements['md5sum.txt'] = generated / 'md5sum.txt'
        args = [xorriso, '-indev', original, '-outdev', partial, '-boot_image', 'any', 'replay']
        for name, path in replacements.items():
            args.extend(['-update', path, '/' + name])
        args.extend(['-padding', '0', '-commit'])
        with (work / 'xorriso.log').open('w') as log:
            run(*args, stdout=log, stderr=subprocess.STDOUT)
        layout = subprocess.check_output([str(xorriso), '-indev', str(partial), '-report_system_area', 'plain'],
                                         stderr=subprocess.STDOUT, text=True)
        sectors = re.search(r'^ISO image size/512\s*:\s*(\d+)', layout, re.M)
        require(sectors is not None, 'Cannot determine hybrid ISO size')
        os.truncate(partial, int(sectors[1]) * 512)
        run('sgdisk', '-v', partial)
        require(esp_digest(partial) == esp_digest(original), 'ISO EFI partition changed')
        audit = work / 'audit'
        with (work / 'audit-extract.log').open('w') as log:
            run(xorriso, '-osirrox', 'on', '-indev', partial, '-extract', '/', audit,
                stdout=log, stderr=subprocess.STDOUT)
        run('md5sum', '--quiet', '-c', 'md5sum.txt', cwd=audit)
        for image in audit.rglob('*'):
            if image.is_file() and image.suffix.lower() == '.efi':
                run('grub-file', '--is-arm64-efi', image)
        for name, path in replacements.items():
            require(sha(audit / name) == sha(path), 'ISO replacement mismatch: ' + name)
        for name in ['minimal.squashfs', 'minimal.standard.squashfs', 'minimal.standard.live.squashfs',
                     'install-sources.yaml']:
            require(sha(audit / 'casper' / name) == sha(tree / 'casper' / name), 'Install layer changed: ' + name)
        for relative, expected in overlay_manifest.items():
            # The full immutable source tree is hashed above; verify representative squashfs extraction too.
            if relative.endswith('board.bin') or relative.endswith('Surface12in-HiFi.conf'):
                data = subprocess.check_output(['unsquashfs', '-cat', str(audit / 'casper' / LAYER), relative])
                require(hashlib.sha256(data).hexdigest() == expected, 'Live squashfs payload differs')
        require(snapshot() == before, 'Physical ESP/NVRAM/mount state changed')
        digest = sha(partial)
        partial.rename(final)
        Path(str(final) + '.sha256').write_text(f'{digest}  {final.name}\n')
        shutil.copyfile(generated / 'sp12-buildinfo.txt', Path(str(final) + '.buildinfo'))
        uid, gid = original.stat().st_uid, original.stat().st_gid
        for path in [final, Path(str(final) + '.sha256'), Path(str(final) + '.buildinfo')]:
            path.chmod(0o644)
            os.chown(path, uid, gid)
        success = True
        print('PASS: full media manifest, SP12 kernel/module/DTB, casper and private support audit', flush=True)
        print('PASS: physical ESP, NVRAM and ESP mount state unchanged', flush=True)
        print('EXPERIMENTAL TEST IMAGE:', final, flush=True)
        print('SHA256:', digest, flush=True)
        print('Live Wi-Fi/audio remain unverified until physical boot.', flush=True)
    finally:
        cleanup_mounts(mounts, before)
        print('Build evidence retained:', work, 'success=' + str(success), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--iso', type=Path, required=True, help='ISO from scripts/build-installer')
    parser.add_argument('--iso-sha256', required=True)
    parser.add_argument('--kernel-package', type=Path, required=True)
    parser.add_argument('--kernel-build-info', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--xorriso', default='xorriso')
    parser.add_argument('--private-machine-support', action='store_true')
    parser.add_argument('--support-source', type=Path, default=Path('/opt/surface-pro-12-linux'))
    parser.add_argument('--machine-root', type=Path, default=Path('/'),
                        help='Root containing the four verified personal support files')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    try:
        build(args)
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__':
    main()
