# AUTOGENERATED! DO NOT EDIT! File to edit: nbks/03_train.ipynb (unless otherwise specified).

__all__ = ['train', 'train_cv']

# Cell
from .dataset import *
from .evaluate import *

from fastai.vision.all import *
from fastcore.script import *
from fastai.callback.wandb import *
import wandb

# Cell
def train(epochs: int, lr: float, frz: int=1, pre: int=800, re: int=256,
          bs: int=256, fold: int=0, smooth: bool=True,
          arch: str='resnet18', dump: bool=False, log: bool=False):
    # Prep Data, Opt, Loss, Arch
    if log: wandb.init(project="plant-pathology")
    dls = get_dls_all_in_1(presize=pre, resize=re, bs=bs, val_fold=fold)
    if smooth: loss_func = LabelSmoothingCrossEntropyFlat()
    else:      loss_func = CrossEntropyLossFlat()
    m = globals()[arch]

    # Build Learner
    cbs = [WandbCallback(), SaveModelCallback()] if log else []
    learn = Learner(dls, create_cnn_model(m, dls.c), loss_func=loss_func,
                    metrics=[accuracy, RocAuc()], cbs=cbs)
    if dump: print(learn.model); exit()
    # Add more callbacks

    print(f"Training for {frz} epochs frozen, {epochs} unfrozen")
    learn.freeze()
    learn.fit_one_cycle(frz, lr)
    learn.unfreeze()
    learn.fit_one_cycle(epochs, slice(lr/100, lr/2))  # Explore other divs
    return learn

# Cell
@call_parse
def train_cv(
    epochs: Param("Number of unfrozen epochs", int),
    lr:     Param("Initial learning rate", float),
    frz:    Param("Number of frozen epochs", int)=1,
    pre:    Param("Presize", int)=800,
    re:     Param("Resize", int)=256,
    bs:     Param("Batch size", int)=256,
    smooth: Param("Label smoothing?", bool_arg)=False,
    arch:   Param("Architecture", str)='resnet18',
    dump:   Param("Print model", bool_arg)=False,
    log:    Param("Log w/ W&B", bool_arg)=False,
):
    scores = []
    for fold in range(5):
        learn = train(epochs, lr, frz=frz, pre=pre, re=re, bs=bs, smooth=smooth, arch=arch, dump=dump, log=log, fold=fold)
        scores.append(learn.final_record)

        # Create submission file for this model
        evaluate(learn, f"predictions_fold_{fold}.csv")
    scores = np.array(scores)
    print(f"Scores: {scores}")
    print(f"Mean: {scores.mean(0)}")