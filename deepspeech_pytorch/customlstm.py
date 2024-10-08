import pytorch_lightning as pl
import torch,math
import torch.nn as nn

class CustomLSTM(nn.Module):
     def __init__(self, input_sz, hidden_sz, peephole=False):
         super().__init__()
         self.input_sz = input_sz
         self.hidden_size = hidden_sz
         self.peephole = peephole
         self.W = nn.Parameter(torch.Tensor(input_sz, hidden_sz * 4))
         self.U = nn.Parameter(torch.Tensor(hidden_sz, hidden_sz * 4))
         self.bias = nn.Parameter(torch.Tensor(hidden_sz * 4))
         self.init_weights()
                 
     def init_weights(self):
         stdv = 1.0 / math.sqrt(self.hidden_size)
         for weight in self.parameters():
             weight.data.uniform_(-stdv, stdv)
         
     def forward(self, x,
                 init_states=None):
         """Assumes x is of shape (batch, sequence, feature)"""
         #bs, seq_sz, _ = x.size()
         #x = x.data
         seq_sz, bs, _ = x.size()
         hidden_seq = []
         if init_states is None:
             h_t, c_t = (torch.zeros(bs, self.hidden_size).to(x.device),
                         torch.zeros(bs, self.hidden_size).to(x.device))
         else:
             h_t, c_t = init_states
         
         HS = self.hidden_size
         for t in range(seq_sz):
             x_t = x[t, :, :]
             # batch the computations into a single matrix multiplication
             
             if self.peephole:
                 gates = x_t @ self.W + c_t @ self.U + self.bias
             else:
                 gates = x_t @ self.W + h_t @ self.U + self.bias
                 g_t = torch.tanh(gates[:, HS*2:HS*3])
             
             i_t, f_t, o_t = (
                 torch.sigmoid(gates[:, :HS]), # input
                 torch.sigmoid(gates[:, HS:HS*2]), # forget
                 torch.sigmoid(gates[:, HS*3:]), # output
             )
             
             if self.peephole:
                 c_t = f_t * c_t + i_t * torch.sigmoid(x_t @ U + bias)[:, HS*2:HS*3]
                 h_t = torch.tanh(o_t * c_t)
             else:
                 c_t = f_t * c_t + i_t * g_t
                 h_t = o_t * torch.tanh(c_t)
                 
             hidden_seq.append(h_t.unsqueeze(0))
             
         hidden_seq = torch.cat(hidden_seq, dim=0)
         # reshape from shape (sequence, batch, feature) to (batch, sequence, feature)
         # hidden_seq = hidden_seq.transpose(0, 1).contiguous()
         
         return hidden_seq, (h_t, c_t)