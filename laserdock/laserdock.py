import argparse
import logging
import struct
import time
from usb.core import USBError

import usb.core
import usb.util
from tqdm import tqdm

from laserdock import constants as const

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(prog='laserdock', description='LaserCube control')
parser.add_argument('-d', '--dummy', help='Run without connecting to a real device', action='store_true')
args = parser.parse_args()


def sleep_until(time_to_wake):
    # wait here for time to be ready
    while time.monotonic() < time_to_wake:
        time_to_wait = time_to_wake - time.monotonic()
        # logger.warning(f'sleeping for {sleep_time}')
        time.sleep(min(time_to_wait, 1))  # sleep the minimum of the correct time and 1 second


class LaserDock:
    intensity_differential = const.INTENSITY_DIFFERENTIAL
    intensity_minimum = const.MIN_INTENSITY

    def __init__(self):
        self.packet_samples = []
        if args.dummy:
            print('Running in dummy mode without connecting to a real device')
            self.dev = None
        else:
            self.dev = self.connect()
            self.get_setting(const.COMMAND_MAJOR_FIRMWARE,               'Major Firmware Version')
            self.get_setting(const.COMMAND_MINOR_FIRMWARE,               'Minor Firmware Version')
            self.get_setting(const.COMMAND_GET_MAX_DAC_RATE,             'Max DAC Rate')
            self.get_setting(const.COMMAND_GET_MIN_DAC_VALUE,            'Min DAC Value')
            self.get_setting(const.COMMAND_GET_MAX_DAC_VALUE,            'Max DAC Value')
            self.set_dac_rate(const.FPS)
            self.get_setting(const.COMMAND_GET_DAC_RATE,                 'Current DAC Rate')  # guint32
            self.clear_ringbuffer()
            self.get_setting(const.COMMAND_GET_SAMPLE_ELEMENT_COUNT,     'Get Sample Element Count')
            self.get_setting(const.COMMAND_GET_ISO_PACKET_SAMPLE_COUNT,  'Get ISO Packet Sample Count')
            self.get_setting(const.COMMAND_GET_BULK_PACKET_SAMPLE_COUNT, 'Get Bulk Packet Sample Count')
            self.enable_output()
            self.get_setting(const.COMMAND_GET_OUTPUT_STATE,             'Current Output Status')  # guint8
            self.last_packet_send_time = time.monotonic()

    @staticmethod
    def connect():
        dev = usb.core.find(idVendor=const.LASERDOCK_VENDOR, idProduct=const.LASERDOCK_PRODUCT)
        if dev is None:
            raise ValueError('No LaserDock/LaserCube found')

        c = 1
        for config in dev:
            print('config', c)
            print('Interfaces', config.bNumInterfaces)
            for i in range(config.bNumInterfaces):
                if dev.is_kernel_driver_active(i):
                    print('detaching kernel driver')
                    dev.detach_kernel_driver(i)
                print(f'Interface #{i}')
            c += 1

        # set the active configuration. With no arguments, the first configuration will be the active one
        dev.set_configuration()
        """
        def find_first_out_endpoint(endpoint):
            return usb.util.endpoint_direction(endpoint.bEndpointAddress) == usb.util.ENDPOINT_OUT

        for cfg in dev:
            print(f'Configuration #: {cfg.bConfigurationValue}')
            for intf in cfg:
                print(f'\tInterface: {intf.bInterfaceNumber}, AltInterface: {intf.bAlternateSetting}')
                for ep in intf:
                    print(f'\t\tEndpoint Address: {ep.bEndpointAddress}')

        # get an endpoint instance
        cfg = dev.get_active_configuration()

        intf = cfg[(0, 0)]

        ep = usb.util.find_descriptor(intf,
                                      custom_match=find_first_out_endpoint)  # match the first OUT endpoint
        assert ep is not None
        """
        return dev

    def disconnect(self):
        usb.util.dispose_resources(self.dev)
        self.dev = None

    def write_ctrl(self, msg):
        self.dev[0][(0, 0)][0].write(msg)

    def reconnect(self):
        logger.warning('Lost Connectivity to USB device... attempting reconnect')
        self.dev = None
        while self.dev is None:
            try:
                self.dev = self.connect()
            except Exception as exc_data:
                logger.warning(f'Exception trying to reconnect: {type(exc_data)} {exc_data}')
            else:
                continue  # or break
            time.sleep(5)

    def write_bulk(self, msg):
        try:
            self.dev[0][(1, 0)][0].write(msg)
        except AttributeError:
            if not args.dummy:
                self.reconnect()
        except Exception as e:
            if self.dev is not None:
                print(f'Uncaught exception in write_bulk: {e}')

    def read_ctrl(self):
        packet_size = self.dev[0][(0, 0)][1].wMaxPacketSize
        response = self.dev[0][(0, 0)][1].read(packet_size)
        return response

    def enable_output(self):
        print('Enabling output')
        self.write_ctrl(const.COMMAND_ENABLE_OUTPUT + b'\x01')
        response = self.read_ctrl()[:4]
        command, response = struct.unpack('<HH', response)
        if command != ord(const.COMMAND_ENABLE_OUTPUT):
            raise Exception('Bad response')
        print(f'Response from enabling output: {response}')

    def disable_output(self):
        if self.dev:
            self.write_ctrl(b'\x80\x00')
            print(self.read_ctrl())

    def get_setting(self, cmd, label):
        self.write_ctrl(cmd)
        response = self.read_ctrl()[:4]
        command, response = struct.unpack('<HH', response)
        if command != ord(cmd):
            raise Exception('Bad response')
        print(f'{label}: {response}')

    def set_dac_rate(self, rate):
        """suint32(d->devh_ctl, 0x82, rate);"""
        print(f'Setting DAC Rate to {rate}')
        self.write_ctrl(const.COMMAND_SET_DAC_RATE + struct.pack('<I', rate))
        response = self.read_ctrl()[:4]
        command, response = struct.unpack('<HH', response)
        if command != ord(const.COMMAND_SET_DAC_RATE):
            raise Exception('Bad response')
        print(f'Response after setting DAC rate: {response}')

    def get_ringbuffer_sample_count(self):
        self.write_ctrl(const.COMMAND_GET_RINGBUFFER_SAMPLE_COUNT)
        print(self.read_ctrl())

    def get_ringbuffer_empty_sample_count(self):
        self.write_ctrl(const.COMMAND_GET_RINGBUFFER_EMPTY_SAMPLE_COUNT)
        print(self.read_ctrl())

    def clear_ringbuffer(self):
        """suint8"""
        print('Clearing ringbuffer')
        self.write_ctrl(const.COMMAND_SET_RINGBUFFER + b'\x00')
        response = self.read_ctrl()[:4]
        command, response = struct.unpack('<HH', response)
        if command != ord(const.COMMAND_SET_RINGBUFFER):
            raise Exception('Bad response')
        print(f'Response from set ringbuffer command: {response}')

    def send_samples(self, packet_samples=None):
        # this one uses the bulk transfer
        # logger.warning('sending samples')
        if (packet_samples):
            self.packet_samples = packet_samples

        msg = b''
        for sample in self.packet_samples:
            msg += struct.pack('<B', sample['r'])
            msg += struct.pack('<B', sample['g'])
            msg += struct.pack('<B', sample['b'])
            msg += struct.pack('<B', 0)
            msg += struct.pack('<H', sample['x'])
            msg += struct.pack('<H', sample['y'])
        try:
            self.write_bulk(msg)
        except (USBError, ValueError):
            self.reconnect()
        self.last_packet_send_time = time.monotonic()
        self.packet_samples = []

    def potentially_send_samples(self):
        if len(self.packet_samples) == const.SAMPLES_PER_PACKET:
            sleep_until(self.last_packet_send_time + const.SAMPLES_PER_PACKET / const.FPS)
            self.send_samples()

    def burn_sample(self, sample):
        intensity = int(sample['intensity'] * self.intensity_differential * const.FPS + self.intensity_minimum * const.FPS)
        # logger.warning(f'intensity is {intensity}, sample is: {sample}')
        for repeat_entry in range(intensity):
            self.packet_samples.append(sample)
            self.potentially_send_samples()
