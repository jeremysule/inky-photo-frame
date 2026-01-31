#!/usr/bin/env python3
"""SD card image generator for Inky Photo Frame.

Creates a bootable Raspberry Pi OS image with:
- Inky Photo Frame pre-installed
- WiFi configuration via wpa_supplicant.conf (optional)
- Auto-start service
- Optimized for headless operation

Requirements: pip install raspi-os-tools
"""

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ImageConfig:
    """Configuration for image building."""

    # Base image URL (Raspberry Pi OS Lite)
    base_image_url: str = "https://downloads.raspberrypi.com/raspios_lite_arm64/images/raspios_lite_arm64-2025-12-04/2025-12-04-raspios-trixie-arm64-lite.img.xz"

    # Script directory (base for relative paths)
    script_dir: Path = Path(__file__).parent

    # Output directory (relative to script dir)
    output_dir: Path = Path(__file__).parent / "build"

    # WiFi configuration
    wifi_ssid: str | None = None
    wifi_password: str | None = None
    wifi_country: str = "GB"

    # SSH keys
    ssh_pubkey: str | None = None

    # Hostname
    hostname: str = "inky-frame"

    # User credentials (for first-boot setup skip)
    username: str = "pi"
    password: str = "inkyframe"


def download_file(url: str, dest: Path, show_progress: bool = True) -> None:
    """Download a file with optional progress indicator.

    Args:
        url: URL to download.
        dest: Destination path.
        show_progress: Show download progress.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)

    print(f"Downloading: {url}")

    def report_progress(block_num, block_size, total_size):
        if show_progress and total_size > 0:
            downloaded = block_num * block_size
            percent = min(100, downloaded * 100 / total_size)
            sys.stdout.write(f"\rProgress: {percent:.1f}%")
            sys.stdout.flush()

    urllib.request.urlretrieve(url, dest, reporthook=report_progress)
    print()  # New line after progress


def calculate_sha256(path: Path) -> str:
    """Calculate SHA256 checksum of a file.

    Args:
        path: Path to file.

    Returns:
        Hexadecimal SHA256 checksum.
    """
    sha256 = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def extract_xz(source: Path, dest: Path) -> None:
    """Extract a .xz file.

    Args:
        source: Source .xz file.
        dest: Destination path.
    """
    print(f"Extracting: {source}")

    import lzma

    with lzma.open(source, "rb") as f_in:
        with dest.open("wb") as f_out:
            shutil.copyfileobj(f_in, f_out)


def mount_image(image_path: Path) -> tuple[Path, Path] | None:
    """Mount the Raspberry Pi OS image partitions.

    Args:
        image_path: Path to the image file.

    Returns:
        Tuple of (boot_mount, root_mount) or None on failure.
    """
    print("Mounting image partitions...")

    # Setup loop device
    result = subprocess.run(
        ["sudo", "losetup", "--find", "--show", "--partscan", str(image_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None

    loop_device = result.stdout.strip()
    print(f"Loop device: {loop_device}")

    # Wait for partition devices to appear
    import time
    time.sleep(1)

    boot_partition = f"{loop_device}p1"
    root_partition = f"{loop_device}p2"

    # Create mount points
    boot_mount = Path(tempfile.mkdtemp(prefix="inky-boot-"))
    root_mount = Path(tempfile.mkdtemp(prefix="inky-root-"))

    # Mount partitions
    subprocess.run(["sudo", "mount", boot_partition, str(boot_mount)], check=True)
    subprocess.run(["sudo", "mount", root_partition, str(root_mount)], check=True)

    # Make mount points writable by current user
    import getpass
    user = getpass.getuser()
    subprocess.run(["sudo", "chown", "-R", f"{user}:{user}", str(boot_mount)], check=True)
    subprocess.run(["sudo", "chown", "-R", f"{user}:{user}", str(root_mount)], check=True)

    return boot_mount, root_mount


def unmount_image(boot_mount: Path, root_mount: Path) -> None:
    """Unmount the image partitions.

    Args:
        boot_mount: Boot partition mount point.
        root_mount: Root partition mount point.
    """
    print("Unmounting partitions...")

    subprocess.run(["sudo", "umount", str(boot_mount)])
    subprocess.run(["sudo", "umount", str(root_mount)])

    os.rmdir(boot_mount)
    os.rmdir(root_mount)

    # Detach loop device
    subprocess.run(["sudo", "losetup", "--detach-all"])


def configure_wifi(boot_mount: Path, root_mount: Path, config: ImageConfig) -> None:
    """Configure WiFi using wpa_supplicant.conf.

    For Raspberry Pi OS, placing wpa_supplicant.conf on the boot partition
    is the most reliable method for headless WiFi setup. The file is copied
    to /etc/wpa_supplicant/wpa_supplicant.conf on first boot.

    This also:
    - Sets regulatory domain in cmdline.txt (required for WiFi)
    - Creates udev rule to unblock WiFi radio at boot

    Args:
        boot_mount: Boot partition mount point.
        root_mount: Root partition mount point.
        config: Image configuration.
    """
    if not config.wifi_ssid:
        return

    print("Configuring WiFi...")

    # 1. Create wpa_supplicant.conf on boot partition
    # Pi OS copies this to /etc/wpa_supplicant/wpa_supplicant.conf on first boot
    wpa_conf = boot_mount / "wpa_supplicant.conf"
    wpa_conf.write_text(f"""country={config.wifi_country}
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={{
    ssid="{config.wifi_ssid}"
    psk="{config.wifi_password}"
    key_mgmt=WPA-PSK
}}
""")
    os.chmod(wpa_conf, 0o600)

    # 2. Set regulatory domain in cmdline.txt
    # Kernel needs regulatory domain before WiFi can work
    cmdline_file = boot_mount / "cmdline.txt"
    if cmdline_file.exists():
        cmdline = cmdline_file.read_text().strip()
        regdom_param = f"cfg80211.ieee80211_regdom={config.wifi_country}"
        if regdom_param not in cmdline:
            cmdline += f" {regdom_param}"
            cmdline_file.write_text(cmdline + "\n")

    # 3. Udev rule to unblock WiFi when device appears
    # The rfkill soft-block happens before any network config is read
    udev_rules_dir = root_mount / "etc" / "udev" / "rules.d"
    udev_rules_dir.mkdir(parents=True, exist_ok=True)
    udev_rule = udev_rules_dir / "90-wifi-unblock.rules"
    udev_rule.write_text('ACTION=="add", SUBSYSTEM=="rfkill", RUN+="/usr/sbin/rfkill unblock wifi"\n')
    os.chmod(udev_rule, 0o644)


def enable_ssh(boot_mount: Path) -> None:
    """Enable SSH by creating the ssh file.

    Args:
        boot_mount: Boot partition mount point.
    """
    print("Enabling SSH...")
    ssh_file = boot_mount / "ssh"
    ssh_file.touch()


def create_userconf(boot_mount: Path, username: str = "pi", password: str = "inkyframe") -> None:
    """Create userconf file to skip first-boot setup wizard.

    Newer Raspberry Pi OS requires this to pre-create a user.
    Without it, the system forces user creation on first boot.

    Args:
        boot_mount: Boot partition mount point.
        username: Default username.
        password: Default password.
    """
    print(f"Creating userconf for user '{username}'...")

    # Generate salted password hash for userconf
    # Format: username:encrypted_password
    # Using the same method as Raspberry Pi's imaging utility
    import base64

    # Create a simple bcrypt-compatible hash
    # The userconf format expects username followed by ':' followed by the password hash
    # We'll use a simple approach - base64 encode the password for the userconf
    # Note: This is a simplified version - for production use proper bcrypt

    # Actually, for userconf we need to use a specific format.
    # The proper way is to use openssl passwd -6 or similar
    # Let's use subprocess to create a proper SHA-512 hash

    result = subprocess.run(
        [
            "openssl", "passwd", "-6",
            password
        ],
        capture_output=True,
        text=True,
        check=True
    )
    password_hash = result.stdout.strip()

    userconf_content = f"{username}:{password_hash}\n"
    userconf_file = boot_mount / "userconf"
    userconf_file.write_text(userconf_content)
    os.chmod(userconf_file, 0o600)


def setup_ssh_keys(root_mount: Path, config: ImageConfig) -> None:
    """Setup SSH keys for passwordless login.

    Args:
        root_mount: Root partition mount point.
        config: Image configuration.
    """
    if not config.ssh_pubkey:
        return

    print("Setting up SSH keys...")

    ssh_dir = root_mount / "home" / "pi" / ".ssh"
    ssh_dir.mkdir(exist_ok=True)
    os.chmod(ssh_dir, 0o700)

    authorized_keys = ssh_dir / "authorized_keys"
    authorized_keys.write_text(config.ssh_pubkey + "\n")
    os.chmod(authorized_keys, 0o600)

    # Fix ownership
    subprocess.run(["sudo", "chown", "-R", "1000:1000", str(ssh_dir)])


def set_hostname(root_mount: Path, config: ImageConfig) -> None:
    """Set the system hostname.

    Args:
        root_mount: Root partition mount point.
        config: Image configuration.
    """
    print(f"Setting hostname to: {config.hostname}")

    hostname_file = root_mount / "etc" / "hostname"
    hostname_file.write_text(config.hostname + "\n")

    # Update hosts file
    hosts_file = root_mount / "etc" / "hosts"
    content = hosts_file.read_text()
    content = content.replace("raspberrypi", config.hostname)
    hosts_file.write_text(content)


def install_app(root_mount: Path, config: ImageConfig) -> None:
    """Install the Inky Photo Frame application.

    Args:
        root_mount: Root partition mount point.
        config: Image configuration.
    """
    print("Installing Inky Photo Frame...")

    app_dir = root_mount / "opt" / "inky-photo-frame"
    app_dir.mkdir(parents=True, exist_ok=True)

    # Copy application files
    for item in ["src", "main.py", "requirements.txt", "config.toml"]:
        src = config.script_dir / item
        if src.is_dir():
            dest = app_dir / item
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
        else:
            shutil.copy2(src, app_dir / item)

    # Create systemd service
    service_file = root_mount / "etc" / "systemd" / "system" / "photo-frame.service"
    service_content = """[Unit]
