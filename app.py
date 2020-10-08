#!/usr/bin/env python3

from aws_cdk import core

from acg_etl.acg_etl_stack import AcgEtlStack


app = core.App()
AcgEtlStack(app, "acg-etl")

app.synth()
