#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Python wrapper around the SoX library.
This module requires that SoX is installed.
"""

from __future__ import print_function

import os
import csv

import logging
import os
import tempfile as tmp
import subprocess

logging.basicConfig(level=logging.DEBUG)

COMBINE_VALS = [
    'concatenate', 'merge', 'mix', 'mix-power', 'multiply', 'sequence', False
]

VERBOSITY_VALS = [0, 1, 2, 3, 4]


class Transformer(object):
    def __init__(self, input_filepath, output_filepath):
        self.globals = Globals().globals
        self.input_filepath = input_filepath
        self.output_filepath = output_filepath
        self.input_format = []
        self.output_format = []
        self.effects = []
        self.effects_log = []

    def build(self):
        """ Executes SoX. """
        args = []
        args.extend(self.globals)
        args.extend(self.input_format)
        args.append(self.input_filepath)
        args.extend(self.output_format)
        args.append(self.output_filepath)
        args.extend(self.effects)

        status = sox(args)
        if status is False:
            raise SoxError
        else:
            logging.info(
                "Created {} with effects: {}".format(
                    self.output_filepath,
                    " ".join(self.effects_log)
                )
            )

    def allpass(self):
        raise NotImplementedError

    def band(self):
        raise NotImplementedError

    def bandpass(self):
        raise NotImplementedError

    def bandreject(self):
        raise NotImplementedError

    def bass(self):
        raise NotImplementedError

    def bend(self):
        raise NotImplementedError

    def biquad(self):
        raise NotImplementedError

    def channels(self):
        raise NotImplementedError

    def chorus(self):
        raise NotImplementedError

    def compand(self):
        raise NotImplementedError

    def contrast(self):
        raise NotImplementedError

    def convert(self, samplerate=None, channels=None, bitdepth=None):
        """Converts output audio to the specified format.

        Parameters
        ----------
        samplerate : float, default=None
            Desired samplerate. If None, defaults to the same as input.
        channels : int, default=None
            Desired channels. If None, defaults to the same as input.
        bitdepth : int, default=None
            Desired bitdepth. If None, defaults to the same as input.

        """
        if bitdepth:
            assert bitdepth in [8, 16, 24, 32, 64]
            self.output_format.extend(['-b', '{}'.format(bitdepth)])
        if channels:
            self.output_format.extend(['-c', '{}'.format(channels)])
        if samplerate:
            self.rate(samplerate)

    def dcshift(self):
        raise NotImplementedError

    def deemph(self):
        raise NotImplementedError

    def delay(self):
        raise NotImplementedError

    def dither(self):
        raise NotImplementedError

    def downsample(self):
        raise NotImplementedError

    def earwax(self):
        raise NotImplementedError

    def echo(self):
        raise NotImplementedError

    def echos(self):
        raise NotImplementedError

    def equalizer(self):
        raise NotImplementedError

    def fade(self, fade_in_len=0, fade_out_len=0, fade_shape='q'):
        """Add a fade in and/or fade out to an audio file.
        Default fade shape is 1/4 sine wave.

        Parameters
        ----------
        fade_in_len: float
            Length of fade-in (seconds). If fade_in_len = 0,
            no fade in is applied.
        fade_out_len: float
            Length of fade-out (seconds). If fade_out_len = 0,
            no fade in is applied.
        fade_shape: str
            Shape of fade. Must be one of
             * 'q' for quarter sine (default),
             * 'h' for half sine,
             * 't' for linear,
             * 'l' for logarithmic
             * 'p' for inverted parabola.

        """
        fade_shapes = ['q', 'h', 't', 'l', 'p']
        assert fade_shape in fade_shapes, "Invalid fade shape."
        assert fade_in_len >= 0, "fade_in_len must be nonnegative."
        assert fade_out_len >= 0, "fade_out_len must be nonnegative."
        effect_args = [
            'fade', str(fade_shape), str(fade_in_len),
            '0', str(fade_out_len)
        ]
        self.effects.extend(effect_args)
        self.effects_log.append('fade')


    def fir(self):
        raise NotImplementedError

    def flanger(self):
        raise NotImplementedError

    def gain(self):
        raise NotImplementedError

    def highpass(self):
        raise NotImplementedError

    def lowpass(self):
        raise NotImplementedError

    def hilbert(self):
        raise NotImplementedError

    def loudness(self):
        raise NotImplementedError

    def mcompand(self):
        raise NotImplementedError

    def noisered(self):
        raise NotImplementedError

    def norm(self, db_level=-3):
        """Normalize an audio file to a particular db level.

        Parameters
        ----------
        db_level : float, default=-3
            Output volume (db)

        """
        effect_args = [
            'norm',
            '{}'.format(db_level)
        ]
        self.effects.extend(effect_args)
        self.effects_log.append('norm')

    def oops(self):
        raise NotImplementedError

    def overdrive(self):
        raise NotImplementedError

    def pad(self, start_duration=0, end_duration=0):
        """Add silence to the beginning or end of a file.
        Calling this with the default arguments has no effect.

        Parameters
        ----------
        start_duration : float
            Number of seconds of silence to add to beginning.
        end_duration : float
            Number of seconds of silence to add to end.

        """
        assert start_duration >= 0, "Start duration must be positive."
        assert end_duration >= 0, "End duration must be positive."
        effect_args = [
            'pad',
            '{}'.format(start_duration),
            '{}'.format(end_duration)
        ]
        self.effects.extend(effect_args)
        self.effects_log.append('pad')

    def phaser(self):
        raise NotImplementedError

    def pitch(self):
        raise NotImplementedError

    def rate(self, samplerate, quality='h'):
        """Change the audio sampling rate (i.e. resample the audio) to any
        given `samplerate`. Better the resampling quality = slower runtime.

        Parameters
        ----------
        samplerate : float
            Desired sample rate.
        quality: str
            Resampling quality. One of:
             * q : Quick - very low quality,
             * l : Low,
             * m : Medium,
             * h : High (default),
             * v : Very high
        silence_threshold: float
            Silence threshold as percentage of maximum sample amplitude.
        min_silence_duration: float
            The minimum ammount of time in seconds required for a region to be
            considered non-silent.
        buffer_around_silence: bool
            If True, leaves a buffer of min_silence_duration around removed
            silent regions.

        """
        assert samplerate > 0, "Samplerate must be a positive number."
        assert quality in ['q', 'l', 'm', 'h', 'v'], "Invalid quality."
        effect_args = [
            'rate',
            '-{}'.format(quality),
            '{}'.format(samplerate)
        ]
        self.effects.extend(effect_args)
        self.effects_log.append('rate')

    def repeat(self):
        raise NotImplementedError

    def reverb(self):
        raise NotImplementedError

    def reverse(self):
        raise NotImplementedError

    def silence(self, location=0, silence_threshold=0.01,
                min_silence_duration=0.1, buffer_around_silence=False):
        """Removes silent regions from an audio file.

        Parameters
        ----------
        location: int
            Where to remove silence. One of:
             * 0 to remove silence throughout the file (default),
             * 1 to remove silence from the beginning,
             * -1 to remove silence from the end,
        silence_threshold: float
            Silence threshold as percentage of maximum sample amplitude.
        min_silence_duration: float
            The minimum ammount of time in seconds required for a region to be
            considered non-silent.
        buffer_around_silence: bool
            If True, leaves a buffer of min_silence_duration around removed
            silent regions.

        """
        effect_args = []

        if location == -1:
            effect_args.append('reverse')

        if buffer_around_silence:
            effect_args.extend(['silence', '-l'])
        else:
            effect_args.append('silence')

        effect_args.extend([
            '1',
            '{}'.format(min_silence_duration),
            '{}%'.format(silence_threshold)
        ])

        if location == 0:
            effect_args.extend([
                '-1',
                '{}'.format(min_silence_duration),
                '{}%'.format(silence_threshold)
            ])

        if location == -1:
            effect_args.append('reverse')

        self.effects.extend(effect_args)
        self.effects_log.append('silence')

    def sinc(self):
        raise NotImplementedError

    def speed(self):
        raise NotImplementedError

    def splice(self):
        raise NotImplementedError

    def swap(self):
        raise NotImplementedError

    def stretch(self):
        raise NotImplementedError

    def tempo(self):
        raise NotImplementedError

    def treble(self):
        raise NotImplementedError

    def tremolo(self):
        raise NotImplementedError

    def trim(self, start_time, end_time):
        """Excerpt a clip from an audio file, given a start and end time.

        Parameters
        ----------
        start_time : float
            Start time of the clip (seconds)
        end_time : float
            End time of the clip (seconds)

        """
        assert start_time >= 0, "`start_time` must be positive."
        assert end_time >= 0, "`end_time` must be positive."
        effect_args = [
            'trim',
            '{}'.format(start_time),
            '{}'.format(end_time - start_time)
        ]

        self.effects.extend(effect_args)
        self.effects_log.append('trim')

    def upsample(self):
        raise NotImplementedError

    def vad(self):
        raise NotImplementedError

    def vol(self):
        raise NotImplementedError


class Globals(object):
    """ Class containing global sox arguments """
    def __init__(self, clobber=True, combine=False, dither=False, guard=False,
                 multithread=False, replay_gain=False, verbosity=2):
        self.clobber = self._set_bool(clobber)
        self.combine = self._set_constrainted(combine, COMBINE_VALS)
        self.dither = self._set_bool(dither)
        self.guard = self._set_bool(guard)
        self.multithread = self._set_bool(multithread)
        self.replay_gain = self._set_bool(replay_gain)
        self.verbosity = self._set_constrainted(verbosity, VERBOSITY_VALS)

        self.globals = self._build_globals()

    def _build_globals(self):
        """ Build global command line arguments.
        """
        global_args = []
        if not self.clobber:
            global_args.append('--no-clobber')

        if self.combine is not False:
            global_args.append('--combine')
            global_args.append(self.combine)

        if not self.dither:
            global_args.append('-D')

        if self.guard:
            global_args.append('-G')

        if self.multithread:
            global_args.append('--multi-threaded')

        if self.replay_gain:
            global_args.append('--replay-gain')
            global_args.append('track')

        global_args.append('-V{}'.format(self.verbosity))

        return global_args

    def _set_bool(self, value):
        """ If true, overwrites existing files.
        """
        if isinstance(value, bool):
            return bool(value)
        else:
            raise ValueError('Value must be a boolean.')

    def _set_constrainted(self, value, valid_vals):
        """ Specifies how multiple input files should be combined.
        """
        if value in valid_vals:
            return value
        else:
            raise ValueError(
                'Invalid value for combine. Must be one of False or {}'.format(
                    valid_vals)
            )


def sox(args):
    """Pass an argument list to SoX.

    Parameters
    ----------
    args : iterable
        Argument list for SoX. The first item can, but does not
        need to, be 'sox'.

    Returns:
    --------
    status : bool
        True on success.

    """
    if args[0].lower() != "sox":
        args.insert(0, "sox")
    else:
        args[0] = "sox"

    try:
        logging.info("Executing: %s", " ".join(args))
        process_handle = subprocess.Popen(args, stderr=subprocess.PIPE)
        status = process_handle.wait()
        if process_handle.stdout is not None:
            logging.info(process_handle.stdout)
        return status == 0
    except OSError as error_msg:
        logging.error("OSError: SoX failed! %s", error_msg)
    except TypeError as error_msg:
        logging.error("TypeError: %s", error_msg)
    return False


class SoxError(Exception):
    """Exception to be raised when SoX exits with non-zero status.
    """
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)
