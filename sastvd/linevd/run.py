import pytorch_lightning as pl
from pytorch_lightning.callbacks import ModelCheckpoint
import sastvd.linevd as lvd
import pandas as pd
from ray.tune.integration.pytorch_lightning import (
    TuneReportCheckpointCallback,
)
import sastvd as svd
from ray import tune

def train_linevd(
    config, savepath, samplesz=-1, max_epochs=130
):
    """Wrap Pytorch Lightning to pass to RayTune."""
    model = lvd.LitGNN(
        hfeat=config["hfeat"],
        embtype=config["embtype"],
        methodlevel=False,
        nsampling=True,
        model=config["modeltype"],
        loss=config["loss"],
        hdropout=config["hdropout"],
        gatdropout=config["gatdropout"],
        num_heads=4,
        multitask=config["multitask"],
        stmtweight=config["stmtweight"],
        gnntype=config["gnntype"],
        scea=config["scea"],
        lr=config["lr"],
    )

    # Load data
    data = lvd.BigVulDatasetLineVDDataModule(
        batch_size=config["batch_size"],
        sample=samplesz,
        methodlevel=False,
        nsampling=True,
        nsampling_hops=2,
        gtype=config["gtype"],
        splits=config["splits"],
    )

    # # Train model
    checkpoint_callback = ModelCheckpoint(monitor="val_loss")
    metrics = ["train_loss", "val_loss", "val_auroc"]
    rtckpt_callback = TuneReportCheckpointCallback(metrics, on="validation_end")
    trainer = pl.Trainer(
        accelerator="auto",
        default_root_dir=savepath,
        num_sanity_val_steps=0,
        callbacks=[checkpoint_callback, rtckpt_callback],
        max_epochs=max_epochs,
    )
    trainer.fit(model, data)
    