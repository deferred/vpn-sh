# vpn.sh

vpn.sh is a shell script to simplify OpenConnect VPN client experience.

## Installation

1. Install OpenConnect and vpn-slice `brew install openconnect vpn-slice`
2. `mkdir -p "${XDG_CONFIG_HOME:-${HOME}/.config}/vpn-sh"`
3. `cp config.example "${XDG_CONFIG_HOME:-${HOME}/.config}/vpn-sh/config"`
4. Modify `${XDG_CONFIG_HOME:-${HOME}/.config}/vpn-sh/config`
5. `sudo cp vpn.sh /usr/local/bin/vpn`

## Usage

```bash
# shows available commands
vpn

# starts vpn
sudo vpn start

# stops vpn
sudo vpn stop

# shows vpn status
sudo vpn status

# restarts vpn
sudo vpn restart
```

Logs are available at `/var/log/vpn-sh.log`
