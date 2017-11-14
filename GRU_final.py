import numpy as np
import cPickle
from collections import defaultdict
import re

import sys
import os

os.environ['KERAS_BACKEND']='tensorflow'

from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from keras.utils.np_utils import to_categorical

from keras.layers import Embedding
from keras.layers import Dense, Input, Flatten
from keras.layers import Conv1D, MaxPooling1D, Embedding, Merge, Dropout, GRU, LSTM, Bidirectional
from keras.models import Model

MAX_SEQUENCE_LENGTH = 1500
#MAX_NB_WORDS = 20000
EMBEDDING_DIM = 100
VALIDATION_SPLIT = 0.2

emails = []
labels = []

classes = []
class_labels = {}
class_ind = 0

for author_dir in os.listdir('clean_enron'):
    if author_dir == '.DS_Store':
        continue
    classes.append(author_dir)
    class_labels[author_dir] = class_ind
    class_ind += 1

for author_dir in os.listdir('clean_enron'):
    if author_dir == '.DS_Store':
        continue
    for message_file in os.listdir('./clean_enron/' + author_dir):
        with open('./clean_enron/' + author_dir + '/' + message_file, 'r') as f:
            text = f.read()
            text = text.replace("\n", " ")
            emails.append(text.lower())
            labels.append(class_labels[author_dir])    

tokenizer = Tokenizer()
tokenizer.fit_on_texts(emails)
sequences = tokenizer.texts_to_sequences(emails)

word_index = tokenizer.word_index
# print('Found %s unique tokens.' % len(word_index))

data = pad_sequences(sequences, maxlen=MAX_SEQUENCE_LENGTH)

labels = to_categorical(np.asarray(labels))
print labels.shape[0], labels.shape[1]
# print('Shape of data tensor:', data.shape)
# print('Shape of label tensor:', labels.shape)

indices = np.arange(data.shape[0])
np.random.shuffle(indices)
data = data[indices]
labels = labels[indices]
nb_validation_samples = int(VALIDATION_SPLIT * data.shape[0])

x_train = data[:-nb_validation_samples]
y_train = labels[:-nb_validation_samples]
x_val = data[-nb_validation_samples:]
y_val = labels[-nb_validation_samples:]

# print('Number of positive and negative reviews in traing and validation set ')
# print y_train.sum(axis=0)
# print y_val.sum(axis=0)

embeddings_index = {}
with open('glove.6B.100d.txt') as f:
    for line in f:
        values = line.split()
        word = values[0]
        coefs = np.asarray(values[1:], dtype='float32')
        embeddings_index[word] = coefs

# print('Total %s word vectors in Glove 6B 100d.' % len(embeddings_index))

embedding_matrix = np.random.random((len(word_index) + 1, EMBEDDING_DIM))
for word, i in word_index.items():
    embedding_vector = embeddings_index.get(word)
    if embedding_vector is not None:
        embedding_matrix[i] = embedding_vector
        
embedding_layer = Embedding(len(word_index) + 1,
                            EMBEDDING_DIM,
                            weights=[embedding_matrix],
                            input_length=MAX_SEQUENCE_LENGTH,
                            trainable=True)

sequence_input = Input(shape=(MAX_SEQUENCE_LENGTH,), dtype='int32')
embedded_sequences = embedding_layer(sequence_input)
l_lstm = Bidirectional(GRU(100))(embedded_sequences)
dense_1 = Dense(128, activation='relu')(l_lstm)
drop_1 = Dropout(0.3)(dense_1)
preds = Dense(10, activation='softmax')(drop_1)
model = Model(sequence_input, preds)
model.compile(loss='categorical_crossentropy',
              optimizer='rmsprop',
              metrics=['acc'])

print("model fitting bidirectional GRU")
model.fit(x_train, y_train, validation_data=(x_val, y_val),
          epochs=30, batch_size=50)

# Attention GRU network		  
# class AttLayer(Layer):
#     def __init__(self, **kwargs):
#         self.init = initializations.get('normal')
#         #self.input_spec = [InputSpec(ndim=3)]
#         super(AttLayer, self).__init__(**kwargs)

#     def build(self, input_shape):
#         assert len(input_shape)==3
#         #self.W = self.init((input_shape[-1],1))
#         self.W = self.init((input_shape[-1],))
#         #self.input_spec = [InputSpec(shape=input_shape)]
#         self.trainable_weights = [self.W]
#         super(AttLayer, self).build(input_shape)  # be sure you call this somewhere!

#     def call(self, x, mask=None):
#         eij = K.tanh(K.dot(x, self.W))
        
#         ai = K.exp(eij)
#         weights = ai/K.sum(ai, axis=1).dimshuffle(0,'x')
        
#         weighted_input = x*weights.dimshuffle(0,1,'x')
#         return weighted_input.sum(axis=1)

#     def get_output_shape_for(self, input_shape):
#         return (input_shape[0], input_shape[-1])

# embedding_matrix = np.random.random((len(word_index) + 1, EMBEDDING_DIM))
# for word, i in word_index.items():
#     embedding_vector = embeddings_index.get(word)
#     if embedding_vector is not None:
#         # words not found in embedding index will be all-zeros.
#         embedding_matrix[i] = embedding_vector
        
# embedding_layer = Embedding(len(word_index) + 1,
#                             EMBEDDING_DIM,
#                             weights=[embedding_matrix],
#                             input_length=MAX_SEQUENCE_LENGTH,
#                             trainable=True)



# sequence_input = Input(shape=(MAX_SEQUENCE_LENGTH,), dtype='int32')
# embedded_sequences = embedding_layer(sequence_input)
# l_gru = Bidirectional(GRU(100, return_sequences=True))(embedded_sequences)
# l_att = AttLayer()(l_gru)
# preds = Dense(2, activation='softmax')(l_att)
# model = Model(sequence_input, preds)
# model.compile(loss='categorical_crossentropy',
#               optimizer='rmsprop',
#               metrics=['acc'])

# print("model fitting - attention GRU network")
# model.summary()
# model.fit(x_train, y_train, validation_data=(x_val, y_val),
#           nb_epoch=10, batch_size=50)
