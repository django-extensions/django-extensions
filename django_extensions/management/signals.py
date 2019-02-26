# -*- coding: utf-8 -*-

from django.dispatch import Signal

run_minutely_jobs = Signal()
run_quarter_hourly_jobs = Signal()
run_hourly_jobs = Signal()
run_daily_jobs = Signal()
run_weekly_jobs = Signal()
run_monthly_jobs = Signal()
run_yearly_jobs = Signal()

pre_command = Signal(providing_args=["args", "kwargs"])
post_command = Signal(providing_args=["args", "kwargs", "outcome"])
