# vpn.sh

vpn.sh is a shell script to simplify OpenConnect VPN client experience.

## Installation

1. Install dependencies: `brew install openconnect uv vpn-slice`
2. `mkdir -p "${XDG_CONFIG_HOME:-${HOME}/.config}/vpn-sh"`
3. `cp config.example "${XDG_CONFIG_HOME:-${HOME}/.config}/vpn-sh/config"`
4. Modify `${XDG_CONFIG_HOME:-${HOME}/.config}/vpn-sh/config`
5. `sudo cp vpn.sh /usr/local/bin/vpn`
6. `sudo cp vpn-auth.py /usr/local/bin/`

## Usage

Run `sudo vpn --help` to list the available commands.

| Command | Description |
| --- | --- |
| `sudo vpn start` | Connect to the VPN. |
| `sudo vpn stop` | Disconnect from the VPN and remove its routes. |
| `sudo vpn status` | Check whether the VPN is running. |
| `sudo vpn restart` | Disconnect and reconnect to the VPN. |
| `sudo vpn clean` | Remove VPN routes without stopping the VPN process. |

Logs are available at `/var/log/vpn-sh.log`
