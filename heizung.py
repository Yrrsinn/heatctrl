#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sys import stdout
from time import time, sleep
from subprocess import Popen, PIPE
from enum import Enum, unique
from requests import get
from requests.exceptions import ConnectionError, ConnectTimeout
from logging import basicConfig, getLogger, INFO, DEBUG
debug = False
if debug:
    basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=DEBUG,
        stream=stdout)
else:
    basicConfig(
        format='%(message)s',
        level=INFO,
        stream=stdout)
log = getLogger(__name__)

air_time_backoff = 10.0
devices = {
    'wohnzimmer': '00:1A:22:10:B5:74',
    'werkstatt_links': '00:1A:22:11:0B:5C',
    'werkstatt_rechts': '00:1A:22:11:02:CE',
    'toilette': '00:1A:22:11:02:D0'
}


class Eq3:
    _sleep = 10.0

    @unique
    class State(Enum):
        unknown = 'unkown'
        initialization = 'initialization'
        comfort = 'comfort'
        eco = 'eco'

    def __init__(self, alias, mac):
        self._alias = alias
        self._mac = mac
        self.temp_comfort = 21.0
        self.temp_eco = 17.0
        self._last_time = time() - 2.0 * self._sleep
        self._target = self.State.initialization
        self._state = self.State.unknown

    def __send_cmd(self, param):
        if abs(time() - self._last_time) < self._sleep:
            return 1, '', 'airtime interval violated'
        _cmd = ['eq3.exp']
        _cmd += [self._mac]
        _cmd += param
        try:
            _p = Popen(_cmd, stdout=PIPE, stderr=PIPE)
            _out, _err = _p.communicate()
            _out, _err = _out.decode('utf8'), _err.decode('utf8')
            _ret = _p.returncode
        except Exception as e:
            log.error('Excepion (%s): %r' % (self._mac, e))
            return 1, '%s ' % param[0], 'failed '
        return _ret, '%s ' % _out, '%s ' % _err

    def __send_init(self):
        _cmd = ['comforteco',
                str(float(self.temp_comfort)),
                str(float(self.temp_eco))]
        code, out, err = self.__send_cmd(_cmd)
        if code > 0:
            return code, out, err
        else:
            return 0, 'comfort-eco initialization ', ''

    def update(self):
        _msg = '%s (%s): ' % (self._alias, self._mac)
        if self._state != self._target:
            if self._target is self.State.initialization:
                code, out, err = self.__send_init()
                _msg += out
            elif self._target is self.State.comfort:
                code, out, err = self.__send_cmd(['comfort'])
                _msg += 'switch to state %s ' % self.State.comfort
            elif self._target is self.State.eco:
                code, out, err = self.__send_cmd(['eco'])
                _msg += 'switch to state %s ' % self.State.eco
            else:
                code, out, err = 1, ' ', 'Internal Error '
            if code > 0:
                _msg += '%s %s' % (out, err)
                log.error(_msg)
            else:
                self._state = self._target
                log.info(_msg)
        else:
            _msg += 'is already in state %s, nothing to do.' % self._state
            log.debug(_msg)

    def on(self):
        self._target = self.State.comfort
        self.update()

    def off(self):
        self._target = self.State.eco
        self.update()


def is_door_unlocked():
    try:
        t = get('http://door.lan:8080/').text
        return 0 == t.find('Door status: UNLOCKED')
    except (ConnectionError, ConnectTimeout, NameError):
        log.debug('kann Tuerstatus nicht lesen')
        return False


def is_afra_open():
    try:
        t = get('https://spaceapi.afra-berlin.de/v1/status').text
        return 0 == t.find('Status true')
    except (ConnectionError, ConnectTimeout, NameError):
        log.debug('kann AfRA Status nicht lesen')
        return False


def main():
    log.info('Start')
    _devices = {}
    for alias, mac in devices.items():
        _devices[alias] = Eq3(alias, mac)
        _devices[alias].update()
    try:
        while True:
            if is_afra_open() or is_door_unlocked():
                log.debug('AfRA ist offen')
                for _, radiator in _devices.items():
                    radiator.on()
            else:
                log.debug('AfRa ist geschlossen')
                for _, radiator in _devices.items():
                    radiator.off()
            sleep(air_time_backoff)
            for _, radiator in _devices.items():
                radiator.update()
    except KeyboardInterrupt:
        log.info('Stop')
        pass


if __name__ == '__main__':
    main()
