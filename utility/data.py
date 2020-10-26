import pandas as pd


class Data:
    def __init__(self):
        self.df = pd.DataFrame(columns=['count', 'cycle', 'timestamp', 'isc_fit', 'disc_fit', 'voc_fit', 'dvoc_fit',
                                        'pmax_fit', 'irrad1', 'irrad2', 't_sample', 'irrad3', 'name', 'date', 'film_id',
                                        'cell_id', 'ref_cell_temp', 'location', 'cal_date', 'cal_value', 'pid_pb',
                                        'pid_int', 'pid_der', 'pid_fuoc', 'pid_tcr1', 'pid_tcr2', 'pid_sp', 't_room',
                                        'rh_room'])

    def add_line(self, *args):
        self.df.loc[len(self.df.index)] = args

    def reset(self):
        self.df = self.df.iloc[0:0]

    def save(self, path):
        self.df.to_excel(path)
