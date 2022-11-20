from math import cos, sin, pi

from laserdock.laserdock import LaserDock
from laserdock.utils import float_to_laserdock_xy


class CircleBuffer(object):
    def __init__(self, circle_steps):
        self._current_position = 0
        self._circle_steps = circle_steps
        self._buffer_elements = circle_steps * 2
        self._buffer = self._buffer_elements * [0]
        step_f = 2.0 * pi / circle_steps

        for i in range(0, circle_steps, 2):
            self._buffer[i * 2] = float_to_laserdock_xy(cos(i * step_f))
            self._buffer[i * 2 + 1] = float_to_laserdock_xy(sin(i * step_f))

    def fill_samples(self, samples_per_packet=64):
        samples = []
        for counter in range(0, samples_per_packet):
            samples.append({
                'x': self._buffer[2 * self._current_position],
                'y': self._buffer[2 * self._current_position + 1],
                'r': 100,
                'g': 0,
                'b': 100
            })
            self._current_position += 1
            if self._current_position >= self._circle_steps:
                self._current_position = 0
        return samples


if __name__ == '__main__':
    LD = LaserDock()
    buffer = CircleBuffer(circle_steps=3000)
    samples_per_pkt = 64
    while True:
        try:
            packet_samples = buffer.fill_samples(samples_per_packet=samples_per_pkt)
            LD.packet_samples = packet_samples
            LD.send_samples()
        except KeyboardInterrupt:
            print('\ninterrupt!')
            break
    LD.disable_output()
