from __future__ import annotations

# Legacy training implementation moved from root model_train.py

import csv
import math
import random
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn import metrics
from torch.utils.data import DataLoader, TensorDataset
from tqdm import tqdm

from backend.process_compliance.utils import csv_to_dict, get_key_by_value, get_parameters, mkdir, read_log

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATASET = "BPIC20_D"
ATTRIBUTES = ("remainingTimeNor", "concept:name", "org:resource", "org:role")
GPU_ID = 0
RANDOM_SEED = 0
EPOCH = 200
TRIALS = 20
ENCODING_LENGTH = 32
DATA_ADD = str(PROJECT_ROOT / "dataset" / "new_data" / f"{DATASET}.csv")
MODEL_DIR = str(PROJECT_ROOT / "model")
PRO_DATA_DIR = str(PROJECT_ROOT / "artifacts" / "processed_features")

np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)
torch.manual_seed(RANDOM_SEED)
USE_CUDA = torch.cuda.is_available()
if USE_CUDA:
    torch.cuda.manual_seed(RANDOM_SEED)
    torch.cuda.set_device(GPU_ID)

# Same runtime convention as legacy file
PREDICTION_MODE = "NAP"


def _resolve_path(path: str | Path, base_dir: str | Path | None = None) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p.resolve()
    root = Path(base_dir).resolve() if base_dir is not None else PROJECT_ROOT
    return (root / p).resolve()


def configure_paths(
    *,
    dataset_name: str | None = None,
    dataset_csv: str | Path | None = None,
    model_dir: str | Path | None = None,
    pro_data_dir: str | Path | None = None,
    base_dir: str | Path | None = None,
) -> None:
    global DATASET, DATA_ADD, MODEL_DIR, PRO_DATA_DIR
    if dataset_name:
        DATASET = dataset_name
    DATA_ADD = str(_resolve_path(dataset_csv or Path("dataset") / "new_data" / f"{DATASET}.csv", base_dir))
    MODEL_DIR = str(_resolve_path(model_dir or "model", base_dir))
    PRO_DATA_DIR = str(_resolve_path(pro_data_dir or Path("artifacts") / "processed_features", base_dir))


def trans_to_str(val):
    if isinstance(val, float):
        new_val = str(int(val))
    elif isinstance(val, int):
        new_val = str(val)
    else:
        new_val = val
    return new_val


