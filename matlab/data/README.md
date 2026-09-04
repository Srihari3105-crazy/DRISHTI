# DRISHTI-LENS — MATLAB Dataset Directory

This directory hosts the validation datasets used by the MATLAB validation scripts.

Expected structure for APTOS 2019 validation:
```
matlab/data/
└── aptos2019/
    ├── train.csv
    └── train_images/
        ├── 000c1434d8d7.png
        └── ...
```

To symlink or copy from `backend/validation/data/aptos2019`:
```powershell
New-Item -ItemType SymbolicLink -Path "matlab\data\aptos2019" -Target "backend\validation\data\aptos2019"
```
