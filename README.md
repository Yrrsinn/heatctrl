# heatctrl
Wrapper around https://github.com/Heckie75/eQ-3-radiator-thermostat to control the eQ-3 radiator-thermostats in the AfRA.

### Device setup
For each device:

    $ sudo bluetoothctl
    # power on
    # discoverable on
    # pairable on
    # agent on
    # scan on
    # scan off
    # pair 00:1A:22:xx:yy:zz -- am geraet knopf lang druecken 'pair' im display
    # quit

### Known devices:
- 00:1A:22:09:8B:D7 Tuerschloss
- 00:1A:22:10:B5:74 wohnzimmer
- 00:1A:22:11:0B:5C werkstatt_links
- 00:1A:22:11:02:CE werkstatt_rechts
- 00:1A:22:11:02:D0 toilette

### Installation
Clone this repository to /home/afra/heizung
sudo cp eq3.exp /usr/local/bin/eq3.exp
sudo cp heizung.service /etc/systemd/system/
sudo systemctl enable heizung.service
sudo systemctl start heizung.service

