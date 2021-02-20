import collections
from metric_dreem import dreem_sleep_apnea_custom_metric


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


def open_config_file(filepath):
    with open(filepath) as jsonfile:
        pdict = json.load(jsonfile)
        params = AttrDict(pdict)
    return params


def epoch_time(start_time, end_time):
  elapsed_time = end_time - start_time
  elapsed_mins = int(elapsed_time / 60)
  elapsed_secs = int(elapsed_time - (elapsed_mins * 60))
  return elapsed_mins, elapsed_secs


def train_model(model, train_loader, optimizer, criterion, params):
    
    epoch_loss = 0
    epoch_acc = 0
    model.train()
    
    with tqdm(train_loader, 
              desc=(f'Train - Epoch: {epoch}'), 
              unit=' patient', 
              ncols=80, 
              unit_scale=params.batch_size) as t:

        for i, (signal, target) in enumerate(t):

            optimizer.zero_grad()
            signal = signal.type(torch.FloatTensor)
            signal, target = signal.to(device), target.to(device)
            signal = signal.permute(1,0,2)

            preds = model(signal).squeeze(1)
            preds = preds.type(torch.FloatTensor).cpu()
            target = target.type(torch.FloatTensor).cpu()
            loss = criterion(preds, target)
            # acc = dreem_sleep_apnea_custom_metric((preds.detach()>0.5).float(), target.detach())

            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()
            # epoch_acc += acc

    # return epoch_loss / len(train_loader), epoch_acc / len(train_loader)
    return epoch_loss / len(train_loader)


def evaluate_model(model, val_loader, criterion):
    
    epoch_loss = 0
    epoch_acc = 0
    model.eval()
    
    with tqdm(val_loader, 
             desc=(f'Validation - Epoch: {epoch}'), 
             unit=' patient', 
             ncols=80, 
             unit_scale=params.batch_size) as t:

        with torch.no_grad():

            for i, (signal, target) in enumerate(t):

                signal = signal.type(torch.FloatTensor)
                signal, target = signal.to(device), target.to(device)
                signal = signal.permute(1,0,2)

                preds = model(signal).squeeze(1)
                preds = preds.type(torch.FloatTensor).cpu()
                target = target.type(torch.FloatTensor).cpu()
                loss = criterion(preds, target)
                # acc = dreem_sleep_apnea_custom_metric((preds.detach()>0.5).float(), target.detach())

                epoch_loss += loss.item()
                # epoch_acc += acc

    # return epoch_loss / len(val_loader), epoch_acc / len(val_loader)
    return epoch_loss / len(val_loader)