import logging
import time
import pandas as pd


class LoadLogs:
    """
    Used to store the batch load performance
    """

    def __init__(self, backend):
        self._backend = backend
        columns = ['Cumulative Batch Size', 'Current Batch Size', 'Batch Start Time', 'Batch Finish Time',
                   'Batch Duration in s', 'Cumulative Duration in s']
        self.journal = pd.DataFrame(columns=columns)
        self.journal.name = 'LoadPerformance'
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 160)
        self._last_cumulative_batch_size = 0
        self._last_cumulative_duration = 0

    def add(self, batch_size, batch_start_time, batch_finish_time):
        current_cumulative_batch_size = self._last_cumulative_batch_size + batch_size
        current_duration = batch_finish_time - batch_start_time
        current_cumulative_duration = self._last_cumulative_duration + current_duration
        self.journal.loc[len(self.journal)] = [current_cumulative_batch_size, batch_size, batch_start_time,
                                               batch_finish_time, current_duration, current_cumulative_duration]
        self._last_cumulative_batch_size = current_cumulative_batch_size
        self._last_cumulative_duration = current_cumulative_duration

    def get(self):
        return self.journal

    def stats(self):
        print(self.journal)
        logging.info("Totals of {} records in {} seconds using {} Backend"
                     .format(self._last_cumulative_batch_size, self._last_cumulative_duration, self._backend))

    def dump(self, export_directory):
        if not export_directory.endswith('/'):
            export_directory = export_directory + '/'
        csv_file_name = export_directory + self._backend.name + '_perf_load.csv'
        excel_file_name = export_directory + self._backend.name + '_perf_load.xlsx'
        self.journal.to_csv(csv_file_name, index=True)
        self.journal.to_excel(excel_file_name, index=True)
        logging.debug('Finished exporting {}\'s LOAD performance in csv/xlsx format'.format(self._backend.name))


class ResolvingLogs:
    """
    Used to store the resolving performance, for both: get() and get_lpm()
    """

    def __init__(self, backend, table_name: str, filename_suffix: str):
        self._backend = backend
        columns = ['Count', 'Cumulative Duration in s']
        self.journal = pd.DataFrame(columns=columns)
        self.journal_name = table_name
        self.filename_suffix = filename_suffix
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 160)
        pd.set_option('display.precision', 18)

    def __repr__(self):
        return repr(self.journal)

    def __str__(self):
        return str(self.journal)

    def add(self, count, duration):
        self.journal.loc[len(self.journal)] = [count, duration]

    def clear(self):
        self.journal.drop(self.journal.index, inplace=True)

    def get_df(self):
        return self.journal

    def dump(self, export_directory):
        if not export_directory.endswith('/'):
            export_directory = export_directory + '/'
        csv_file_name = export_directory + self._backend.name + '_perf_' + self.filename_suffix + '.csv'
        excel_file_name = export_directory + self._backend.name + '_perf_' + self.filename_suffix + '.xlsx'
        self.journal.to_csv(csv_file_name, index=True)
        self.journal.to_excel(excel_file_name, index=True)
        logging.debug('Finished exporting {}\'s resolving performance of type {} in csv/xlsx format. File suffix: {}'
                      .format(self._backend.name, self.journal_name, self.filename_suffix))


class CallsLogs:
    """
    Used to measure the get() performance, both positive and negative
    """

    def __init__(self, backend):
        self._backend = backend
        self.longest_prefix_match_counter = 0
        self.adds_counter = 0

    def increment_lpm(self):
        self.longest_prefix_match_counter += 1

    def increment_adds(self):
        self.adds_counter += 1

    def stats(self):
        s = 'Adds Count = {}. LPM Count = {}'.format(self.adds_counter, self.longest_prefix_match_counter)
        return s


