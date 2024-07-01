import configparser
import logging
import os
import pathlib
import subprocess
import time
from threading import Thread

import Selector

# region Configuration
config_file = '/etc/ndn/pnp/app.ini'
path = pathlib.Path(config_file)
if not path.exists():
    exit('Can not find the configuration file in: {}'.format(config_file))
application_config = configparser.ConfigParser()
application_config.read(config_file)
export_home = application_config.get('Paths', 'export_home')
export_home = export_home if export_home.endswith('/') else export_home + '/'
sampling_interval = float(application_config.get('Profiler', 'sampling_interval'))


# endregion Configuration


class Profiler:
    psr_process = None

    def __init__(self, backend_type: Selector.Algorithms, process_id, test_name: str):
        self.pid = process_id
        self.be = backend_type
        self.be_name = backend_type.name
        self.test_name = test_name
        self.activity_filename = export_home + backend_type.name + '_psr_activity_' + test_name + '.txt'
        self.plot_filename = export_home + backend_type.name + '_psr_plot_' + test_name + '.png'
        self.thread = None
        self.keep_running = True

    def start(self):
        self.thread = Thread(target=self.monitor)
        self.thread.start()

    def stop(self):
        self.keep_running = False
        if self.thread is not None:
            self.thread = None

    def monitor(self):
        # Modified version on psrecord.monitor() that supports start/stop

        import psutil

        pr = psutil.Process(self.pid)

        # Record start time
        start_time = time.time()

        if self.activity_filename:
            f = open(self.activity_filename, 'w')
            f.write("# {0:12s} {1:12s} {2:12s} {3:12s}\n".format(
                'Elapsed time'.center(12),
                'CPU (%)'.center(12),
                'Real (MB)'.center(12),
                'Virtual (MB)'.center(12))
            )

        log = {}
        log['times'] = []
        log['cpu'] = []
        log['mem_real'] = []
        log['mem_virtual'] = []

        try:

            # Start main event loop
            while self.keep_running:

                # Find current time
                current_time = time.time()

                try:
                    pr_status = pr.status()
                except TypeError:  # psutil < 2.0
                    pr_status = pr.status
                except psutil.NoSuchProcess:  # pragma: no cover
                    break

                # Check if process status indicates we should exit
                if pr_status in [psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD]:
                    print("Process finished ({0:.2f} seconds)"
                          .format(current_time - start_time))
                    break


                # Get current CPU and memory
                try:
                    current_cpu = pr.cpu_percent()
                    current_mem = pr.memory_info()
                except Exception:
                    break
                current_mem_real = current_mem.rss / 1024. ** 2
                current_mem_virtual = current_mem.vms / 1024. ** 2

                if self.activity_filename:
                    f.write("{0:12.3f} {1:12.3f} {2:12.3f} {3:12.3f}\n".format(
                        current_time - start_time,
                        current_cpu,
                        current_mem_real,
                        current_mem_virtual))
                    f.flush()

                if sampling_interval is not None:
                    time.sleep(sampling_interval)

                # If plotting, record the values
                if self.plot_filename:
                    log['times'].append(current_time - start_time)
                    log['cpu'].append(current_cpu)
                    log['mem_real'].append(current_mem_real)
                    log['mem_virtual'].append(current_mem_virtual)

        except KeyboardInterrupt:  # pragma: no cover
            pass

        if self.activity_filename:
            f.close()

        if self.plot_filename:
            # Use non-interactive backend, to enable operation on headless machines
            import matplotlib.pyplot as plt
            with plt.rc_context({'backend': 'Agg'}):
                fig = plt.figure()
                ax = fig.add_subplot(1, 1, 1)

                ax.plot(log['times'], log['cpu'], '-', lw=1, color='r')

                ax.set_ylabel('CPU (%)', color='r')
                ax.set_xlabel('time (s)')
                ax.set_ylim(0., max(log['cpu']) * 1.2)

                ax2 = ax.twinx()

                ax2.plot(log['times'], log['mem_real'], '-', lw=1, color='b')
                ax2.set_ylim(0., max(log['mem_real']) * 1.2)

                ax2.set_ylabel('Real Memory (MB)', color='b')

                ax.grid()

                fig.savefig(self.plot_filename)
