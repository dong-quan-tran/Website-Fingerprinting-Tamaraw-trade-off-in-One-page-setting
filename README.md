***

# Website Fingerprinting: Tamaraw Trade-off in the One-Page Setting

This repository is a standalone research codebase built on top of Xiao Deng’s Website-Fingerprinting-Library (WFlib). It evaluates how the Tamaraw defense trades off bandwidth overhead and website-fingerprinting accuracy in the **one-page** closed-world setting, using four deep-learning attacks: **DF, TikTok, Var-CNN, and RF**.

The code is intended for research purposes only.

## Contents

- Modified WFlib core for our experiments
- Scripts to generate Tamaraw-defended datasets from CW traces
- Scripts to build one-page datasets at different pad lengths
- Training and evaluation scripts for DF, TikTok, Var-CNN, and RF on Tamaraw
- Utilities to peek and summarize one-page results

***

## Environment setup

We recommend a dedicated conda/venv environment (Python 3.8, PyTorch with CUDA).

```bash
# From WSL
cd ~/Website-Fingerprinting-Library

# (optional) create env
conda create -n wf38 python=3.8
conda activate wf38

# install this project in editable mode
pip install --user -e .
pip install -r requirements.txt
```

***

## Base datasets

This project assumes the original CW dataset from WFlib.

1. Create a datasets folder:

```bash
mkdir -p datasets
```

2. Download WFlib datasets (including `CW.npz`) from:

   https://zenodo.org/records/13732130

3. Place the files under:

```text
./datasets/CW.npz
```

4. Split CW into train/valid/test (if not already split):

```bash
python exp/dataset_process/dataset_split.py --dataset CW
```

This produces `CW_train.npz`, `CW_valid.npz`, and `CW_test.npz` under `datasets/` using WFlib’s standard split logic.

***

## Generating Tamaraw-defended CW traces

We generate **Tamaraw-protected** traces for the CW dataset, for a chosen pad length `PadL` and parameters matching Tamaraw’s design.

The main entry point is:

```bash
python run_Tamaraw_CW.py \
  --input_dataset CW \
  --output_prefix CW_tamaraw \
  --pad_length PADL \
  [other Tamaraw parameters...]
```

Typical usage:

```bash
# Example: generate Tamaraw-defended CW dataset with a given PadL
python run_Tamaraw_CW.py \
  --input_dataset CW \
  --output_prefix CW_tamaraw \
  --pad_length 2000
```

This script:

- reads the original CW split (`CW_train`, `CW_valid`, `CW_test`),
- applies Tamaraw padding with the chosen pad length,
- writes Tamaraw-defended splits under names like:
  - `CW_tamaraw_train.npz`
  - `CW_tamaraw_valid.npz`
  - `CW_tamaraw_test.npz`

Check `run_Tamaraw_CW.py` for the exact CLI arguments (pad length, packet rate, burst sizes, etc.).

***

## Building one-page datasets

For each Tamaraw-defended CW dataset, we construct **one-page** datasets following Wang’s one-page setting.

To build the one-page dataset for a given `CW_tamaraw` and sequence length 5000:

```bash
# inside repo root
dataset=CW_tamaraw

for split in train valid test
do
  python -u exp/dataset_process/gen_tam.py \
    --dataset ${dataset} \
    --seq_len 5000 \
    --in_file ${split}
done
```

This produces processed files such as:

- `datasets/CW_tamaraw_tam_train.npz`
- `datasets/CW_tamaraw_tam_valid.npz`
- `datasets/CW_tamaraw_tam_test.npz`

These are used for the RF (TAM feature) experiments; DF/TikTok/Var-CNN experiments use direction/timing features directly from `CW_tamaraw`.

If you want to automate multiple pad lengths and one-page configurations, see:

```bash
./run_onepage_experiments.sh
```

This script loops over PadL values, generates Tamaraw datasets, then runs all attacks in the one-page setting.

***

## Running the attacks

We evaluate **DF, TikTok, Var-CNN, and RF** on Tamaraw-defended CW in the one-page setting. Below are the core commands (for a single PadL and the dataset name `CW_tamaraw`).

### DF (Deep Fingerprinting)

