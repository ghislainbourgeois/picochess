# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import logging
import time

from eboard.certabo.protocol import Protocol


logger = logging.getLogger(__name__)


class CertaboAgent:

    def __init__(self, appque):
        self.name = 'CertaboAgent'
        self.appque = appque
        self.brd = Protocol(self.appque, self.name)
        self.init_position = False

        if not self.brd.connected:
            logger.warning('Connection to Certabo failed.')
            return

        logger.debug('waiting for board position')
        start = time.time()
        warned = False
        while not self.init_position:
            if self.brd.error_condition:
                logger.info('Certabo board not available.')
                return
            if time.time() - start > 2 and not warned:
                warned = True
                logger.info('Searching for Certabo board...')
            self.init_position = self.brd.position_initialized()
            time.sleep(0.1)

        if self.init_position:
            logger.debug('board position received, init ok.')
        else:
            logger.error('no board position received')

    def quit(self):
        self.brd.quit()

    def set_led_off(self):
        self.brd.set_led_off()

    def set_led(self, pos):
        self.brd.set_led(pos)

    def uci_move(self, move: str):
        self.brd.uci_move(move)

    def promotion_done(self, uci_move: str):
        self.brd.promotion_done(uci_move)