Description=Inky Photo Frame
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/opt/inky-photo-frame
ExecStart=/usr/bin/python3 /opt/inky-photo-frame/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    service_file.write_text(service_content)

    # Enable service
    service_link = root_mount / "etc" / "systemd" / "system" / "multi-user.target.wants" / "photo-frame.service"
    service_link.symlink_to("/etc/systemd/system/photo-frame.service")


def build_image(config: ImageConfig) -> Path:
    """Build the SD card image.

    Args:
        config: Image configuration.

    Returns:
        Path to the built image.
    """
    config.output_dir.mkdir(parents=True, exist_ok=True)

    # Paths
    image_name = f"inky-frame-{config.hostname}.img"
    cache_dir = config.output_dir / "cache"
    cache_dir.mkdir(exist_ok=True)

    base_xz = cache_dir / Path(config.base_image_url).name
    base_img = cache_dir / base_xz.stem.replace(".xz", "")
    output_img = config.output_dir / image_name

    # Download base image if needed
    if not base_xz.exists():
        download_file(config.base_image_url, base_xz)

    # Extract if needed
    if not base_img.exists():
        extract_xz(base_xz, base_img)

    # Copy to output
    print(f"Creating image: {output_img}")
    shutil.copy2(base_img, output_img)

    # Mount and configure
    mounts = mount_image(output_img)
    if mounts is None:
        raise RuntimeError("Failed to mount image")

    boot_mount, root_mount = mounts

    try:
        configure_wifi(boot_mount, root_mount, config)
        enable_ssh(boot_mount)
        create_userconf(boot_mount, config.username, config.password)
        set_hostname(root_mount, config)
        install_app(root_mount, config)
    finally:
        unmount_image(boot_mount, root_mount)

    print(f"\nImage built successfully: {output_img}")
    return output_img