```bash
dataset=CW_tamaraw

python -u exp/train.py \
  --dataset ${dataset} \
  --model DF \
  --device cuda:0 \
  --feature DIR \
  --seq_len 5000 \
  --train_epochs 30 \
  --batch_size 128 \
  --learning_rate 2e-3 \
  --optimizer Adamax \
  --eval_metrics Accuracy Precision Recall F1-score \
  --save_metric F1-score \
  --save_name max_f1

python -u exp/test.py \
  --dataset ${dataset} \
  --model DF \
  --device cuda:0 \
  --feature DIR \
  --seq_len 5000 \
  --batch_size 256 \
  --eval_metrics Accuracy Precision Recall F1-score \
  --load_name max_f1
```

### TikTok

```bash
dataset=CW_tamaraw

python -u exp/train.py \
  --dataset ${dataset} \
  --model TikTok \
  --device cuda:0 \
  --feature DT \
  --seq_len 5000 \
  --train_epochs 30 \
  --batch_size 128 \
  --learning_rate 2e-3 \
  --optimizer Adamax \
  --eval_metrics Accuracy Precision Recall F1-score \
  --save_metric F1-score \
  --save_name max_f1

python -u exp/test.py \
  --dataset ${dataset} \
  --model TikTok \
  --device cuda:0 \
  --feature DT \
  --seq_len 5000 \
  --batch_size 256 \
  --eval_metrics Accuracy Precision Recall F1-score \
  --load_name max_f1
```

### RF (Robust Fingerprinting) on Tamaraw one-page features

Assuming you have already run `gen_tam.py` (see “Building one-page datasets”):

```bash
dataset=CW_tamaraw

python -u exp/train.py \
  --dataset ${dataset} \
  --model RF \
  --device cuda:0 \
  --train_file tam_train \
  --valid_file tam_valid \
  --feature TAM \
  --seq_len 1800 \
  --train_epochs 30 \
  --batch_size 200 \
  --learning_rate 5e-4 \
  --optimizer Adam \
  --eval_metrics Accuracy Precision Recall F1-score \
  --save_metric F1-score \
  --save_name max_f1

python -u exp/test.py \
  --dataset ${dataset} \
  --model RF \
  --device cuda:0 \
  --test_file tam_test \
  --feature TAM \
  --seq_len 1800 \
  --batch_size 256 \
  --eval_metrics Accuracy Precision Recall F1-score \
  --load_name max_f1
```

### Var-CNN

```bash
dataset=CW_tamaraw

python -u exp/train.py \
  --dataset ${dataset} \
  --model VarCNN \
  --device cuda:0 \
  --feature DT2 \
  --seq_len 5000 \
  --train_epochs 30 \
  --batch_size 50 \
  --learning_rate 1e-3 \
  --optimizer Adam \
  --eval_metrics Accuracy Precision Recall F1-score \
  --save_metric F1-score \
  --save_name max_f1

python -u exp/test.py \
  --dataset ${dataset} \
  --model VarCNN \
  --device cuda:0 \
  --feature DT2 \
  --seq_len 5000 \
  --batch_size 256 \
  --eval_metrics Accuracy Precision Recall F1-score \
  --load_name max_f1
```

All metrics and logs are saved under `./exp/logs/` and corresponding result folders, following the original WFlib conventions.

***

## Inspecting and summarizing results

We provide helper code to inspect and summarize results across pad lengths and attacks:

- `peek_onepage_results.py`: parses experiment logs and prints/exports accuracy, precision, recall, F1-score vs pad length.

Typical usage:

```bash
python peek_onepage_results.py \
  --results_dir exp/logs/ \
  --output_csv results/onepage_summary.csv
```

Adjust `--results_dir` to where your training scripts write logs.

***

## Reference / Attribution

This project is **based on**:

- X. Deng, Q. Li, and K. Xu, “Robust and Reliable Early-Stage Website Fingerprinting Attacks via Spatial-Temporal Distribution Analysis,” CCS 2024 (WFlib).

If you use this repository in academic work, please cite both Deng et al.’s WFlib paper and our Tamaraw trade-off work (add your BibTeX once finalized).

***

## Contact

For questions about this Tamaraw one-page trade-off code:

- Dong Quan Tran (Johnny) - dxt9721@mavs.uta.edu / dongquan.tran.johnny@gmail.com

For questions about the original WFlib:

- Xinhao Deng – dengxh23@mails.tsinghua.edu.cn  

***
