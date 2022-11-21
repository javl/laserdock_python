from math import cos, sin, tau
import sys

from laserdock.laserdock import LaserDock
from laserdock.utils import to_laserdock_coord, packet_to_image
from PIL import Image, ImageDraw


class CircleBuffer(object):
    def __init__(self, circle_steps):
        self._current_position = 0
        self._circle_steps = circle_steps
        self._buffer_elements = circle_steps
        self._buffer = self._buffer_elements * [(0, 0)]
        # self._buffer = 2 * [(0, 0)]
        step_f = tau / circle_steps

        for i in range(circle_steps):
            # if i < 50:
            # self._buffer[i] = to_laserdock_coord(cos(i * step_f) * 0.5, sin(i * step_f) * 0.5)
            x = -1 + 2 * i / circle_steps
            y = 0
            self._buffer[i] = to_laserdock_coord(x, y)

        # try:
        #     im = Image.open('circle.png')
        # except IOError:
        #     im = Image.new('RGB', (4096, 4096), 'white')
        # draw = ImageDraw.Draw(im)

        # for pos in self._buffer[:100]:
        #     draw.ellipse((pos[0]-50, pos[1]-50, pos[0]+50, pos[1]+50), fill='green')
        # im.save('circle.png')
        # exit()
    def fill_samples(self, samples_per_packet=64):
        samples = []
        for __ in range(0, samples_per_packet):
            samples.append({
                'x': self._buffer[self._current_position][0],
                'y': self._buffer[self._current_position][1],
                'r': 1,
                'g': 0,
                'b': 0
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
            # packet_to_image('circle.png', packet_samples)
            # sys.exit()
            LD.send_samples()
        except KeyboardInterrupt:
            LD.disable_output()
            sys.exit('interrupted')
    LD.disable_output()
