import time
import h5py
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from sklearn.metrics import confusion_matrix, classification_report

from models import create_model
from dataset import SleepApneaDataModule, EmbeddedDataModule
from utils import open_config_file, train_model, evaluate_model, test_model, epoch_time, plot_curves

parser = argparse.ArgumentParser()
parser.add_argument('--config', type=str, default="config/default.json", metavar='N', help='config file')
args = parser.parse_args()
params = open_config_file(args.config)

print('------------ Options -------------')
for k, v in vars(params).items():
    print('%s: %s' % (str(k), str(v)))
print('-------------- End ----------------')

if params.discrete_transform:
    data_module = EmbeddedDataModule(params)
else:
    data_module = SleepApneaDataModule(params)
data_module.setup()
train_dataset, val_dataset, test_dataset = data_module.train_dataset, data_module.val_dataset, data_module.test_dataset
train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=params.batch_size, shuffle=False)
val_loader = torch.utils.data.DataLoader(val_dataset, batch_size=params.batch_size, shuffle=False)

model = create_model(params)
optimizer = optim.Adam(model.parameters())
model = model.cuda()
criterion = nn.BCELoss()
criterion = criterion.cuda()

best_valid_loss = float('inf')
best_valid_acc = 0.0

train_losses, val_losses = [], []
train_accuracies, val_accuracies = [], []

for epoch in range(params.nepochs):

    start_time = time.time()
    # train_loss = train_model(epoch+1, model, train_loader, optimizer, criterion, params)
    train_loss, train_acc = train_model(epoch+1, model, train_loader, optimizer, criterion, params)
    train_losses.append(train_loss)
    train_accuracies.append(train_acc)

    if epoch % params.eval_every == 0:
        # valid_loss = evaluate_model(epoch+1, model, val_loader, criterion, params)
        valid_loss, valid_acc = evaluate_model(epoch+1, model, val_loader, criterion, params)
        val_losses.append(valid_loss)
        val_accuracies.append(valid_acc)

        if params.tracking == 'val_loss':
            if valid_loss < best_valid_loss:
                best_valid_loss = valid_loss
                torch.save(model.state_dict(), 'best_model.pt')

        elif params.tracking == 'val_acc':
            if valid_acc > best_valid_acc:
                best_valid_acc = valid_acc
                torch.save(model.state_dict(), 'best_model.pt')

    end_time = time.time()
    epoch_mins, epoch_secs = epoch_time(start_time, end_time)
    print(f'End of epoch {epoch+1} / {params.nepochs} \t Time Taken:  {epoch_mins}m {epoch_secs}s')
    print(f'Train loss: {np.round(train_loss,6)} \t Train acc: {np.round(train_acc,4)}')
    print(f'Val loss: {np.round(valid_loss,6)} \t Val acc: {np.round(valid_acc,4)}\n')

plot_curves(train_losses, train_accuracies, val_losses, val_accuracies, params)

print('Beginning testing...')
test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=1, shuffle=False)
best_model = create_model(params)
best_model.load_state_dict(torch.load('best_model.pt'))
best_model = best_model.cuda()
best_model.eval()

test_predictions = test_model(best_model, test_loader, params, threshold=0.5)
test_result_list = []
for i, (sample_id, pred) in enumerate(test_predictions.items()):
    test_result_list.append([sample_id] + pred)
test_result_df = pd.DataFrame(test_result_list, columns=['ID']+[f'y_{i}' for i in range(90)])
test_result_df.to_csv('test_predictions.csv', index=False)
print('done')