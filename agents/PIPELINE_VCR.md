# PIPELINE – Classificador CNN Multi-Escala de Cor Veicular (VCR)

Este documento descreve **a arquitetura lógica e o pipeline de treinamento, inferência e avaliação**
do projeto **Classificador CNN Multi-Escala com Modulação Long-Tail**, em uma forma **operacional,
iterativa e codificável por IA**.

---

## Visão Geral do Pipeline

environment usando o uv

Pipeline composto por **6 scripts independentes**, conectados por **artefatos explícitos**.

01_detect_crop.py  
02_preprocess.py  
03_model.py  
04_train_mlflow.py  
05_infer.py  
06_eval.py  

O **manifest** é o contrato central.

---

## Estrutura de Diretórios

vcr/
  data/
    raw/
    crops/
    processed/
    manifests/
      manifest_raw.jsonl
      manifest_ready.jsonl
  runs/
  src/
    utils/
  01_detect_crop.py
  02_preprocess.py
  03_model.py
  04_train_mlflow.py
  05_infer.py
  06_eval.py

---

## Manifest (JSONL)

Uma linha por amostra.

Campos mínimos:

{
  "id": "cam01_000123",
  "image_path": "data/raw/cam01/frame_000123.jpg",
  "bbox_xyxy": [120, 80, 640, 420],
  "label": "silver",
  "split": "train"
}

Campos opcionais:
- crop_path
- meta (camera_id, time_of_day, etc.)

---

## 1. 01_detect_crop.py
Responsável por detectar veículos ou ler bbox existentes e gerar o manifest bruto.

Entrada:
- data/raw/

Saída:
- data/manifests/manifest_raw.jsonl
- data/crops/ (opcional)

---

## 2. 02_preprocess.py
Valida e prepara o dataset.

Saída:
- manifest_ready.jsonl
- class_to_idx.json

---

## 3. 03_model.py
Define a arquitetura:
- Backbone CNN
- Fusão multi-escala (MSFF)
- Cabeça de classificação

Não executa treino.

---

## 4. 04_train_mlflow.py
Treinamento com registro em MLflow.

Saída:
- runs/<run_id>/best.pt
- runs/<run_id>/last.pt

Métricas:
- top1, top3
- macro-F1
- balanced accuracy
- many / medium / few-shot accuracy

---

## 5. 05_infer.py
Executa inferência com modelo treinado.

Saída:
- preds.jsonl

---

## 6. 06_eval.py
Avaliação final.

Saída:
- report.json
- report.md
- confusion matrix (opcional)

---

## Princípios
- Scripts independentes
- Comunicação apenas via arquivos
- Manifest como fonte da verdade
- Inferência desacoplada da avaliação

---

## Próximos Passos
1. Implementar Dataset PyTorch baseado no manifest
2. Implementar MSFF
3. Implementar Smooth Modulation Loss
4. Automatizar geração de report.md
