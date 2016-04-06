import hashlib
import logging
import multiprocessing as mp
import os
import Queue

import ROOT

from context_managers import open_root


ROOT.gROOT.SetBatch(True)

class TreeCopier(object):
    """
    Skim and copy the files of a sample according to a list of LFNs.

    Parameters
    ----------
    primary_dataset : str
                      The primary dataset name of the sample.
    LFN_path        : str
                      The path to the directory storing the LFN files.
    xrd_redirector  : str
                      The XRootD redirector prepended to the LFNs.
                      Global  : cms-xrd-global.cern.ch
                      EU/Asia : xrootd-cms.infn.it
                      US      : cmsxrootd.fnal.gov
                      The default is the global redirector.
    cut             : str
                      The selection cut used to skim the sample.
    prep_out        : str
                      The local output directory storing the prepared samples.
    prefix          : str
                      The prefix for the sample subdirectory and merged file names.
    merge           : bool
                      Flag whether the files should be merged. The default is True.
    """
    def __init__(self, primary_dataset='', LFN_path='', xrd_redirector='cms-xrd-global.cern.ch', cut='', prep_out='', prefix='', merge=True):

        self.logger = logging.getLogger('TreeCopier')

        # Parse the file for the list of LFNs.
        LFN_file = os.path.join(LFN_path, primary_dataset + '.txt')
        with open(LFN_file, 'r') as infile:
            self.LFNs = [line.strip() for line in infile.readlines() if not line.isspace()]
        self.logger.debug('The LFN list is %s', self.LFNs)

        # Create the output directory for the copied files.
        self.copy_dir = os.path.join(prep_out, prefix + primary_dataset)
        try:
            os.makedirs(self.copy_dir)
            self.logger.info('The copy destination is %s', self.copy_dir)
        except OSError:
            if not os.path.isdir(self.copy_dir):
                raise

        # Set the remaining attributes.
        self.xrd_redirector = xrd_redirector
        self.logger.info('Using XRootD redirector %s', self.xrd_redirector)

        self.cut = cut
        self.logger.info('The skimming cut is %s', self.cut)

        # Copy the files, merging the if requested.
        while self.LFNs:
            self._copy_files()
        if merge:
            self._merge_files()

    def _copy_files(self):
        """
        Copy the files in parallel, managing the processes and queues.
        """
        # Fill a task queue with the LFNs.
        task_queue = mp.Queue()
        for LFN in self.LFNs:
            task_queue.put(LFN)

        # Prepare a result queue to receive the LFNs of successful copies.
        result_queue = mp.Queue()

        # Prepare a message queue to receive asynchronous log messages.
        message_queue = mp.Queue()

        # Instantiate the file copy worker processes. There are two less than the maximum number of
        # detected CPUs to account for the main calling process and the message listener process.
        workers = [
            mp.Process(target = self._copy_file_worker, args = (task_queue, result_queue, message_queue))
            for cpu in xrange(mp.cpu_count() - 2)
        ]

        # Instantiate and start the message listener process.
        listener = mp.Process(target = self._message_listener, args = (message_queue,))
        listener.start()

        # For each worker process, queue a sentinel value and start running.
        for worker in workers:
            task_queue.put(None)
            worker.start()

        # Ensure the calling process waits for the workers to terminate.
        for worker in workers:
            worker.join()

        # Ensure the calling process waits for the listener to terminate.
        message_queue.put(None)
        listener.join()

        # Remove the LFNs returned through the result queue.
        result_queue.put(None)
        for result in iter(result_queue.get, None):
            self.LFNs.remove(result)

    def _copy_file_worker(self, task_queue, result_queue, message_queue):

        # Consume LFNs from the task queue until the sentinel value is received.
        for LFN in iter(task_queue.get, None):

            # Form the input file url.
            input_url = 'root://{0}//{1}'.format(self.xrd_redirector, LFN)
            # Form the output file path. The file name is a hash digest of the bare LFN.
            output_path = os.path.join(self.copy_dir, hashlib.sha256(LFN).hexdigest() + '.root')

            with open_root(input_url, 'r') as infile, open_root(output_path, 'w'):
                # Copy any objects present besides the tree.
                for key in infile.GetListOfKeys():
                    if key.GetName() == 'tree':
                        continue
                    obj = key.ReadObj()
                    obj.Write()
                # Copy the tree with the skimming cut.
                intree = infile.Get('tree')
                outtree = intree.CopyTree(self.cut)
                n_in = intree.GetEntriesFast()
                n_out = outtree.GetEntriesFast()
                outtree.Write()

            # Check whether the output file is corrupted. If it passes all tests, return the LFN in the result queue.
            try:
                with open_root(output_path, 'r') as outfile:
                    if not outfile.GetNkeys():
                        msg = '[PID {0!s}] Copy Failed: No TKeys were written to the output file.\n{1}'.format(os.getpid(), LFN)
                    elif outfile.TestBit(ROOT.TFile.kRecovered):
                        msg = '[PID {0!s}] Copy Failed: The kRecovered bit is set for the output file.\n{1}'.format(os.getpid(), LFN)
                    elif outfile.IsZombie():
                        msg = '[PID {0!s}] Copy Failed: The kZombie bit is set for the output file.\n{1}'.format(os.getpid(), LFN)
                    else:
                        msg = '[PID {0!s}] Copy Successful: Selected {1!s} out of {2!s} entries.\n{3}'.format(os.getpid(), n_out, n_in, LFN)
                        result_queue.put(LFN)
            except IOError:
                msg = '[PID {0!s}] Copy Failed: Unable to open the output file for error checking.\n{1}'.format(os.getpid(), LFN)

            message_queue.put(msg)

    def _message_listener(self, message_queue):
        while True:
            try:
                message = message_queue.get_nowait()
                if message is None:
                    break
                self.logger.info(message)
            except Queue.Empty:
                pass

    def _merge_files(self):

        merge_path = self.copy_dir + '.root'
        self.logger.debug('Merging the files to %s', merge_path)

        # Set the first positional argument, isLocal, to false to prevent the
        # files to merge from being copied to a temporary directory, as they
        # are already available locally. PyROOT doesn't support keyword args.
        merge_file = ROOT.TFileMerger(ROOT.kFALSE)
        merge_file.OutputFile(merge_path, 'RECREATE')

        for file_name in os.listdir(self.copy_dir):
            merge_file.AddFile(os.path.abspath(os.path.join(self.copy_dir, file_name)))

        merge_file.Merge()

