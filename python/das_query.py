import argparse
import os
import re
import subprocess as sp
import sys

import myutils


def parse_command_line(argv):

    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser()

    parser.add_argument(
        'sample_config',
        help = 'The path to the sample configuration file, e.g. "LucaZllHbb13TeVconfig/samples_nosplit.ini".'
    )

    parser.add_argument(
        '--outdir',
        default = '',
        help = 'The output directory to store the file query results. The default is the directory storing the sample configuration file.'
    )

    return parser.parse_args(argv)

def parse_sample_config(sample_config):
    """
    Return the query options and a list of primary dataset names.
    """
    parser = myutils.BetterConfigParser()
    parser.read(sample_config)

    # The first two section headers, "General" and "Samples_running", are skipped.
    sections = parser.sections()
    primary_datasets = list(sections[2:])

    processed_dataset = parser.get('General', 'processed_dataset')
    if not processed_dataset:
        process_dataset = '*'

    data_tier = parser.get('General', 'data_tier')
    if not data_tier:
        data_tier = '*'

    dbs_instance = parser.get('General', 'dbs_instance')
    query_filter = parser.get('General', 'query_filter')

    return primary_datasets, processed_dataset, data_tier, dbs_instance, query_filter

def main(argv=None):

    args = parse_command_line(argv)

    primary_datasets, processed_dataset, data_tier, dbs_instance, query_filter = parse_sample_config(args.sample_config)

    for primary_dataset in primary_datasets:

        # Query DAS to find the dataset(s).
        dataset_query = 'dataset=/{}/{}/{}'.format(primary_dataset, processed_dataset, data_tier)
        if dbs_instance:
            dataset_query += ' instance={}'.format(dbs_instance)

        try:
            dataset_query_output = sp.check_output(['python', 'das_client.py', '--query', dataset_query, '--limit', '0'])
        except sp.CalledProcessError as e:
            print '{0}\nThe dataset query failed for "{1}".\n'.format(e, primary_dataset)
            continue

        if query_filter:
            pattern = re.compile(query_filter)
            datasets = [line for line in dataset_query_output.splitlines() if re.search(query_filter, line)]
        else:
            datasets = dataset_query_output.splitlines()

        if not datasets:
            print 'No datasets were found for "{}".\n'.format(primary_dataset)
            continue

        # Query DAS to find each dataset's files and save their logical file names (LFNs).
        LFNs = []

        for dataset in datasets:

            file_query = 'file dataset={}'.format(dataset)
            if dbs_instance:
                file_query += ' instance={}'.format(dbs_instance)

            try:
                file_query_output = sp.check_output(['python', 'das_client.py', '--query', file_query, '--limit', '0'])
            except sp.CalledProcessError as e:
                print '{0}\nThe file query failed for "{1}".\n'.format(e, primary_dataset)
                continue
            else:
                LFNs.extend(file_query_output.splitlines())

        if not LFNs:
            print 'No files were found for "{}".\n'.format(primary_dataset)
            continue

        # Create the output directory.
        outdir = os.path.join(os.path.dirname(args.sample_config), args.outdir)

        try:
            os.makedirs(outdir)
        except OSError:
            if not os.path.isdir(outdir):
                raise

        # Write the LFNs to a file.
        outpath = os.path.join(outdir, primary_dataset + '.txt')

        try:
            # Retrieve the LFNs from an existing file.
            with open(outpath, 'r') as outfile:
                LFNs_old = [line.strip() for line in outfile.readlines() if not line.isspace()]

            with open(outpath, 'w') as outfile:
                # Rewrite the contents to remove any empty lines (e.g. inserted by hand).
                outfile.writelines(LFN + '\n' for LFN in LFNs_old)
                # If the old LFNs do not match those returned by the query, the new
                # LFNs are appended in git merge conflict style for manual resolution.
                if LFNs_old == LFNs:
                    print 'The file "{}" already exists, with content matching the query result.\n'.format(outpath)
                else:
                    print 'The file "{}" already exists, but its content does not match the query result.'.format(outpath)
                    outfile.seek(0)
                    outfile.write('<<<<<<< Old LFNs\n')
                    outfile.seek(0, 2)
                    outfile.write('=======\n')
                    for LFN in LFNs:
                        outfile.write(LFN + '\n')
                    outfile.write('>>>>>>> New LFNs\n')
                    print 'The new LFNs have been appended to the same file for manual resolution.\n'
        except:
            # If the file exists but is inaccessible, raise the exception.
            if os.path.isfile(outpath):
                raise
            # If the file does not exist, create it and write the LFNs.
            with open(outpath, 'w') as outfile:
                for LFN in LFNs:
                    outfile.write(LFN + '\n')
            print 'The LFNs were written to "{}".\n'.format(outpath)

if __name__ == '__main__':

    status = main()
    sys.exit(status)

