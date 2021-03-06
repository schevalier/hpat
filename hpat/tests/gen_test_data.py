import h5py
import numpy as np
import pyarrow.parquet as pq
import pyarrow as pa
import pandas as pd


def gen_lr(file_name, N, D):
    points = np.random.random((N,D))
    responses = np.random.random(N)
    f = h5py.File(file_name, "w")
    dset1 = f.create_dataset("points", (N,D), dtype='f8')
    dset1[:] = points
    dset2 = f.create_dataset("responses", (N,), dtype='f8')
    dset2[:] = responses
    f.close()

def gen_kde_pq(file_name, N):
    df = pd.DataFrame({'points': np.random.random(N)})
    table = pa.Table.from_pandas(df)
    row_group_size = 128
    pq.write_table(table, file_name, row_group_size)

def gen_pq_test(file_name):
    df = pd.DataFrame({'one': [-1, np.nan, 2.5, 3., 4., 6., 10.0],
                           'two': ['foo', 'bar', 'baz', 'foo', 'bar', 'baz', 'foo'],
                           'three': [True, False, True, True, True, False, False],
                           'four': [-1, 5.1, 2.5, 3., 4., 6., 11.0], # float without NA
                           'five': ['foo', 'bar', 'baz', None, 'bar', 'baz', 'foo'], # str with NA
                     })
    table = pa.Table.from_pandas(df)
    pq.write_table(table, 'example.parquet')
    pq.write_table(table, 'example2.parquet', row_group_size=2)

N = 101
D = 10
gen_lr("lr.hdf5", N, D)

arr = np.arange(N)
f = h5py.File("test_group_read.hdf5", "w")
g1 = f.create_group("G")
dset1 = g1.create_dataset("data", (N,), dtype='i8')
dset1[:] = arr
f.close()

gen_kde_pq('kde.parquet', N)
gen_pq_test('example.parquet')

df = pd.DataFrame({'A': ['bc']+["a"]*3+ ["bc"]*3+['a'], 'B': [-8,1,2,3,1,5,6,7]})
df.to_parquet("groupby3.pq")

df = pd.DataFrame({"A": ["foo", "foo", "foo", "foo", "foo",
                          "bar", "bar", "bar", "bar"],
                    "B": ["one", "one", "one", "two", "two",
                          "one", "one", "two", "two"],
                    "C": ["small", "large", "large", "small",
                          "small", "large", "small", "small",
                          "large"],
                    "D": [1, 2, 2, 6, 3, 4, 5, 6, 9]})
df.to_parquet("pivot2.pq")

# test datetime64, spark dates
dt1 = pd.DatetimeIndex(['2017-03-03 03:23', '1990-10-23', '1993-07-02 10:33:01'])
df = pd.DataFrame({'DT64': dt1, 'DATE': dt1.copy()})
df.to_parquet('pandas_dt.pq')

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, DateType, TimestampType

spark = SparkSession.builder.appName("GenSparkData").getOrCreate()
schema = StructType([StructField('DT64', DateType(), True), StructField('DATE', TimestampType(), True)])
sdf = spark.createDataFrame(df, schema)
sdf.write.parquet('sdf_dt.pq', 'overwrite')

spark.stop()

# generated data for parallel merge_asof testing
df1 = pd.DataFrame({'time': pd.DatetimeIndex(
    ['2017-01-03', '2017-01-06', '2017-02-15', '2017-02-21']),
    'B': [4, 5, 9, 6]})
df2 = pd.DataFrame({'time': pd.DatetimeIndex(
    ['2017-01-01', '2017-01-14', '2017-01-16', '2017-02-23', '2017-02-23',
    '2017-02-25']), 'A': [2,3,7,8,9,10]})
df1.to_parquet("asof1.pq")
df2.to_parquet("asof2.pq")