def get_att_values(log_add, atts):
    att_dicts = dict()
    for att in atts:
        att_dicts[att] = []
    with open(log_add, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            for att in atts:
                if str(row[att]) != "nan":
                    att_dicts[att].append(row[att])
    new_att_dicts = dict()
    for att in atts:
        new_att_dicts[att] = list(set(att_dicts[att]))
    return new_att_dicts


def trans_to_prob(labels_, num_label_):
    batch = len(labels_)
    label_probs_ = [[0 for _ in range(num_label_)] for _ in range(batch)]
    for m in range(len(labels_)):
        label_probs_[m][int(labels_[m])] = 1
    return label_probs_


def dataset_split(a_list, train_percent=0.8):
    train_num = math.ceil(len(a_list) * train_percent)
    whole_index = [i for i in range(len(a_list))]
    final_train_index = random.sample(range(0, len(a_list)), train_num)
    valid_index = list(set(whole_index) - set(final_train_index))
    final_train_log_ = [a_list[i] for i in final_train_index]
    valid_log_ = [a_list[i] for i in valid_index]
    return final_train_log_, valid_log_


class EarlyStopping:
    def __init__(self, path="resAttention.pth", patience=10, verbose=False, delta=0, trace_func=print):
        self.patience = patience
        self.verbose = verbose
        self.counter = 0
        self.best_score = None
        self.early_stop = False
        self.val_loss_min = np.inf
        self.delta = delta
        self.path = path
        self.trace_func = trace_func

    def __call__(self, val_loss, model):
        score = -val_loss
        if self.best_score is None:
            self.best_score = score
            self.save_checkpoint(val_loss, model)
        elif score < self.best_score + self.delta:
            self.counter += 1
            self.trace_func(f"EarlyStopping counter: {self.counter} out of {self.patience}")
            if self.counter >= self.patience:
                self.early_stop = True
        else:
            self.best_score = score
            self.save_checkpoint(val_loss, model)
            self.counter = 0

    def save_checkpoint(self, val_loss, model):
        if self.verbose:
            self.trace_func(f"Validation loss decreased ({self.val_loss_min:.9f} --> {val_loss:.9f}). Saving model ...")
        torch.save(model.state_dict(), self.path)
        self.val_loss_min = val_loss


class CsvEventLog:
    def __init__(self, log_add=DATA_ADD, attributes=ATTRIBUTES, encoding_length=ENCODING_LENGTH, min_length=3):
        self.log_df = pd.read_csv(log_add)
        self.log_dict = read_log(log_add)
        self.min_length = min_length
        self.max_length = self.log_df["case"].value_counts().max()
        self.max_prefix_length = self.max_length - 1
        self.discrete_attributes = attributes[1:]
        self.activity_attribute = attributes[1]
        self.remaining_time = attributes[0]
        self.attributes_values, self.attributes_values_nums = dict(), dict()
        for attribute in self.discrete_attributes:
            self.attributes_values[attribute] = sorted(list(set(self.log_df[attribute].values.tolist())))
            self.attributes_values_nums[attribute] = len(self.attributes_values[attribute])
        self.encoding_length = encoding_length

        self.activity_encoding = dict()
        for i in range(len(self.attributes_values[self.activity_attribute])):
            self.activity_encoding[self.attributes_values[self.activity_attribute][i]] = i

        self.attribute_encodings = dict()
        for attribute in self.discrete_attributes:
            self.attribute_encodings[attribute] = self.discrete_embedding(attribute)

    def discrete_embedding(self, attribute_name):
        embedding_result = dict()
        attribute_num = self.attributes_values_nums[attribute_name]
        num_list = torch.IntTensor([i for i in range(attribute_num)])
        embedding = nn.Embedding(attribute_num, self.encoding_length)
        results = embedding(num_list)
        for j in range(attribute_num):
            embedding_result[self.attributes_values[attribute_name][j]] = results[j].tolist()
        return embedding_result

    def time_value_embedding(self, value):
        half_dim = self.encoding_length // 2
        emb_base = math.log(10000.0) / (half_dim - 1) if half_dim > 1 else 1.0
        exp_term = torch.exp(torch.arange(half_dim).float() * -emb_base)
        v = float(value)
        args = v * exp_term
        embedding = torch.zeros(self.encoding_length)
        embedding[0 : 2 * half_dim : 2] = torch.sin(args)
        embedding[1 : 2 * half_dim : 2] = torch.cos(args)
        if self.encoding_length % 2 == 1:
            embedding[-1] = math.sin(v)
        return embedding.tolist()

    def trace_encoding(self, a_trace):
        trace_encoding = []
        for i in range(len(a_trace)):
            event_encoding = []
            for attribute in self.discrete_attributes:
                if a_trace[i][attribute] in self.attributes_values[attribute]:
                    event_encoding.append(self.attribute_encodings[attribute][a_trace[i][attribute]])
                else:
                    event_encoding.append([0 for _ in range(self.encoding_length)])
            time_encoding = self.time_value_embedding(a_trace[i][self.remaining_time])
            event_encoding.append(time_encoding)
            event_encoding = [[math.tanh(x) for x in vector] for vector in event_encoding]
            trace_encoding.append(event_encoding)
        return trace_encoding

    def fit_prefix(self, a_prefix):
        unfitted_prefix = []
        fit_list = [[0 for _ in range(self.encoding_length)] for _ in range(len(a_prefix[0]))]
        if len(a_prefix) < self.max_length - 1:
            for _ in range(self.max_length - len(a_prefix) - 1):
                unfitted_prefix.append(fit_list)
        new_prefix = unfitted_prefix + a_prefix
        return new_prefix

    def dataset_encoding(self, a_log):
        print("-----------log encoding-----------")
        x_att_encodings, y_att_encodings = [], []
        if PREDICTION_MODE == "NAP":
            for trace in tqdm(a_log):
                if len(trace) >= self.min_length:
                    encoding = self.trace_encoding(trace)
                    for i in range(len(trace) - self.min_length + 1):
                        prefix = encoding[: (i + self.min_length - 1)]
                        prefix = self.fit_prefix(prefix)
                        x_att_encodings.append(prefix)
                        label = self.activity_encoding[trace[i + self.min_length - 1][self.activity_attribute]]
                        y_att_encodings.append(label)
        elif PREDICTION_MODE == "PO":
            for trace in tqdm(a_log):
                if len(trace) >= self.min_length:
                    encoding = self.trace_encoding(trace)
                    for i in range(len(trace) - self.min_length + 1):
                        prefix = encoding[: (i + self.min_length - 1)]
                        prefix = self.fit_prefix(prefix)
                        x_att_encodings.append(prefix)
                        label = self.activity_encoding[trace[-1][self.activity_attribute]]
                        y_att_encodings.append(label)
        else:
            for trace in tqdm(a_log):
                if len(trace) >= self.min_length:
                    encoding = self.trace_encoding(trace)
                    for i in range(len(trace) - self.min_length + 1):
                        prefix = encoding[: (i + self.min_length - 1)]
                        prefix = self.fit_prefix(prefix)
                        x_att_encodings.append(prefix)
                        label = trace[i + self.min_length - 2][self.remaining_time]
                        y_att_encodings.append(label)
        return x_att_encodings, y_att_encodings


class ResCell(nn.Module):
    def __init__(self, in_channel, mid_channel, out_channel, stride=1):
        super().__init__()
        self.in_channel = in_channel
        self.mid_channel = mid_channel
        self.out_channel = out_channel
        self.stride = stride
        self.cnn1 = nn.Conv2d(self.in_channel, self.mid_channel, kernel_size=1, stride=1)
        self.bn1 = nn.BatchNorm2d(self.mid_channel)
        self.cnn2 = nn.Conv2d(self.mid_channel, self.mid_channel, kernel_size=3, stride=self.stride, padding=1)
        self.bn2 = nn.BatchNorm2d(self.mid_channel)
        self.cnn3 = nn.Conv2d(self.mid_channel, self.out_channel, kernel_size=1, stride=1)
        self.bn3 = nn.BatchNorm2d(self.out_channel)
        self.cnn4 = nn.Conv2d(self.in_channel, self.out_channel, kernel_size=1, stride=self.stride)
        self.bn4 = nn.BatchNorm2d(self.out_channel)

    def forward(self, x):
        y = F.relu(self.bn1(self.cnn1(x)))
        y = F.relu(self.bn2(self.cnn2(y)))
        y = self.bn3(self.cnn3(y))
        x = self.bn4(self.cnn4(x))
        return F.relu(x + y)


class ResBlock(nn.Module):
    def __init__(self, att_channel, output_dim):
        super().__init__()
        self.att_channel = att_channel
        self.output_dim = output_dim
        self.res_net1 = ResCell(self.att_channel, 64, 64, stride=2)
        self.res_net2 = ResCell(64, 128, 128, stride=2)
        self.res_net3 = ResCell(128, 256, 256, stride=2)
        self.res_net4 = ResCell(256, 512, 512, stride=2)
        self.pooling = nn.AdaptiveAvgPool2d(1)
        self.linear = nn.Linear(512, self.output_dim)

    def forward(self, x):
        y1 = self.res_net1(x)
        y2 = self.res_net2(y1)
        y3 = self.res_net3(y2)
        y4 = self.res_net4(y3)
        out = torch.squeeze(self.pooling(y4), (2, 3))
        return F.relu(self.linear(out))


class SelfAttention(nn.Module):
    def __init__(self, max_prefix_length, hidden_dim, output_dim):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim
        self.max_prefix_length = max_prefix_length
        self.q_fc = nn.Linear(2 * self.hidden_dim, 2 * self.hidden_dim)
        self.k_fc = nn.Linear(2 * self.hidden_dim, 2 * self.hidden_dim)
        self.v_fc = nn.Linear(2 * self.hidden_dim, 2 * self.hidden_dim)
        self.attention = nn.MultiheadAttention(2 * self.hidden_dim, num_heads=2, batch_first=True)
        self.linear = nn.Linear(2 * self.hidden_dim * self.max_prefix_length, self.output_dim)
        self.flatten = nn.Flatten()
        self.ln = nn.LayerNorm(2 * self.hidden_dim * self.max_prefix_length)

    def forward(self, x):
        q = self.q_fc(x)
        k = self.k_fc(x)
        v = self.v_fc(x)
        output, _ = self.attention(q, k, v)
        output = self.flatten(output + x)
        out = self.ln(output)
        return F.relu(self.linear(out))


class ResAttSelf(nn.Module):
    def __init__(self, encoding_length, activity_num, max_prefix_length, att_channel, batch_size, hidden_dim, dropout_rate):
        super().__init__()
        self.encoding_length = encoding_length
        self.activity_num = activity_num
        self.att_channel = att_channel
        self.max_prefix_length = max_prefix_length
        self.num_layers = 2
        self.hidden_dim = hidden_dim
        self.batch_size = batch_size
        self.dropout_rate = dropout_rate
        self.prediction_mode = PREDICTION_MODE

        self.attention = SelfAttention(self.max_prefix_length, self.hidden_dim, self.hidden_dim)
        self.lstm = nn.LSTM(
            input_size=self.att_channel * self.encoding_length,
            hidden_size=self.hidden_dim,
            num_layers=self.num_layers,
            batch_first=True,
            bidirectional=True,
        )
        self.res_block = ResBlock(self.att_channel, self.hidden_dim)
        if PREDICTION_MODE == "T":
            self.linear = nn.Linear(2 * self.hidden_dim, 1)
        else:
            self.linear = nn.Linear(2 * self.hidden_dim, self.activity_num)
        self.dropout = nn.Dropout(self.dropout_rate)

    def forward(self, x):
        x1 = torch.flatten(x, 2, 3)
        weight1 = next(self.parameters()).data
        hidden1 = (
            weight1.new(2 * self.num_layers, self.batch_size, self.hidden_dim).zero_().float().cuda(),
            weight1.new(2 * self.num_layers, self.batch_size, self.hidden_dim).zero_().float().cuda(),
        )
        out_lstm, _ = self.lstm(x1, hidden1)
        out_sfem = self.attention(out_lstm)
        out_ffem = self.res_block(x.permute(0, 2, 1, 3))
        out = torch.concat([out_sfem, out_ffem], dim=1)
        out = self.dropout(out)
        if self.prediction_mode == "T":
            return torch.sigmoid(self.linear(out))
        return self.linear(out)


def data_pro():
    log = CsvEventLog(log_add=DATA_ADD)
    input_channel = len(ATTRIBUTES)
    label_num = len(log.activity_encoding)
    max_prefix_length = log.max_prefix_length
    encoding_length = log.encoding_length
    train_log, test_log = dataset_split(log.log_dict, train_percent=0.8)
    x_train_set, y_train_set = log.dataset_encoding(train_log)
    x_test_set, y_test_set = log.dataset_encoding(test_log)
    data_dir = str(_resolve_path(PRO_DATA_DIR)) + "/"
    mkdir(data_dir)
    np.save(f"{data_dir}{DATASET}_{PREDICTION_MODE}_train_data_x.npy", np.array(x_train_set))
    np.save(f"{data_dir}{DATASET}_{PREDICTION_MODE}_test_data_x.npy", np.array(x_test_set))
    np.save(f"{data_dir}{DATASET}_{PREDICTION_MODE}_train_data_y.npy", np.array(y_train_set))
    np.save(f"{data_dir}{DATASET}_{PREDICTION_MODE}_test_data_y.npy", np.array(y_test_set))
    parameter_add = f"{data_dir}{DATASET}_{PREDICTION_MODE}_parameters.csv"
    pd.DataFrame(
        {
            "input_channel": input_channel,
            "label_num": label_num,
            "max_prefix_length": max_prefix_length,
            "encoding_length": encoding_length,
        },
        index=[0],
    ).to_csv(parameter_add, index=False)


def objective(trial):
    import optuna

    data_dir = str(_resolve_path(PRO_DATA_DIR))
    parameters = get_parameters(str(Path(data_dir) / f"{DATASET}_{PREDICTION_MODE}_parameters.csv"))
    batch_size = trial.suggest_int("batch_size", 32, 128, step=32)
    learning_rate = trial.suggest_float("learning_rate", 0.00001, 0.0001, log=False)
    dropout_rate = trial.suggest_float("drop_rate", 0.1, 0.9, log=False)
    hidden_dim = trial.suggest_int("hidden_dim", 128, 512, step=128)
    net = ResAttSelf(
        parameters["encoding_length"],
        parameters["label_num"],
        parameters["max_prefix_length"],
        parameters["input_channel"],
        batch_size,
        hidden_dim,
        dropout_rate,
    )
    criterion_nap = nn.CrossEntropyLoss()
    criterion_t = nn.MSELoss()
    optimizer = torch.optim.Adam(net.parameters(), lr=learning_rate)

    x_train_data = torch.tensor(np.load(str(Path(data_dir) / f"{DATASET}_{PREDICTION_MODE}_train_data_x.npy")), dtype=torch.float)
    if PREDICTION_MODE == "T":
        y_train_data = torch.tensor(np.load(str(Path(data_dir) / f"{DATASET}_{PREDICTION_MODE}_train_data_y.npy")).astype(float), dtype=torch.float)
    else:
        y_train_data = torch.tensor(np.load(str(Path(data_dir) / f"{DATASET}_{PREDICTION_MODE}_train_data_y.npy")), dtype=torch.float)
    train_loader = DataLoader(TensorDataset(x_train_data, y_train_data), shuffle=True, batch_size=batch_size, drop_last=True)

    x_test_data = torch.tensor(np.load(str(Path(data_dir) / f"{DATASET}_{PREDICTION_MODE}_test_data_x.npy")), dtype=torch.float)
    if PREDICTION_MODE == "T":
        y_test_data = torch.tensor(np.load(str(Path(data_dir) / f"{DATASET}_{PREDICTION_MODE}_test_data_y.npy")).astype(float), dtype=torch.float)
    else:
        y_test_data = torch.tensor(np.load(str(Path(data_dir) / f"{DATASET}_{PREDICTION_MODE}_test_data_y.npy")), dtype=torch.float)
    test_loader = DataLoader(TensorDataset(x_test_data, y_test_data), shuffle=True, batch_size=batch_size, drop_last=True)

    avg_test_losses = []
    model_dir = str(_resolve_path(MODEL_DIR)) + "/"
    mkdir(model_dir)
    model_path = f"{model_dir}{DATASET}_{PREDICTION_MODE}.pth"
    net.cuda()
    early_stopping = EarlyStopping(patience=10, verbose=True, path=model_path)
    train_losses, test_losses = [], []
    for epoch in range(EPOCH):
        net.train()
        labels_train, predict_train = [], []
        for inputs, labels in train_loader:
            inputs, labels = inputs.cuda(), labels.cuda()
            optimizer.zero_grad()
            output = net(inputs)
            train_loss = criterion_nap(output, labels.long())
            train_loss.backward()
            optimizer.step()
            train_losses.append(train_loss.item())
            if PREDICTION_MODE == "T":
                labels_train += labels.tolist()
                predict_train += output.tolist()
            else:
                predict_ = torch.argmax(torch.nn.Softmax(dim=1)(output), 1)
                labels_train += labels.tolist()
                predict_train += predict_.tolist()
        if trial.should_prune():
            raise optuna.exceptions.TrialPruned()

        net.eval()
        labels_test, predict_test = [], []
        with torch.no_grad():
            for inputs_, labels_ in test_loader:
                inputs_, labels_ = inputs_.cuda(), labels_.cuda()
                test_output = net(inputs_)
                if PREDICTION_MODE == "T":
                    test_loss = criterion_t(test_output.squeeze(), labels_)
                    predict_output = torch.sigmoid(test_output)
                    labels_test += labels_.tolist()
                    predict_test += predict_output.tolist()
                else:
                    test_loss = criterion_nap(test_output.squeeze(), labels_.long())
                    predict_output = torch.nn.Softmax(dim=1)(test_output)
                    predict_ = torch.argmax(predict_output, 1)
                    labels_test += labels_.tolist()
                    predict_test += predict_.tolist()
                test_losses.append(test_loss.item())
        avg_train_loss = np.average(train_losses)
        avg_test_loss = np.average(test_losses)
        avg_test_losses.append(avg_test_loss)
        if PREDICTION_MODE == "T":
            print(
                f"| Epoch: {epoch + 1:2d}/{EPOCH:2d} | Train Loss: {avg_train_loss:.4f} | Test Loss: {avg_test_loss:.4f} | "
                f"Train Mse: {metrics.mean_squared_error(labels_train, predict_train):.4f} | "
                f"Test Mse: {metrics.mean_squared_error(labels_test, predict_test):.4f} |"
            )
        else:
            print(
                f"| Epoch: {epoch + 1:2d}/{EPOCH:2d} | Train Loss: {avg_train_loss:.4f} | Test Loss: {avg_test_loss:.4f} | "
                f"Train Acc: {metrics.accuracy_score(labels_train, predict_train):.4f} | "
                f"Test Acc: {metrics.accuracy_score(labels_test, predict_test):.4f} |"
            )
        train_losses, test_losses = [], []
        trial.report(avg_test_loss, epoch)
        early_stopping(avg_test_loss, net)
        if early_stopping.early_stop:
            break
    return sum(avg_test_losses) / len(avg_test_losses)


def main():
    try:
        import optuna
    except ImportError as e:
        raise RuntimeError("Training requires optuna. Install project training dependencies before auto-training models.") from e

    study = optuna.create_study(direction="minimize")
    study.optimize(objective, n_trials=TRIALS, show_progress_bar=True)
    trial = study.best_trial
    best = {key: value for key, value in trial.params.items()}
    data_dir = _resolve_path(PRO_DATA_DIR)
    mkdir(str(data_dir))
    pd.DataFrame(best, index=[0]).to_csv(data_dir / f"best_hyperparameters_{DATASET}_{PREDICTION_MODE}.csv", index=False)


def _load_parameters_or_infer(pro_data_path: Path, dataset: str, mode: str, log: CsvEventLog, state: dict):
    parameter_file = pro_data_path / f"{dataset}_{mode}_parameters.csv"
    if parameter_file.exists():
        return get_parameters(str(parameter_file))
    return {
        "input_channel": len(ATTRIBUTES),
        "label_num": len(log.activity_encoding),
        "max_prefix_length": log.max_prefix_length,
        "encoding_length": log.encoding_length,
    }


def _load_hyperparameters_or_infer(pro_data_path: Path, dataset: str, mode: str, state: dict):
    hyperparameter_file = pro_data_path / f"best_hyperparameters_{dataset}_{mode}.csv"
    if hyperparameter_file.exists():
        return get_parameters(str(hyperparameter_file))
    linear_weight = state.get("linear.weight")
    if linear_weight is None:
        raise FileNotFoundError(f"Missing hyperparameters and cannot infer hidden_dim from model state for {dataset}_{mode}.")
    return {
        "hidden_dim": int(linear_weight.shape[1] // 2),
        "drop_rate": 0.0,
    }


def _torch_load_state(path: Path):
    try:
        return torch.load(str(path), weights_only=True)
    except TypeError:
        return torch.load(str(path))


def _predict_classification(mode: str, dataset: str, pro_data_path: Path, model_path: Path, log: CsvEventLog, trace_input):
    global PREDICTION_MODE
    PREDICTION_MODE = mode
    state = _torch_load_state(model_path / f"{dataset}_{mode}.pth")
    p = _load_parameters_or_infer(pro_data_path, dataset, mode, log, state)
    h = _load_hyperparameters_or_infer(pro_data_path, dataset, mode, state)
    model = ResAttSelf(p["encoding_length"], p["label_num"], p["max_prefix_length"], len(ATTRIBUTES), 1, h["hidden_dim"], h["drop_rate"])
    model.load_state_dict(state)
    model.eval().cuda()
    with torch.no_grad():
        out = torch.nn.Softmax(dim=1)(model(trace_input))
        pred = torch.argmax(out, 1)
        probs = out.tolist()
        return get_key_by_value(log.activity_encoding, pred.item()), max(probs[0])


def predict(trace_add, prediction_mode_, *, dataset_name=None, model_dir=None, base_dir=None, pro_data_dir=None, dataset_csv=None):
    global PREDICTION_MODE
    dataset = dataset_name or DATASET
    base_path = Path(base_dir).resolve() if base_dir is not None else PROJECT_ROOT
    model_path = _resolve_path(model_dir or MODEL_DIR, base_path)

    pro_data_path = _resolve_path(pro_data_dir or PRO_DATA_DIR, base_path)
    trace = read_log(trace_add)
    dataset_csv_path = _resolve_path(dataset_csv or Path("dataset") / "new_data" / f"{dataset}.csv", base_path)
    if not dataset_csv_path.exists():
        raise FileNotFoundError(f"Dataset CSV not found: {dataset_csv_path}")
    log = CsvEventLog(log_add=str(dataset_csv_path))
    trace_encoding_ = log.trace_encoding(trace[0])
    final_encoding = log.fit_prefix(trace_encoding_)
    trace_input = torch.tensor(final_encoding, dtype=torch.float32).unsqueeze(dim=0).cuda()
    if prediction_mode_ == "NAP":
        return _predict_classification("NAP", dataset, pro_data_path, model_path, log, trace_input)
    if prediction_mode_ == "PO":
        return _predict_classification("PO", dataset, pro_data_path, model_path, log, trace_input)
    PREDICTION_MODE = "T"
    state = _torch_load_state(model_path / f"{dataset}_T.pth")
    p = _load_parameters_or_infer(pro_data_path, dataset, "T", log, state)
    h = _load_hyperparameters_or_infer(pro_data_path, dataset, "T", state)
    model = ResAttSelf(p["encoding_length"], p["label_num"], p["max_prefix_length"], len(ATTRIBUTES), 1, h["hidden_dim"], h["drop_rate"])
    model.load_state_dict(state)
    model.eval().cuda()
    avg_times_file = (base_path / "dataset" / "new_data" / "avg_times.csv").resolve()
    avg_times = csv_to_dict(str(avg_times_file)) if avg_times_file.exists() else {}
    with torch.no_grad():
        t_out = model(trace_input)
        if dataset in avg_times:
            return (avg_times[dataset] * t_out.item()) / 86400
        return t_out.item()

