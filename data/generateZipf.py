import tensorflow as tf
import tensorflow_probability as tfp
import sys

def create_Zipf_data(alpha, n, data_type):
    tfd = tfp.distributions
    gen = tfd.Zipf(alpha, dtype=data_type)
    data = gen.sample(n)
    return data

data = create_Zipf_data(float(sys.argv[1]), 1024*1024*1024/2, tf.uint32)
data.numpy().tofile(sys.argv[2])