class CR:
    def __init__(self):
        trials_columns = ['seq', 'backend_name', 'dataset_size', 'profiler_sleep_time', 'load_batch_size',
                          'resolving_batch_sizes', 'start', 'finish', 'duration', 'total_nodes', 'total_components']
        self.trials = pd.DataFrame(columns=trials_columns)
        self.perf_load = {}
        self.perf_get_positive = {}
        self.perf_get_negative = {}
        self.perf_lpm_positive = {}
        self.perf_lpm_negative = {}
        self.profilers = {}
        self.last_sequence = 0

        self.summary_load = None

    def add_trial(self, backend_name, dataset_size, profiler_sleep_time, load_batch_size, resolving_batch_sizes):
        seq = len(self.trials)
        self.trials.loc[seq] = [seq, backend_name, dataset_size, profiler_sleep_time, load_batch_size,
                                resolving_batch_sizes, time.time(), None, None, None, None]
        self.last_sequence = seq
        return seq

    def finish_trial(self, sequence_number, tn, tc):
        st = self.trials['start'].loc[self.trials['seq'] == sequence_number]
        now = time.time()
        self.trials.loc[self.trials['seq'] == sequence_number, 'finish'] = now
        self.trials.loc[self.trials['seq'] == sequence_number, 'duration'] = now - st
        self.trials.loc[self.trials['seq'] == sequence_number, 'total_nodes'] = tn
        self.trials.loc[self.trials['seq'] == sequence_number, 'total_components'] = tc

    def add_load(self, sequence_number, test_results: pd.DataFrame):
        self.perf_load[sequence_number] = test_results

    def get_load(self, sequence_number):
        return self.perf_load[sequence_number]

    def add_resolve(self, sequence_number, test_type: str, test_results: pd.DataFrame):
        match test_type:
            case 'get_positive':
                self.perf_get_positive[sequence_number] = test_results
            case 'get_negative':
                self.perf_get_negative[sequence_number] = test_results
            case 'lpm_positive':
                self.perf_lpm_positive[sequence_number] = test_results
            case 'lpm_negative':
                self.perf_lpm_negative[sequence_number] = test_results

    def get_resolve_summary(self, sequence_number):
        gp = 'Get Positive: \n' + str(self.perf_get_positive[sequence_number]) + '\n'
        gn = 'Get Negative: \n' + str(self.perf_get_negative[sequence_number]) + '\n'
        lp = 'LPM Positive: \n' + str(self.perf_lpm_positive[sequence_number]) + '\n'
        ln = 'LPM Negative: \n' + str(self.perf_lpm_negative[sequence_number]) + '\n'
        return gp + gn + lp + ln

    def stats(self, level: int):
        print('Performance Consolidated Statistics')
        print('***********************************')
        t = self.trials
        match level:
            # Case 1: Description of what we have in trials
            case 1:
                print(t.to_string(index=False))
            # Case 2: Trial header and the 1st level beneath it
            case 2:
                for index, row in t.iterrows():
                    print(row)
                    print(self.get_load(row['seq']))
                    print(self.get_resolve_summary(row['seq']))

    def export_to_excel(self, export_directory):
        if not export_directory.endswith('/'):
            export_directory = export_directory + '/'
        with pd.ExcelWriter(export_directory + 'cr.xlsx', mode='w') as writer:
            # Export Trials
            self.trials.to_excel(writer, sheet_name='trials')

            # Export Load
            start_row = 0
            for seq in self.trials['seq'].values:
                f = self.perf_load[seq]
                f.to_excel(writer, sheet_name='load', startrow=start_row)
                start_row = start_row + 5 + len(f.index)

            # Export Resolving
            start_row_f1 = 0
            start_row_f2 = 0
            start_row_f3 = 0
            start_row_f4 = 0
            for seq in self.trials['seq'].values:
                f1 = self.perf_get_positive[seq].get_df()
                f1.to_excel(writer, sheet_name='get_positive', startrow=start_row_f1)
                start_row_f1 = start_row_f1 + 5 + len(f1.index)
                f2 = self.perf_get_negative[seq].get_df()
                f2.to_excel(writer, sheet_name='get_negative', startrow=start_row_f2)
                start_row_f2 = start_row_f2 + 5 + len(f2.index)
                f3 = self.perf_lpm_positive[seq].get_df()
                f3.to_excel(writer, sheet_name='lpm_positive', startrow=start_row_f3)
                start_row_f3 = start_row_f3 + 5 + len(f3.index)
                f4 = self.perf_lpm_negative[seq].get_df()
                f4.to_excel(writer, sheet_name='lpm_negative', startrow=start_row_f4)
                start_row_f4 = start_row_f4 + 5 + len(f4.index)

    def summarize(self):
        # Initialize Summarize Load
        summary_load_df = pd.DataFrame()
        cbs = self.perf_load[0]
        extracted_column = cbs['Cumulative Batch Size']
        summary_load_df.insert(0, 'Cumulative Batch Size', extracted_column)

        # Initialize Summarise Gets/LPMs
        queries_count = self.perf_get_positive[0].get_df()['Count']
        summary_gp_df = pd.DataFrame()
        summary_gp_df.insert(0, 'Queries Count', queries_count)
        summary_gn_df = pd.DataFrame()
        summary_gn_df.insert(0, 'Queries Count', queries_count)
        summary_lp_df = pd.DataFrame()
        summary_lp_df.insert(0, 'Queries Count', queries_count)
        summary_ln_df = pd.DataFrame()
        summary_ln_df.insert(0, 'Queries Count', queries_count)

        i = 1
        for idx, t in self.trials.iterrows():
            seq = t['seq']
            algo_name = t['backend_name']

            # Summarize Load
            summary_load_df.insert(i, algo_name, self.perf_load[seq]['Cumulative Duration in s'])

            # Summarize Get - Positive
            summary_gp_df.insert(i, algo_name, self.perf_get_positive[seq].get_df()['Cumulative Duration in s'])

            # Summarize Get - Negative
            summary_gn_df.insert(i, algo_name, self.perf_get_negative[seq].get_df()['Cumulative Duration in s'])

            # Summarize LPM - Positive
            summary_lp_df.insert(i, algo_name, self.perf_lpm_positive[seq].get_df()['Cumulative Duration in s'])

            # Summarize LPM - Negative
            summary_ln_df.insert(i, algo_name, self.perf_lpm_negative[seq].get_df()['Cumulative Duration in s'])

            i += 1

        store = pd.HDFStore('exports/store.h5')
        store['summary_load_df'] = summary_load_df
        store['summary_gp_df'] = summary_gp_df
        store['summary_gn_df'] = summary_gn_df
        store['summary_lp_df'] = summary_lp_df
        store['summary_ln_df'] = summary_ln_df
        pass

