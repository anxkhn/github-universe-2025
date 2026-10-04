"""PIO envelope capture and replay through MonaOS's carrier generator."""
# Ruff cannot resolve instruction names injected by the PIO assembler.
# ruff: noqa: F821

from array import array
import time
import rp2
from machine import Pin
from aye_arr.pulse.send import PulseSender
import board

MAX_EDGES = 4095


@rp2.asm_pio(fifo_join=rp2.PIO.JOIN_RX)
def envelope():
    wait(1, pin, 0)
    wait(0, pin, 0)
    label("mark")
    mov(x, invert(null))
    label("mark_loop")
    jmp(pin, "mark_end")
    jmp(x_dec, "mark_loop")
    label("mark_end")
    mov(isr, invert(x))
    push()
    irq(rel(0))
    mov(x, invert(null))
    label("space_loop")
    jmp(pin, "space_more")
    jmp("space_end")
    label("space_more")
    jmp(x_dec, "space_loop")
    label("space_end")
    mov(isr, invert(x))
    push()
    irq(rel(0))
    jmp("mark")


class Infrared:
    def __init__(self):
        self.buffer = array("I", [0] * MAX_EDGES)
        self.count = 0
        self.overflow = False
        self.last_edge = 0
        self.receiver = rp2.StateMachine(
            0,
            envelope,
            freq=2000000,
            in_base=Pin(board.IR_RX, Pin.IN, Pin.PULL_UP),
            jmp_pin=board.IR_RX,
        )
        self.sender = None

    def _receive(self, sm):
        while sm.rx_fifo():
            duration = sm.get()
            if self.count < MAX_EDGES:
                self.buffer[self.count] = duration + 5
                self.count += 1
                self.last_edge = time.ticks_us()
            else:
                self.overflow = True
                sm.active(0)

    def start(self):
        self.stop()
        self.count = 0
        self.overflow = False
        self.receiver.restart()
        while self.receiver.rx_fifo():
            self.receiver.get()
        self.receiver.irq(self._receive, hard=True)
        self.receiver.active(1)

    def stop(self):
        self.receiver.active(0)
        self.receiver.irq(None)

    def finish(self):
        self.stop()
        if self.overflow:
            raise ValueError("Signal too long")
        # A complete envelope ends with a mark. A trailing space means the next
        # mark has started but not finished; do not save a truncated packet.
        if self.count < 15 or self.count % 2 == 0:
            raise ValueError("Incomplete signal")
        return list(self.buffer[: self.count])

    def send(self, timings, carrier):
        self.stop()
        self.sender = PulseSender(board.IR_TX, 0, 1, carrier)
        try:
            self.sender.start()
            for index in range(0, len(timings), 2):
                mark = timings[index]
                space = timings[index + 1] if index + 1 < len(timings) else 15000
                self.sender.send(mark, min(space, 50000))
                if space > 50000:
                    self.sender.wait_for_send()
                    time.sleep_us(space - 50000)
            self.sender.wait_for_send()
        finally:
            self.sender.stop()
            Pin(board.IR_TX, Pin.OUT, value=0)

    def close(self):
        self.stop()
        if self.sender:
            self.sender.stop()
        rp2.PIO(0).remove_program(envelope)
