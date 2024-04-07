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

import time
import logging
from threading import Thread
import queue

from eboard.eboard import EBoard
from utilities import DisplayMsg
from dgt.api import Message, Dgt
from dgt.util import ClockIcons

from eboard.certabo.certabo_agent import CertaboAgent


logger = logging.getLogger(__name__)


class CertaboBoard(EBoard):

    def __init__(self):
        self.agent = None
        self.appque = queue.Queue()

    def light_squares_on_revelation(self, uci_move: str):
        logger.debug('turn LEDs on - move: %s', uci_move)
        dpos = [[0 for _ in range(8)] for _ in range(8)]
        dpos[int(uci_move[1]) - 1][ord(uci_move[0]) - ord('a')] = 1  # from
        dpos[int(uci_move[3]) - 1][ord(uci_move[2]) - ord('a')] = 1  # to
        if self.agent is not None:
            self.agent.uci_move(uci_move)
            self.agent.set_led(dpos)

    def light_square_on_revelation(self, square: str):
        logger.debug('turn on LEDs - square: %s', square)
        dpos = [[0 for _ in range(8)] for _ in range(8)]
        dpos[int(square[1]) - 1][ord(square[0]) - ord('a')] = 1
        if self.agent is not None:
            self.agent.set_led(dpos)

    def clear_light_on_revelation(self):
        logger.debug('turn LEDs off')
        if self.agent is not None:
            self.agent.set_led_off()

    def _process_incoming_board_forever(self):
        result = {}
        wait_counter = 0
        waitchars = ['/', '-', '\\', '|']
        while 'cmd' not in result or (result['cmd'] == 'agent_state' and result['state'] == 'offline'):
            try:
                result = self.appque.get(block=False)
            except queue.Empty:
                pass
            bwait = waitchars[wait_counter]
            text = self._display_text('no Certabo e-Board' + bwait, 'Certabo' + bwait, 'Certabo' + bwait, bwait)
            DisplayMsg.show(Message.DGT_NO_EBOARD_ERROR(text=text))
            wait_counter = (wait_counter + 1) % len(waitchars)
            time.sleep(1.0)

        if result['state'] != 'offline':
            logger.info('incoming_board ready')

        self._process_after_connection()

    def _process_after_connection(self):
        while True:
            if self.agent is not None:
                try:
                    result = self.appque.get(block=False)
                    if 'cmd' in result and result['cmd'] == 'agent_state' and 'state' in result and 'message' in result:
                        if result['state'] == 'offline':
                            text = self._display_text(result['message'], result['message'], 'no/', 'Board')
                        else:
                            text = Dgt.DISPLAY_TIME(force=True, wait=True, devs={'ser', 'i2c', 'web'})
                        DisplayMsg.show(Message.DGT_NO_EBOARD_ERROR(text=text))
                    elif 'cmd' in result and result['cmd'] == 'raw_board_position' and 'fen' in result:
                        fen = result['fen'].split(' ')[0]
                        DisplayMsg.show(Message.DGT_FEN(fen=fen, raw=True))
                    elif 'cmd' in result and result['cmd'] == 'request_promotion_dialog' and 'move' in result:
                        DisplayMsg.show(Message.PROMOTION_DIALOG(move=result['move']))
                except queue.Empty:
                    pass

            time.sleep(0.1)

    def _connect(self):
        logger.info('connecting to board')
        self.agent = CertaboAgent(self.appque)

    def set_text_rp(self, text: bytes, beep: int):
        return True

    def _display_text(self, web, large, medium, small):
        return Dgt.DISPLAY_TEXT(web_text=web, large_text=large, medium_text=medium, small_text=small,
                                wait=True, beep=False, maxtime=0.1, devs={'i2c', 'web'})

    def run(self):
        connect_thread = Thread(target=self._connect)
        connect_thread.setDaemon(True)
        connect_thread.start()
        incoming_board_thread = Thread(target=self._process_incoming_board_forever)
        incoming_board_thread.setDaemon(True)
        incoming_board_thread.start()

    def set_text_xl(self, text: str, beep: int, left_icons=ClockIcons.NONE, right_icons=ClockIcons.NONE):
        pass

    def set_text_3k(self, text: bytes, beep: int):
        pass

    def set_and_run(self, lr: int, lh: int, lm: int, ls: int, rr: int, rh: int, rm: int, rs: int):
        pass

    def end_text(self):
        pass

    def promotion_done(self, uci_move: str):
        self.agent.promotion_done(uci_move)
