import random

import torch.nn as nn
import torch.nn.functional as F
import torch.nn.init as init

class ModelMLP(nn.Module):
    """A 2-layer multilayer perceptron based classifier that uses one-hot encoding as an input sequence representation"""

    def __init__(self, input_dim, hidden_dim, output_dim):
        """
        Args:
            input_dim (int): the size of the input feature vector
            hidden_dim (int): the output size of the first Linear layer
            output_dim (int): the output size of the second Linear layer
        """
        # call the base initialization
        super(ModelMLP, self).__init__()

        # Define the model

        # first linear layer with number of inputs correspoding to the size of the input feature vector and number of outputs correspoding to the hidden state size
        self.fc1 = nn.Linear(in_features=input_dim, out_features=hidden_dim)

        # second linear layer with number of inputs correspoding to the hidden state size and number of outputs corresponding the number of output classes
        self.fc2 = nn.Linear(in_features=hidden_dim, out_features=output_dim)

        # Initialize the weights to random numbers
        self.initialize_weights()

    def initialize_weights(self):
        # Initialize weights of l1 and l2 layers with random values
        init.uniform_(self.fc1.weight, -1, 1)
        init.uniform_(self.fc2.weight, -1, 1)

    def mutate_weights(self, mutation_probability, mutation_factor):
        for param in self.parameters():
            if param.requires_grad:
                tensor = param.data
                if tensor.dim() == 2:
                    for i in range(tensor.shape[0]):
                        for j in range(tensor.shape[1]):
                            rand = random.random()
                            if rand < mutation_probability:
                                side = -1 if (random.random() < 0.5) else 1
                                tensor[i, j] += side * (random.random()) * mutation_factor * tensor[i, j]

    def forward(self, x_in):
        """
        The forward pass of the Classifier

        Args:
            x_in (torch.Tensor): an input data tensor with input shape (batch, input_dim)
        Returns:
            resulting tensor, with shape (batch, output_dim)
        """
        # calculate the output of the first linear layer
        y_out = self.fc1(x_in)

        # apply non-linear function to the output of the linear layer
        y_out = F.relu(y_out)

        # calculate the output of the second linear layer
        y_out = self.fc2(y_out)

        return True if (y_out[0] > 0) else False