def main() -> int:
    """Main entry point.

    Returns:
        Exit code.
    """
    parser = argparse.ArgumentParser(
        description="Build SD card image for Inky Photo Frame"
    )
    parser.add_argument(
        "--wifi-ssid",
        help="WiFi SSID",
    )
    parser.add_argument(
        "--wifi-password",
        help="WiFi password",
    )
    parser.add_argument(
        "--wifi-country",
        default="US",
        help="WiFi country code (default: US)",
    )
    parser.add_argument(
        "--ssh-pubkey",
        help="SSH public key for passwordless login",
    )
    parser.add_argument(
        "--hostname",
        default="inky-frame",
        help="System hostname (default: inky-frame)",
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory (default: <script-dir>/build)",
    )
    parser.add_argument(
        "--username",
        default="pi",
        help="Default username (default: pi)",
    )
    parser.add_argument(
        "--password",
        default="inkyframe",
        help="Default password for user (default: inkyframe)",
    )

    args = parser.parse_args()

    # Handle output directory - make it absolute relative to script dir
    script_dir = Path(__file__).parent
    if args.output_dir:
        output_dir = Path(args.output_dir)
        if not output_dir.is_absolute():
            output_dir = script_dir / output_dir
    else:
        output_dir = script_dir / "build"

    config = ImageConfig(
        wifi_ssid=args.wifi_ssid,
        wifi_password=args.wifi_password,
        wifi_country=args.wifi_country,
        ssh_pubkey=args.ssh_pubkey,
        hostname=args.hostname,
        output_dir=output_dir,
        script_dir=script_dir,
        username=args.username,
        password=args.password,
    )

    try:
        build_image(config)
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
