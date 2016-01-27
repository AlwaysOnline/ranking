import pandas as pd
import numpy as np
from fast_converter import fast_colley_matrix_build, fast_colley_vector_build,\
fast_rate_diff_vote_matrix_build, fast_simple_diff_vote_matrix_build, \
fast_rate_vote_matrix_build
from scipy.sparse import coo_matrix, csr_matrix


class Converter(object):
    """Converter accepts dataframe hdf5 files and converts it to different matrix
    suitable for the needs of ranker. Users can call different matrix generator
    to generate their matrix wanted.
    """

    def __init__(self, filename):
        # Detect table format
        table = pd.read_hdf(filename, "item_pair_rate")
        self.table = table[['primary','secondary','rate1','rate2','weight']]
        # itemid to index table
        idx = self._extract_list(self.table)
        self.itemlist = idx
        temptable = table.iloc[:,:2].values
        pair = np.fromfunction(np.vectorize(lambda i, j: idx[temptable[i,j]]),
                        temptable.shape)
        pair = np.require(pair, dtype=np.int32)
        self.pair = pair

    def _extract_list(self, table):
        iid = np.hstack([table.loc[:,'primary'].values,
              table.loc[:,'secondary'].values])
        iid = np.unique(iid)
        # index to itemid
        self.iid = iid
        item_id = dict(zip(iid, range(iid.shape[0])))
        return item_id

    def ItemList(self):
        table = self.itemlist
        itemlist =  pd.DataFrame({'itemid': table.keys(),
                             'index': table.values()},
                            columns=['itemid', 'index'])
        itemlist.sort_values(by='index',inplace=True)
        return pd.DataFrame(itemlist.values,
                            index = pd.Index(range(itemlist.shape[0])),
                            columns=['itemid', 'index'])

    def ColleyMatrix(self):
        idx = self.itemlist
        table = self.table

        icnt = len(idx)
        # allocate space for computing
        C = np.zeros((icnt, icnt), dtype=np.float32)
        pair = self.pair

        fast_colley_matrix_build(pair,
                        np.require(table.iloc[:,2:].values, dtype=np.float32),
                        C)

        return C

    def ColleyVector(self):
        idx = self.itemlist
        table = self.table

        icnt = len(idx)
        # allocate space for computing
        b = np.zeros(icnt, dtype=np.float32)
        pair = self.pair

        fast_colley_vector_build(pair,
                        np.require(table.iloc[:,2:].values, dtype=np.float32),
                        b)

        return b


    def RateDifferenceVoteMatrix(self):
        """This function outputs only Point Difference Matrix.
        """
        idx = self.itemlist
        table = self.table

        icnt = len(idx)
        # allocate space for computing
        D = np.zeros((icnt, icnt), dtype=np.float32)
        pair = self.pair

        fast_rate_diff_vote_matrix_build(pair,
                        np.require(table.iloc[:,2:].values, dtype=np.float32),
                        D)

        return D

    def SimpleDifferenceVoteMatrix(self):
        """This function outputs only Simple Difference Vote Matrix.
        """
        idx = self.itemlist
        table = self.table

        icnt = len(idx)
        # allocate space for computing
        D = np.zeros((icnt, icnt), dtype=np.float32)
        pair = self.pair

        fast_simple_diff_vote_matrix_build(pair,
                        np.require(table.iloc[:,2:].values, dtype=np.float32),
                        D)

        return D

    def RateVoteMatrix(self):
        """This function outputs only Simple Difference Vote Matrix.
        """
        idx = self.itemlist
        table = self.table

        icnt = len(idx)
        # allocate space for computing
        D = np.zeros((icnt, icnt), dtype=np.float32)
        pair = self.pair

        fast_rate_vote_matrix_build(pair,
                        np.require(table.iloc[:,2:].values, dtype=np.float32),
                        D)

        return D


    def MasseyMatrix(self):
        """This function produces X'WX
        """
        idx = self.itemlist
        table = self.table
        pair = self.pair
        j = np.ravel(pair)
        i = np.repeat(np.arange(table.shape[0], dtype=np.int32), 2, axis=0)
        data = np.array([[1,-1]],dtype=np.float32)
        data = np.ravel(np.repeat(data, table.shape[0], axis=0))
        X = coo_matrix((data, (i, j)), shape=(table.shape[0], len(idx)))
        X = X.tocsr()
        W = np.require(table.iloc[:,4].values, np.float32)
        W = coo_matrix((W, (np.arange(W.shape[0]), np.arange(W.shape[0])))).tocsr()
        return (X.T*W*X).todense()


    def MasseyVector(self):
        """This function produces X'Wy
        """
        idx = self.itemlist
        table = self.table
        pair = self.pair
        j = np.ravel(pair)
        i = np.repeat(np.arange(table.shape[0], dtype=np.int32), 2, axis=0)
        data = np.array([[1,-1]],dtype=np.float32)
        data = np.ravel(np.repeat(data, table.shape[0], axis=0))
        X = coo_matrix((data, (i, j)), shape=(table.shape[0], len(idx)))
        X = X.tocsr()
        W = np.require(table.iloc[:,4].values, np.float32)
        y = table.iloc[:, 2].values - table.iloc[:, 3].values;
        Wy=np.multiply(W, y)
        return X.T*Wy

    def DataDifferenceMatrix(self):
        return self.RateDifferenceVoteMatrix().T
