#!/usr/bin/env python

import argparse
import logging
import os
import sys

import myutils
import utils


# Configure logging.
logging.basicConfig(
    format = '%(asctime)s - %(name)s - %(levelname)s\n%(message)s\n',
    datefmt = '%d-%b-%Y %H:%M:%S',
    level = logging.DEBUG,
)

logger = logging.getLogger('prep')

def parse_command_line(argv):

    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser()

    parser.add_argument(
        'config_dir',
        help = 'The path to the configuration directory, e.g. "SeanZvvHbb13TeVconfig".'
    )

    parser.add_argument(
        'sample_name',
        help = 'The name of the sample to prepare.'
    )

    args = parser.parse_args(argv)

    return args.config_dir, args.sample_name

def parse_path_config(config):

    parser = myutils.BetterConfigParser()
    parser.read(os.path.join(config, 'paths.ini'))

    prep_out = parser.get('Directories', 'PREPout')
    samples_info = parser.get('Directories', 'samplesinfo')

    return prep_out, samples_info

def parse_sample_config(samples_info):

    parser = myutils.BetterConfigParser()
    parser.read(samples_info)

    LFN_dir = parser.get('General', 'LFN_dir')
    samples = myutils.ParseInfo(samples_info, '')

    return LFN_dir, samples

def main(argv=None):

    config_dir, sample_name = parse_command_line(argv)
    logger.debug('Configuration Directory: %s', config_dir)
    logger.debug('Sample Name: %s', sample_name)

    prep_out, samples_info = parse_path_config(config_dir)
    logger.debug('Preparation Directory: %s', prep_out)
    logger.debug('Sample Configuration File: %s', samples_info)

    LFN_dir, samples = parse_sample_config(samples_info)
    logger.debug('LFN Directory: %s', LFN_dir)

    for sample in samples:
        if (sample.name != sample_name) or sample.subsample:
            continue

        logger.info('Sample to Prepare: %s', sample.name)

        LFN_path = os.path.join(config_dir, LFN_dir)
        logger.debug('LFN File Path: %s', LFN_path)

        utils.TreeCopier(sample.identifier, LFN_path, 'xrootd-cms.infn.it', sample.addtreecut, prep_out, sample.prefix)

if __name__ == '__main__':

    status = main()
    sys.exit(status)

