""" rnn, xor problem """
import numpy as np
import tensorflow as tf

np.random.seed(0)

# Parameter Settings
batch_size0, seq_len0 = [128, 50]
dim_in, dim_hidden, dim_out = [2, 30, 1]
dtype = tf.float32

def get_batches(batch_size=batch_size0):
    seq_len = seq_len0 #round(seq_len0 + 0.1*np.random.rand()*seq_len0)
    x = np.zeros([batch_size, seq_len, dim_in])
    y = np.zeros([batch_size, dim_out])
    for i in range(batch_size):
        x[i,:,0] = np.random.choice([-1.0, 1.0], seq_len)

        i1 = int(np.floor(np.random.rand()*0.1*seq_len))
        i2 = int(np.floor(np.random.rand()*0.4*seq_len + 0.1*seq_len))             
        x[i, i1, 1] = 1.0
        x[i, i2, 1] = 1.0
        if x[i,i1,0] == x[i,i2,0]:
            y[i] = -1.0 # lable 0
        else:
            y[i] = 1.0  # lable 1
            
    #tranpose x to dimensions: sequence_length * batch_size * dimension_input  
    return np.transpose(x, [1, 0, 2]), y


# generate a random orthogonal matrix for recurrent matrix initialization 
def get_rand_orth( dim ):
    temp = np.random.normal(size=[dim, dim])
    q, _ = np.linalg.qr(temp)
    return q


# Model Coefficients
W1 = tf.Variable(np.concatenate((np.random.normal(0.0, 0.1, [dim_in, dim_hidden]), 
                                 get_rand_orth(dim_hidden), 
                                 np.zeros([1, dim_hidden])), axis=0), 
                                 dtype = dtype)
W2 = tf.Variable(np.concatenate((np.random.normal(0.0, 0.1, [dim_hidden, dim_out]), 
                                 np.zeros([1, dim_out])), axis=0),
                                 dtype = dtype)
Ws = [W1, W2]   # put all trainable coefficients in this list

train_inputs = tf.placeholder(dtype, [seq_len0, batch_size0, dim_in])
train_outputs = tf.placeholder(dtype, [batch_size0, dim_out])

# model definition 
def model(Ws, inputs):
    W1, W2 = Ws
    batch_size = inputs.shape.as_list()[1]
    ones = tf.ones([batch_size, 1], dtype=dtype)
    
#    """ Unfortunately, tf.while_loop does not support second order derivative """
#    _, last_state = tf.while_loop(lambda i, state: i < tf.shape(inputs)[0],
#                                  lambda i, state: [i+1, tf.tanh(tf.matmul(tf.concat([inputs[i], state, ones], 1), W1))],
#                                  [0, tf.zeros([batch_size, dim_hidden])],)
    
    """ Unfortunately, tf.while_loop does not support second order derivative; so static unrolling here """
    last_state = tf.zeros([batch_size, dim_hidden], dtype=dtype)
    for i in range(seq_len0):
        last_state = tf.tanh(tf.matmul(tf.concat([inputs[i], last_state, ones], 1), W1))
        
    y = tf.matmul(tf.concat((last_state, ones), 1), W2)
    return y
    
# logistic loss
def train_criterion(Ws):
    y = model(Ws, train_inputs)
    score = y*train_outputs
    return tf.reduce_mean(-score + tf.log(1.0 + tf.exp(score)))

# classification error rate
test_x, test_y = get_batches(10000)
def test_criterion(Ws):
    y = model(Ws, tf.constant(test_x, dtype=dtype))
    score = y*tf.constant(test_y, dtype=dtype)
    return tf.reduce_mean(tf.cast(tf.less(score, 0.0), dtype=dtype))