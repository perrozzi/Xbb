#!/usr/bin/env python

import argparse
import os
import sys

import myutils
import utils


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
    print 'Configuration Directory: {}\n'.format(config_dir)
    print 'Sample Name: {}\n'.format(sample_name)

    prep_out, samples_info = parse_path_config(config_dir)
    print 'Preparation Directory: {}\n'.format(prep_out)
    print 'Sample Configuration File: {}\n'.format(samples_info)

    LFN_dir, samples = parse_sample_config(samples_info)
    print 'LFN Directory: {}\n'.format(LFN_dir)

    for sample in samples:
        if (sample.name != sample_name) or sample.subsample:
            continue

        print 'Sample to Prepare: {}\n'.format(sample.name)

        LFN_path = os.path.join(config_dir, LFN_dir)
        print 'LFN File Path: {}\n'.format(LFN_path)

        utils.TreeCopier(sample.identifier, LFN_path, 'xrootd-cms.infn.it', sample.addtreecut, prep_out, sample.prefix)

if __name__ == '__main__':

    status = main()
    sys.exit(status)

